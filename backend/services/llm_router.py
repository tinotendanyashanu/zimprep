from __future__ import annotations

import base64
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Any

import httpx
from google import genai
from google.genai import types
from openai import OpenAI

logger = logging.getLogger(__name__)

_SUPPORTED_MODEL_TYPES = {"extraction", "verification", "mcq"}
_MAX_ATTEMPTS_PER_PROVIDER = 2


@dataclass(frozen=True)
class _ProviderSpec:
    name: str
    provider: str
    model: str
    timeout_seconds: int


@dataclass
class _GeminiCandidateAdapter:
    finish_reason: str | None = None


class _GeminiLikeResponse:
    def __init__(self, text: str, finish_reason: str | None = None):
        self.text = text
        self.candidates = []
        if finish_reason:
            self.candidates = [_GeminiCandidateAdapter(finish_reason=finish_reason)]


_PROVIDER_CHAIN = {
    "extraction": (
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 20),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 15),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 20),
    ),
    "verification": (
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 20),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 15),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 20),
    ),
    "mcq": (
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 20),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 15),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 20),
    ),
}


class _ProviderFallback(Exception):
    """Signal that the next provider in the chain should be tried."""


def call_llm(model_type: str, contents: list, system_instruction: str, config: dict):
    """
    Route an LLM call through the configured provider chain.

    Rules:
      - 503 / unavailable / overloaded: no retry, immediate fallback
      - 429 / rate limit: one retry, then fallback
      - timeout / connection: one retry, then fallback
      - other errors: fail immediately
    """
    if model_type not in _SUPPORTED_MODEL_TYPES:
        raise ValueError(f"Unsupported model_type: {model_type}")

    last_fallback_error: Exception | None = None

    for provider_spec in _PROVIDER_CHAIN[model_type]:
        try:
            response = _call_provider_with_policy(
                provider_spec=provider_spec,
                contents=contents,
                system_instruction=system_instruction,
                config=config or {},
            )
            logger.info(
                "LLM routing success: model_type=%s provider_used=%s model=%s",
                model_type,
                provider_spec.name,
                provider_spec.model,
            )
            return response
        except _ProviderFallback as exc:
            last_fallback_error = exc
            continue

    raise RuntimeError("ALL_LLM_PROVIDERS_FAILED") from last_fallback_error


def _call_provider_with_policy(
    *,
    provider_spec: _ProviderSpec,
    contents: list,
    system_instruction: str,
    config: dict[str, Any],
):
    for attempt in range(1, _MAX_ATTEMPTS_PER_PROVIDER + 1):
        started_at = time.monotonic()
        try:
            if provider_spec.provider == "gemini":
                response = _call_gemini(
                    model=provider_spec.model,
                    contents=contents,
                    system_instruction=system_instruction,
                    config=config,
                    timeout_seconds=provider_spec.timeout_seconds,
                )
            elif provider_spec.provider == "openai":
                response = _call_openai(
                    model=provider_spec.model,
                    contents=contents,
                    system_instruction=system_instruction,
                    config=config,
                    timeout_seconds=provider_spec.timeout_seconds,
                )
            else:
                raise RuntimeError(f"Unsupported provider: {provider_spec.provider}")

            elapsed = time.monotonic() - started_at
            logger.info(
                "%s succeeded on attempt %d in %.2fs",
                provider_spec.name,
                attempt,
                elapsed,
            )
            return response
        except Exception as exc:
            elapsed = time.monotonic() - started_at
            category = _classify_error(exc)
            reason = _describe_error(category, exc)

            if category == "unavailable":
                logger.warning(
                    "%s failed (%s) on attempt %d in %.2fs -> switching provider",
                    provider_spec.name,
                    reason,
                    attempt,
                    elapsed,
                )
                raise _ProviderFallback(exc) from exc

            if category in {"rate_limit", "timeout"} and attempt < _MAX_ATTEMPTS_PER_PROVIDER:
                logger.warning(
                    "%s failed (%s) on attempt %d in %.2fs -> retrying once",
                    provider_spec.name,
                    reason,
                    attempt,
                    elapsed,
                )
                continue

            if category in {"rate_limit", "timeout"}:
                logger.warning(
                    "%s failed (%s) on attempt %d in %.2fs -> switching provider",
                    provider_spec.name,
                    reason,
                    attempt,
                    elapsed,
                )
                raise _ProviderFallback(exc) from exc

            logger.error(
                "%s failed (%s) on attempt %d in %.2fs -> aborting",
                provider_spec.name,
                reason,
                attempt,
                elapsed,
            )
            raise

    raise RuntimeError(f"{provider_spec.name} exhausted attempts unexpectedly")


