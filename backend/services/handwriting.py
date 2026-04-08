"""
Handwriting interpretation helpers for photo-based answer submissions.
"""
from __future__ import annotations

import json
import logging
import mimetypes
import re
from typing import Any

import httpx
from google.genai import types

from services.llm_router import call_llm

logger = logging.getLogger(__name__)

_OCR_SYSTEM_PROMPT = """You are an OCR transcription engine for student handwritten exam answers.
Transcribe only what is visible in the student's answer image.
Rules:
- Do not grade or correct the answer.
- Do not invent missing words, equations, or symbols.
- Preserve academic notation exactly when readable.
- If part is unreadable, keep it brief and mark it as [illegible].
Return plain text only. No markdown. No JSON."""

_CANONICAL_SYSTEM_PROMPT = """You are the Handwritten Answer Interpretation Engine for an AI-powered exam system.

Your job is to convert a student's uploaded handwritten answer into a clean, structured, machine-markable canonical answer.

Follow this algorithm strictly:
1. Clean OCR noise, duplicated characters, and unreadable fragments.
2. Normalize symbols when supported by the text, without changing meaning.
3. Interpret according to the subject:
   - Mathematics / Physics: extract equations, identify steps, detect final answer
   - Chemistry: preserve formulas, states, and reactions
   - Accounts / Economics: preserve numerical and table-like structure
   - Biology / Theory subjects: preserve sentences, terms, and definitions
   - Geography / Mixed: preserve descriptive and structured parts
4. Merge optional typed clarification, giving it priority where it conflicts with OCR.
5. Estimate confidence from OCR clarity, completeness, and consistency.

Constraints:
- Do not invent content.
- Do not correct the student's logic.
- Use only the supplied OCR text and optional typed clarification.
- Remain faithful to the student's response.

Return ONLY valid JSON with this exact schema:
{
  "final_answer": "",
  "steps": [],
  "explanation": "",
  "equations": [],
  "tables": [],
  "notes": "",
  "confidence": 0.0
}"""

_DEFAULT_CANONICAL = {
    "final_answer": "",
    "steps": [],
    "explanation": "",
    "equations": [],
    "tables": [],
    "notes": "",
}


