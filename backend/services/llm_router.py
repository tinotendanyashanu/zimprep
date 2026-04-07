from __future__ import annotations

import base64
import logging
import os
import threading
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
_MAX_PROVIDER_OUTPUT_TOKENS = 8000
_CIRCUIT_BREAKER_THRESHOLD = 3
_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60
_provider_failures: dict[str, int] = {}
_provider_disabled_until: dict[str, float] = {}
_provider_state_lock = threading.Lock()


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
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 40),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 25),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 40),
    ),
    "verification": (
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 40),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 25),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 40),
    ),
    "mcq": (
        _ProviderSpec("Gemini Pro", "gemini", "gemini-2.5-pro", 40),
        _ProviderSpec("Gemini Flash", "gemini", "gemini-2.5-flash", 25),
        _ProviderSpec("OpenAI GPT-4o", "openai", "gpt-4o", 40),
    ),
}


class _ProviderFallback(Exception):
    """Signal that the next provider in the chain should be tried."""


def normalize_config(provider: str, config: dict[str, Any]) -> dict[str, Any]:
    config = config or {}

    if provider == "openai":
        max_tokens = config.get("max_output_tokens", 4000)
        if not isinstance(max_tokens, int):
            try:
                max_tokens = int(max_tokens)
            except (TypeError, ValueError):
                max_tokens = 4000

        max_tokens = max(1, min(max_tokens, _MAX_PROVIDER_OUTPUT_TOKENS))
        normalized = {
            "max_tokens": max_tokens,
            "temperature": config.get("temperature", 0.2),
        }
        logger.info(
            "OpenAI config normalized: max_tokens=%s temperature=%s",
            normalized["max_tokens"],
            normalized["temperature"],
        )
        return normalized

    if provider == "gemini":
        max_output_tokens = config.get("max_output_tokens", _MAX_PROVIDER_OUTPUT_TOKENS)
        if not isinstance(max_output_tokens, int):
            try:
                max_output_tokens = int(max_output_tokens)
            except (TypeError, ValueError):
                max_output_tokens = _MAX_PROVIDER_OUTPUT_TOKENS

        normalized = {
            "max_output_tokens": max(1, min(max_output_tokens, _MAX_PROVIDER_OUTPUT_TOKENS)),
            "thinking_config": config.get("thinking_config"),
        }
        logger.info(
            "Gemini config normalized: max_output_tokens=%s thinking_config=%s",
            normalized["max_output_tokens"],
            "set" if normalized["thinking_config"] is not None else "none",
        )
        return normalized

    return dict(config)


def call_llm(
    model_type: str,
    contents: list,
    system_instruction: str,
    config: dict,
    task_type: str | None = None,
):
    """
    Route an LLM call through the configured provider chain.

    Rules:
      - 503 / unavailable / overloaded: no retry, immediate fallback
      - 429 / rate limit: one retry, then fallback
      - timeout / connection: immediate fallback
      - other errors: fail immediately
    """
    resolved_task_type = task_type or (config or {}).get("task_type", model_type)
    if resolved_task_type not in _SUPPORTED_MODEL_TYPES:
        raise ValueError(f"Unsupported model_type: {resolved_task_type}")

    last_fallback_error: Exception | None = None
    provider_chain = _get_provider_chain(resolved_task_type, config or {})

    for provider_spec in provider_chain:
        if _is_provider_disabled(provider_spec.name):
            logger.warning("Skipping %s due to circuit breaker", provider_spec.name)
            continue
        try:
            response = _call_provider_with_policy(
                provider_spec=provider_spec,
                contents=contents,
                system_instruction=system_instruction,
                config=config or {},
            )
            logger.info(
                "LLM routing success: model_type=%s provider_used=%s model=%s",
                resolved_task_type,
                provider_spec.name,
                provider_spec.model,
            )
            return response
        except _ProviderFallback as exc:
            last_fallback_error = exc
            continue

    raise RuntimeError("ALL_LLM_PROVIDERS_FAILED") from last_fallback_error