def _call_gemini(
    *,
    model: str,
    contents: list,
    system_instruction: str,
    config: dict[str, Any],
    timeout_seconds: int,
):
    api_key = os.environ["GOOGLE_AI_API_KEY"]
    client = genai.Client(api_key=api_key)
    generation_config = _build_gemini_config(
        system_instruction=system_instruction,
        config=config,
    )

    return _run_with_timeout(
        lambda: client.models.generate_content(
            model=model,
            contents=contents,
            config=generation_config,
        ),
        timeout_seconds=timeout_seconds,
        provider_name=model,
    )


def _call_openai(
    *,
    model: str,
    contents: list,
    system_instruction: str,
    config: dict[str, Any],
    timeout_seconds: int,
):
    api_key = os.environ["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key, timeout=timeout_seconds)
    messages = _build_openai_messages(
        contents=contents,
        system_instruction=system_instruction,
    )
    create_kwargs = _build_openai_kwargs(config)

    response = _run_with_timeout(
        lambda: client.chat.completions.create(
            model=model,
            messages=messages,
            **create_kwargs,
        ),
        timeout_seconds=timeout_seconds,
        provider_name=model,
    )

    choice = response.choices[0]
    finish_reason = choice.finish_reason
    if finish_reason == "length":
        finish_reason = "MAX_TOKENS"

    text = choice.message.content or ""
    return _GeminiLikeResponse(text=text, finish_reason=finish_reason)


def _build_gemini_config(
    *,
    system_instruction: str,
    config: dict[str, Any],
) -> types.GenerateContentConfig:
    payload = dict(config)
    payload["system_instruction"] = system_instruction

    thinking_budget = payload.pop("thinking_budget", None)
    thinking_config = payload.get("thinking_config")

    if thinking_budget is not None:
        payload["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
    elif isinstance(thinking_config, dict):
        payload["thinking_config"] = types.ThinkingConfig(**thinking_config)

    return types.GenerateContentConfig(**payload)


def _build_openai_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}

    if "max_output_tokens" in config:
        kwargs["max_tokens"] = config["max_output_tokens"]
    if "temperature" in config:
        kwargs["temperature"] = config["temperature"]
    if "top_p" in config:
        kwargs["top_p"] = config["top_p"]

    return kwargs


def _build_openai_messages(*, contents: list, system_instruction: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    if system_instruction:
        messages.append(
            {
                "role": "system",
                "content": system_instruction,
            }
        )

    user_parts: list[dict[str, Any]] = []
    for item in contents:
        text_part = _as_text_part(item)
        if text_part is not None:
            user_parts.append({"type": "text", "text": text_part})
            continue

        image_part = _as_image_part(item)
        if image_part is not None:
            user_parts.append(image_part)
            continue

        user_parts.append({"type": "text", "text": str(item)})

    messages.append({"role": "user", "content": user_parts})
    return messages


def _as_text_part(item: Any) -> str | None:
    if isinstance(item, str):
        return item
    return None


def _as_image_part(item: Any) -> dict[str, Any] | None:
    inline_data = getattr(item, "inline_data", None)
    if inline_data is None:
        return None

    data = getattr(inline_data, "data", None)
    mime_type = getattr(inline_data, "mime_type", None)
    if not data or not mime_type:
        return None

    encoded = base64.b64encode(data).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{encoded}",
        },
    }


def _run_with_timeout(fn, *, timeout_seconds: int, provider_name: str):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"{provider_name} timed out after {timeout_seconds}s") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _classify_error(exc: Exception) -> str:
    if isinstance(exc, (TimeoutError, FuturesTimeoutError, httpx.TimeoutException)):
        return "timeout"

    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError, ConnectionError)):
        return "timeout"

    message = str(exc).lower()

    if any(token in message for token in ("503", "unavailable", "overloaded", "high demand")):
        return "unavailable"

    if any(token in message for token in ("429", "rate limit", "resource exhausted", "quota")):
        return "rate_limit"

    if any(token in message for token in (
        "timeout",
        "timed out",
        "connection reset",
        "connection aborted",
        "connection refused",
        "temporarily unavailable",
        "broken pipe",
    )):
        return "timeout"

    return "other"


def _describe_error(category: str, exc: Exception) -> str:
    if category == "unavailable":
        return "503/unavailable"
    if category == "rate_limit":
        return "429/rate_limit"
    if category == "timeout":
        return "timeout/connection"
    return str(exc)[:200] or exc.__class__.__name__
