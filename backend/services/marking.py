"""
AI Marking Service

Marks student attempts using Google Gemini 2.0 Flash with cost optimisations:
- MCQ: answer key lookup (zero AI cost)
- Written: Gemini 2.0 Flash for all mark values
- Exact answer caching (same question+answer = reuse result)
- Empty/trivial answers score 0 without calling AI
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from db.client import get_supabase

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt


def _gemini_call_with_retry(fn, *args, **kwargs):
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            msg = str(exc).lower()
            is_retryable = "429" in msg or "quota" in msg or "rate" in msg or "resource exhausted" in msg
            if is_retryable and attempt < _MAX_RETRIES - 1:
                logger.warning(
                    "Gemini rate-limit (attempt %d/%d) — waiting %ds",
                    attempt + 1, _MAX_RETRIES, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("Gemini marking call failed after all retries")


MARKING_SYSTEM_PROMPT = """You are an experienced ZIMSEC examiner. Given a question and a student's answer, evaluate the answer and return ONLY valid JSON matching this schema exactly:
{
  "score": <integer from 0 to the question's maximum marks>,
  "feedback": {
    "correct_points": [<string>, ...],
    "missing_points": [<string>, ...],
    "examiner_note": <string>
  },
  "references": [<topic string>, ...]
}
No preamble. No markdown. No explanation outside the JSON."""

_FALLBACK_RESULT: dict[str, Any] = {
    "score": 0,
    "feedback": {
        "correct_points": [],
        "missing_points": [],
        "examiner_note": "Marking error — please flag this question.",
    },
    "references": [],
}


def _mcq_static_note(
    question: dict[str, Any],
    given: str,
    correct: str,
) -> str:
    """
    Build an instant, zero-cost examiner note for an MCQ result.

    Shows the correct option letter and its text (if mcq_options are stored),
    plus a brief note when the student was wrong.
    """
    correct_text = ""
    if question.get("mcq_options"):
        for opt in question["mcq_options"]:
            if opt.get("letter") == correct:
                correct_text = opt.get("text", "")
                break

    if given == correct:
        if correct_text:
            return f"Correct. {correct} — {correct_text}"
        return "Correct."
    else:
        if correct_text:
            return f"The correct answer is {correct} — {correct_text}."
        return f"The correct answer is {correct}."


def _update_attempt(attempt_id: str, result: dict[str, Any], marks: int) -> None:
    supabase = get_supabase()
    score = min(int(result.get("score", 0)), marks)
    supabase.table("attempt").update(
        {
            "ai_score": score,
            "ai_feedback": result.get("feedback"),
            "ai_references": result.get("references", []),
            "marked_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", attempt_id).execute()


def mark_attempt(attempt_id: str) -> None:
    """
    Mark a single attempt. Designed to be called directly (practice mode)
    or from mark_session (exam mode background task).
    """
    supabase = get_supabase()

    # Fetch attempt with nested question + subject
    row = (
        supabase.table("attempt")
        .select("*, question!inner(*, subject!inner(*))")
        .eq("id", attempt_id)
        .maybe_single()
        .execute()
    )
    if not row or not row.data:
        logger.error("Attempt %s not found", attempt_id)
        return

    attempt = row.data
    question = attempt["question"]
    subject = question["subject"]
    marks: int = int(question.get("marks", 0))
    student_answer: str | None = attempt.get("student_answer")
    question_type: str = question.get("question_type", "written")

    result: dict[str, Any]

    # ── MCQ path ───────────────────────────────────────────────────────────────
    if question_type == "mcq":
        given = (student_answer or "").strip().upper()
        mcq_row = (
            supabase.table("mcq_answer")
            .select("correct_option")
            .eq("question_id", question["id"])
            .maybe_single()
            .execute()
        )
        if mcq_row and mcq_row.data:
            correct = mcq_row.data["correct_option"]
            is_correct = given == correct
            result = {
                "score": marks if is_correct else 0,
                "feedback": {
                    "correct_points": [f"You selected {given} — correct!"] if is_correct else [],
                    "missing_points": [] if is_correct else [f"You selected {given}. The correct answer is {correct}."],
                    "examiner_note": _mcq_static_note(question, given, correct),
                },
                "references": [],
            }
            _update_attempt(attempt_id, result, marks)
            return
        elif given in ("A", "B", "C", "D"):
            logger.warning(
                "MCQ answer row missing for question %s — recording answer without scoring",
                question["id"],
            )
            result = {
                "score": 0,
                "feedback": {
                    "correct_points": [],
                    "missing_points": [],
                    "examiner_note": "Answer recorded. The answer key for this question is not yet available.",
                },
                "references": [],
            }
            _update_attempt(attempt_id, result, marks)
            return
        else:
            result = {
                "score": 0,
                "feedback": {
                    "correct_points": [],
                    "missing_points": [],
                    "examiner_note": (
                        f"Invalid MCQ answer '{given}'. Please select A, B, C, or D."
                        if given
                        else "No answer selected."
                    ),
                },
                "references": [],
            }
            _update_attempt(attempt_id, result, marks)
            return

    # ── Empty / trivial answer gate ────────────────────────────────────────────
    if not student_answer or not student_answer.strip():
        result = {
            "score": 0,
            "feedback": {
                "correct_points": [],
                "missing_points": [],
                "examiner_note": "No answer provided.",
            },
            "references": [],
        }
        _update_attempt(attempt_id, result, marks)
        return

    if len(student_answer.strip()) < 3:
        result = {
            "score": 0,
            "feedback": {
                "correct_points": [],
                "missing_points": [],
                "examiner_note": "Answer too short to evaluate.",
            },
            "references": [],
        }
        _update_attempt(attempt_id, result, marks)
        return

    # ── Cache check ────────────────────────────────────────────────────────────
    cached = (
        supabase.table("attempt")
        .select("ai_score, ai_feedback, ai_references")
        .eq("question_id", question["id"])
        .eq("student_answer", student_answer)
        .not_.is_("marked_at", "null")
        .neq("id", attempt_id)
        .limit(1)
        .execute()
    )
    if cached.data:
        cached_row = cached.data[0]
        result = {
            "score": cached_row["ai_score"],
            "feedback": cached_row["ai_feedback"],
            "references": cached_row["ai_references"] or [],
        }
        _update_attempt(attempt_id, result, marks)
        return

    # ── Gemini marking ─────────────────────────────────────────────────────────
    from google import genai
    from google.genai import types

    prompt = (
        f"Subject: {subject['name']} ({subject['level']})\n"
        f"Question ({marks} mark{'s' if marks != 1 else ''}): {question['text']}\n"
        f"Student Answer: {student_answer}"
    )

    try:
        client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
        response = _gemini_call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=MARKING_SYSTEM_PROMPT,
                # Allow limited thinking for marking — reasoning over student answers
                # meaningfully improves score accuracy. 1024 tokens is enough for
                # most questions without running up large thinking bills.
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=1024),
            ),
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
    except Exception as exc:
        logger.error("Gemini marking failed for attempt %s: %s", attempt_id, exc, exc_info=True)
        result = dict(_FALLBACK_RESULT)

    _update_attempt(attempt_id, result, marks)


_MCQ_EXPLANATION_SYSTEM_PROMPT = """You are an expert ZIMSEC/Cambridge examiner.
For each MCQ question listed below, explain concisely (2–3 sentences) why the correct answer is correct
and, where the student chose wrong, why their choice is incorrect.
Return ONLY valid JSON: an object where keys are the 0-based question index (as a string)
and values are explanation strings.
Example: {"0": "The correct answer is B because...", "1": "C is correct here because..."}
No preamble. No markdown. No extra keys."""


def generate_mcq_explanations(session_id: str) -> dict[str, str]:
    """
    Make ONE LLM call to explain all incorrectly answered MCQ questions in a session.
    Returns a dict mapping attempt_id → explanation string.
    Only called on explicit student request (on-demand) or end-of-exam trigger.
    """
    supabase = get_supabase()

    # Fetch all MCQ attempts in this session with question data
    attempts_result = (
        supabase.table("attempt")
        .select(
            "id, question_id, student_answer, ai_score, "
            "question!inner(marks, text, mcq_options, question_type)"
        )
        .eq("session_id", session_id)
        .execute()
    )
    attempts = attempts_result.data or []

    # Only process wrong MCQ attempts that were actually marked
    wrong_mcq: list[dict[str, Any]] = []
    for a in attempts:
        q = a.get("question") or {}
        if q.get("question_type") != "mcq":
            continue
        marks = int(q.get("marks") or 1)
        score = int(a.get("ai_score") or 0)
        if score >= marks:
            continue  # correct — no explanation needed

        # Look up the stored correct answer
        mcq_row = (
            supabase.table("mcq_answer")
            .select("correct_option")
            .eq("question_id", a["question_id"])
            .maybe_single()
            .execute()
        )
        correct = mcq_row.data["correct_option"] if (mcq_row and mcq_row.data) else None

        wrong_mcq.append({
            "attempt_id": a["id"],
            "text": q.get("text", ""),
            "mcq_options": q.get("mcq_options") or [],
            "student_answer": (a.get("student_answer") or "").strip().upper(),
            "correct_answer": correct,
        })

    if not wrong_mcq:
        return {}

    # Build ONE batch prompt for all wrong MCQ questions
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

    prompt_lines: list[str] = []
    for i, item in enumerate(wrong_mcq):
        opts = item["mcq_options"]
        if opts:
            opts_text = "  |  ".join(
                f"{o['letter']}: {o['text']}"
                for o in opts
                if isinstance(o, dict) and o.get("letter") and o.get("text")
            )
        else:
            opts_text = "No options stored"
        correct = item["correct_answer"] or "Unknown"
        student = item["student_answer"] or "None"
        prompt_lines.append(
            f"{i}. {item['text']}\n"
            f"   Options: {opts_text}\n"
            f"   Correct answer: {correct}  |  Student chose: {student}"
        )

    prompt = "\n\n".join(prompt_lines)

    try:
        response = _gemini_call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_MCQ_EXPLANATION_SYSTEM_PROMPT,
                max_output_tokens=min(4096, 256 + len(wrong_mcq) * 200),
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        raw_explanations: dict[str, str] = json.loads(raw)
    except Exception as exc:
        logger.error(
            "MCQ batch explanation failed for session %s: %s", session_id, exc
        )
        return {}

    # Map index → attempt_id
    result: dict[str, str] = {}
    for idx_str, explanation in raw_explanations.items():
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        if idx < len(wrong_mcq):
            result[wrong_mcq[idx]["attempt_id"]] = str(explanation)

    logger.info(
        "Generated MCQ explanations for %d/%d wrong attempts in session %s",
        len(result), len(wrong_mcq), session_id,
    )
    return result


def mark_session(session_id: str) -> None:
    """
    Batch mark all attempts in a session. Designed to run as a FastAPI BackgroundTask.
    Each attempt is marked independently — one failure does not block the rest.
    """
    supabase = get_supabase()
    attempts = (
        supabase.table("attempt")
        .select("id")
        .eq("session_id", session_id)
        .execute()
    )
    for row in attempts.data:
        try:
            mark_attempt(row["id"])
        except Exception as exc:
            logger.error(
                "Failed to mark attempt %s in session %s: %s",
                row["id"],
                session_id,
                exc,
            )
    logger.info("Batch marking complete for session %s", session_id)