def _get_provider_chain(model_type: str, config: dict[str, Any]) -> tuple[_ProviderSpec, ...]:
    chain = _PROVIDER_CHAIN[model_type]
    gemini_flash = next((spec for spec in chain if spec.model == "gemini-2.5-flash"), None)
    gemini_pro = next((spec for spec in chain if spec.model == "gemini-2.5-pro"), None)
    openai = next((spec for spec in chain if spec.provider == "openai"), None)

    if model_type == "extraction":
        batch_size = config.get("batch_size", config.get("batch_pages"))
        try:
            batch_size = int(batch_size)
        except (TypeError, ValueError):
            batch_size = None

        if batch_size is not None and batch_size <= 3:
            ordered = [gemini_flash, openai]
            logger.info("Using Flash-first extraction chain for small batch: batch_size=%s", batch_size)
        else:
            ordered = [gemini_pro, gemini_flash, openai]
        return tuple(spec for spec in ordered if spec is not None)

    if model_type in {"verification", "mcq"}:
        return tuple(spec for spec in (gemini_flash, openai) if spec is not None)

    return chain


def _is_provider_disabled(provider_name: str) -> bool:
    now = time.monotonic()
    with _provider_state_lock:
        disabled_until = _provider_disabled_until.get(provider_name, 0.0)
        if disabled_until <= now:
            if provider_name in _provider_disabled_until:
                _provider_disabled_until.pop(provider_name, None)
                _provider_failures.pop(provider_name, None)
            return False
        return True


def _record_provider_success(provider_name: str) -> None:
    with _provider_state_lock:
        _provider_failures[provider_name] = 0
        _provider_disabled_until.pop(provider_name, None)


def _record_provider_failure(provider_name: str) -> None:
    now = time.monotonic()
    with _provider_state_lock:
        failures = _provider_failures.get(provider_name, 0) + 1
        _provider_failures[provider_name] = failures
        if failures >= _CIRCUIT_BREAKER_THRESHOLD:
            _provider_disabled_until[provider_name] = now + _CIRCUIT_BREAKER_COOLDOWN_SECONDS
            logger.warning(
                "Circuit breaker opened for %s after %d consecutive failures",
                provider_name,
                failures,
            )


def _call_provider_with_policy(
    *,
    provider_spec: _ProviderSpec,
    contents: list,
    system_instruction: str,
    config: dict[str, Any],
):
    normalized_config = normalize_config(provider_spec.provider, config)

    for attempt in range(1, _MAX_ATTEMPTS_PER_PROVIDER + 1):
        started_at = time.monotonic()
        try:
            if provider_spec.provider == "gemini":
                response = _call_gemini(
                    model=provider_spec.model,
                    contents=contents,
                    system_instruction=system_instruction,
                    config=normalized_config,
                    timeout_seconds=provider_spec.timeout_seconds,
                )
            elif provider_spec.provider == "openai":
                response = _call_openai(
                    model=provider_spec.model,
                    contents=contents,
                    system_instruction=system_instruction,
                    config=normalized_config,
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
            _record_provider_success(provider_spec.name)
            return response
        except Exception as exc:
            elapsed = time.monotonic() - started_at
            category = _classify_error(exc)
            reason = _describe_error(category, exc)
            _record_provider_failure(provider_spec.name)

            if category == "unavailable":
                logger.warning(
                    "%s failed (%s) on attempt %d in %.2fs -> switching provider",
                    provider_spec.name,
                    reason,
                    attempt,
                    elapsed,
                )
                raise _ProviderFallback(exc) from exc

            if category == "rate_limit" and attempt < _MAX_ATTEMPTS_PER_PROVIDER:
                logger.warning(
                    "%s failed (%s) on attempt %d in %.2fs -> retrying once",
                    provider_spec.name,
                    reason,
                    attempt,
                    elapsed,
                )
                continue

            if category in {"rate_limit", "timeout", "unavailable"}:
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
    cfg = normalize_config("openai", config)

    response = _run_with_timeout(
        lambda: client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=cfg["max_tokens"],
            temperature=cfg["temperature"],
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
    cfg = normalize_config("openai", config)
    return {
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
    }


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
