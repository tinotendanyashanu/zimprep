"""
AI Marking Service

Marks student attempts using Claude with cost optimisations:
- MCQ: answer key lookup (zero Claude cost)
- Haiku for ≤3 mark questions, Sonnet for >3 marks
- Exact answer caching (same question+answer = reuse result)
- Empty/trivial answers score 0 without calling Claude
- 20-char minimum for written answers
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from mistralai.client import Mistral
from mistralai.client.errors.sdkerror import SDKError

from db.client import get_supabase

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt


def _mistral_call_with_retry(fn, *args, **kwargs):
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except SDKError as exc:
            if "429" in str(exc) or "rate_limited" in str(exc).lower():
                if attempt < _MAX_RETRIES - 1:
                    logger.warning(
                        "Mistral rate-limit (attempt %d/%d) — waiting %ds",
                        attempt + 1, _MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise
    raise RuntimeError("Mistral marking call failed after all retries")

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
    # Try to find the option text for the correct answer
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
            # Answer key not stored yet — record answer but don't penalise
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
            # Not a valid MCQ selection — fall through to written marking
            question_type = "written"

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

    # ── Mistral marking ────────────────────────────────────────────────────────
    # mistral-small for ≤3 mark questions (fast + cheap), mistral-large for longer answers
    model = "mistral-small-latest" if marks <= 3 else "mistral-large-latest"
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"], timeout_ms=60_000)

    prompt = (
        f"Subject: {subject['name']} ({subject['level']})\n"
        f"Question ({marks} mark{'s' if marks != 1 else ''}): {question['text']}\n"
        f"Student Answer: {student_answer}"
    )

    try:
        response = _mistral_call_with_retry(
            client.chat.complete,
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": MARKING_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        # Strip markdown fences if the model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        result = json.loads(raw)
    except Exception as exc:
        logger.error("Mistral marking failed for attempt %s: %s", attempt_id, exc, exc_info=True)
        result = dict(_FALLBACK_RESULT)

    _update_attempt(attempt_id, result, marks)


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
