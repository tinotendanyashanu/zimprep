from __future__ import annotations

import re
from typing import Any

_MATH_SEGMENT_RE = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)
_LATEX_INLINE_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_LATEX_BLOCK_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
_RAW_LATEX_RE = re.compile(
    r"(\\[A-Za-z]+(?:\{[^{}]+\}|[A-Za-z0-9^_()+\-=/:])*(?:\s*\\[A-Za-z]+(?:\{[^{}]+\}|[A-Za-z0-9^_()+\-=/:])*)*)"
)
_SCIENTIFIC_NOTATION_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:x|×)\s*10\^\{?(-?\d+)\}?\b"
)
_POWER_EXPRESSION_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9/]*(?:\s+[A-Za-z][A-Za-z0-9/]*)*)\^(-?\d+)\b"
)
_SUBSCRIPT_EXPRESSION_RE = re.compile(r"\b([A-Za-z]+)_([A-Za-z0-9]+)\b")
_CHEMISTRY_RE = re.compile(r"\b(?:[A-Z][a-z]?\d*){2,}\b")
_UNICODE_SQUARED_CUBED_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9/]*)([²³])\b")

_TEXT_KEYS = {"text", "examiner_note"}
_TEXT_LIST_KEYS = {"correct_points", "missing_points", "ai_references"}

_SUPERSCRIPT_MAP = {"²": "2", "³": "3"}


def _normalise_math_body(body: str) -> str:
    body = body.replace("×", r"\times ")
    body = re.sub(
        r"([_^])(?!\{)(-?[A-Za-z0-9]+)",
        lambda match: f"{match.group(1)}{{{match.group(2)}}}",
        body,
    )
    body = re.sub(r"\s+", " ", body).strip()
    return body


def _wrap_inline_math(expr: str) -> str:
    return f"${_normalise_math_body(expr)}$"


def _wrap_block_math(expr: str) -> str:
    return f"$${_normalise_math_body(expr)}$$"


def _normalise_chemistry_formula(match: re.Match[str]) -> str:
    formula = match.group(0)
    return re.sub(r"(\d+)", lambda part: f"$_{part.group(1)}$", formula)


def _normalise_plain_text(text: str) -> str:
    text = _RAW_LATEX_RE.sub(lambda match: _wrap_inline_math(match.group(1)), text)
    text = _SCIENTIFIC_NOTATION_RE.sub(
        lambda match: _wrap_inline_math(
            f"{match.group(1)} \\times 10^{{{match.group(2)}}}"
        ),
        text,
    )
    text = _UNICODE_SQUARED_CUBED_RE.sub(
        lambda match: _wrap_inline_math(
            f"{match.group(1)}^{{{_SUPERSCRIPT_MAP[match.group(2)]}}}"
        ),
        text,
    )
    text = _POWER_EXPRESSION_RE.sub(
        lambda match: _wrap_inline_math(f"{match.group(1)}^{{{match.group(2)}}}"),
        text,
    )
    text = _SUBSCRIPT_EXPRESSION_RE.sub(
        lambda match: _wrap_inline_math(f"{match.group(1)}_{{{match.group(2)}}}"),
        text,
    )
    text = _CHEMISTRY_RE.sub(_normalise_chemistry_formula, text)
    return text


def normalize_scientific_content(text: str) -> str:
    """
    Convert mixed plain-text scientific notation into a render-safe hybrid format.

    The output keeps normal prose intact while wrapping math-like fragments in
    inline/block dollar delimiters that the frontend renderer can parse.
    """
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _LATEX_BLOCK_RE.sub(
        lambda match: _wrap_block_math(match.group(1)),
        normalized,
    )
    normalized = _LATEX_INLINE_RE.sub(
        lambda match: _wrap_inline_math(match.group(1)),
        normalized,
    )

    parts: list[str] = []
    for chunk in _MATH_SEGMENT_RE.split(normalized):
        if not chunk:
            continue
        if chunk.startswith("$$") and chunk.endswith("$$"):
            parts.append(_wrap_block_math(chunk[2:-2]))
            continue
        if chunk.startswith("$") and chunk.endswith("$"):
            parts.append(_wrap_inline_math(chunk[1:-1]))
            continue
        parts.append(_normalise_plain_text(chunk))

    normalized = "".join(parts)
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def validate_renderable_content(text: str) -> str:
    """
    Backend safety gate for any question-like text headed to storage or the UI.
    """
    return normalize_scientific_content(text)


def normalize_render_payload(payload: Any) -> Any:
    """
    Recursively normalise renderable strings in API payloads so legacy rows do
    not leak raw scientific notation to the frontend.
    """
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            if key in _TEXT_KEYS and isinstance(value, str):
                normalized[key] = normalize_scientific_content(value)
            elif key in _TEXT_LIST_KEYS and isinstance(value, list):
                normalized[key] = [
                    normalize_scientific_content(item) if isinstance(item, str)
                    else normalize_render_payload(item)
                    for item in value
                ]
            else:
                normalized[key] = normalize_render_payload(value)
        return normalized

    if isinstance(payload, list):
        return [normalize_render_payload(item) for item in payload]

    return payload