def _strip_json_fences(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _clean_whitespace(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def _normalize_symbols(text: str, subject: str) -> str:
    normalized = (text or "").replace("->", "→")
    subject_key = (subject or "").strip().lower()
    if subject_key in {"mathematics", "physics"}:
        normalized = re.sub(r"\b([A-Za-z])2\b", r"\1²", normalized)
        normalized = re.sub(r"\b([A-Za-z])3\b", r"\1³", normalized)
    return normalized


def clean_ocr_text(text: str, subject: str) -> str:
    cleaned = (text or "").replace("\uFFFD", " ")
    cleaned = re.sub(r"([A-Za-z0-9=+\-])\1{3,}", r"\1\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = _clean_whitespace(cleaned)
    return _normalize_symbols(cleaned, subject)


def _guess_mime_type(image_url: str, headers: httpx.Headers) -> str:
    content_type = headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type.startswith("image/"):
        return content_type
    guessed, _ = mimetypes.guess_type(image_url)
    return guessed or "image/jpeg"


def _fetch_image_bytes(image_url: str) -> tuple[bytes, str]:
    response = httpx.get(image_url, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    return response.content, _guess_mime_type(image_url, response.headers)


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_tables(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _validation_status(confidence: float) -> str:
    if confidence > 0.85:
        return "proceed"
    if confidence >= 0.6:
        return "confirm"
    return "resubmit"


def extract_ocr_text(question_text: str, subject: str, answer_image_url: str) -> str:
    image_bytes, mime_type = _fetch_image_bytes(answer_image_url)
    parts: list[Any] = [
        (
            f"Subject: {subject or 'Unknown'}\n"
            f"Question:\n{question_text or ''}\n\n"
            "Transcribe only the student's answer from the image."
        ),
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
    ]
    response = call_llm(
        "extraction",
        parts,
        _OCR_SYSTEM_PROMPT,
        {"max_output_tokens": 2000, "batch_size": 1},
    )
    return clean_ocr_text(response.text or "", subject)


def canonicalize_answer(
    question_text: str,
    subject: str,
    ocr_extracted_text: str,
    optional_typed_input: str | None = None,
) -> dict[str, Any]:
    typed = _clean_whitespace(optional_typed_input or "")
    prompt = (
        f"question_text:\n{question_text or ''}\n\n"
        f"subject:\n{subject or ''}\n\n"
        f"OCR_extracted_text:\n{ocr_extracted_text or ''}\n\n"
        f"optional_typed_input:\n{typed}\n"
    )
    response = call_llm(
        "verification",
        [prompt],
        _CANONICAL_SYSTEM_PROMPT,
        {"max_output_tokens": 2500},
    )
    raw = _strip_json_fences(response.text or "")
    parsed = json.loads(raw)

    confidence = parsed.get("confidence", 0.0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0

    canonical = {
        "final_answer": str(parsed.get("final_answer", "") or "").strip(),
        "steps": _coerce_string_list(parsed.get("steps")),
        "explanation": str(parsed.get("explanation", "") or "").strip(),
        "equations": _coerce_string_list(parsed.get("equations")),
        "tables": _coerce_tables(parsed.get("tables")),
        "notes": str(parsed.get("notes", "") or "").strip(),
    }
    return {
        "canonical_answer": canonical,
        "confidence": confidence,
        "status": _validation_status(confidence),
    }


def interpret_handwritten_answer(
    *,
    question_text: str,
    subject: str,
    answer_image_url: str,
    optional_typed_input: str | None = None,
) -> dict[str, Any]:
    fallback = {
        "canonical_answer": {
            **_DEFAULT_CANONICAL,
            "final_answer": _clean_whitespace(optional_typed_input or ""),
            "notes": "Handwriting interpretation failed.",
        },
        "confidence": 0.0,
        "status": "resubmit",
    }

    try:
        ocr_text = extract_ocr_text(question_text, subject, answer_image_url)
        interpreted = canonicalize_answer(
            question_text=question_text,
            subject=subject,
            ocr_extracted_text=ocr_text,
            optional_typed_input=optional_typed_input,
        )
        return interpreted
    except Exception as exc:
        logger.error("Handwriting interpretation failed: %s", exc, exc_info=True)
        return fallback


def serialize_handwriting_result(result: dict[str, Any]) -> str:
    payload = {
        **(result.get("canonical_answer") or _DEFAULT_CANONICAL),
        "confidence": float(result.get("confidence", 0.0) or 0.0),
    }
    return json.dumps(payload, ensure_ascii=False)


def load_handwriting_result(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    confidence = parsed.get("confidence", 0.0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "canonical_answer": {
            "final_answer": str(parsed.get("final_answer", "") or "").strip(),
            "steps": _coerce_string_list(parsed.get("steps")),
            "explanation": str(parsed.get("explanation", "") or "").strip(),
            "equations": _coerce_string_list(parsed.get("equations")),
            "tables": _coerce_tables(parsed.get("tables")),
            "notes": str(parsed.get("notes", "") or "").strip(),
        },
        "confidence": confidence,
        "status": _validation_status(confidence),
    }


def canonical_answer_to_text(result: dict[str, Any] | None) -> str:
    if not result:
        return ""

    canonical = result.get("canonical_answer") or {}
    parts: list[str] = []

    final_answer = str(canonical.get("final_answer", "") or "").strip()
    if final_answer:
        parts.append(f"Final answer: {final_answer}")

    steps = _coerce_string_list(canonical.get("steps"))
    if steps:
        parts.append("Steps:\n" + "\n".join(f"- {step}" for step in steps))

    explanation = str(canonical.get("explanation", "") or "").strip()
    if explanation:
        parts.append(f"Explanation: {explanation}")

    equations = _coerce_string_list(canonical.get("equations"))
    if equations:
        parts.append("Equations:\n" + "\n".join(f"- {equation}" for equation in equations))

    tables = canonical.get("tables")
    if tables:
        parts.append("Tables:\n" + json.dumps(tables, ensure_ascii=False))

    notes = str(canonical.get("notes", "") or "").strip()
    if notes:
        parts.append(f"Notes: {notes}")

    return "\n\n".join(parts).strip()
