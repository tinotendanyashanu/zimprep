"""
Batch marking service.

Written answers  → Anthropic Message Batches API (50% cost vs standard API).
MCQ answers      → Supabase answer-key lookup (zero Claude cost).
Single written   → Standard Anthropic API (for practice mode / immediate marking).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import logging
from typing import Optional

import anthropic
from supabase import Client

from core.config import settings

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a ZIMSEC examination marking expert. "
    "Mark student answers strictly and fairly against the expected syllabus knowledge. "
    "Return ONLY valid JSON — no markdown fences, no extra text. "
    "If the student's answer is gibberish, off-topic, contains fewer than 20 meaningful characters, "
    "or is completely blank, award score=0 with missing_points=['No substantive answer provided'] "
    "and feedback_summary='No credit awarded — answer did not address the question.'"
)

MARKING_USER_TEMPLATE = """\
Question: {question_text}
Max Score: {max_score}
Student Answer: {student_answer}

Return a JSON object with EXACTLY these fields:
{{
  "score": <integer 0-{max_score}>,
  "max_score": {max_score},
  "correct_points": [<strings — what the student answered correctly>],
  "missing_points": [<strings — what was missing or incorrect>],
  "feedback_summary": "<2-3 sentence overall feedback>",
  "study_references": [<topic names or syllabus sections to review>]
}}"""

MARKING_USER_TEMPLATE_WITH_CONTEXT = """\
Syllabus Context (for reference):
{syllabus_context}

Question: {question_text}
Max Score: {max_score}
Student Answer: {student_answer}

Return a JSON object with EXACTLY these fields:
{{
  "score": <integer 0-{max_score}>,
  "max_score": {max_score},
  "correct_points": [<strings — what the student answered correctly>],
  "missing_points": [<strings — what was missing or incorrect>],
  "feedback_summary": "<2-3 sentence overall feedback>",
  "study_references": [<topic names or syllabus sections to review>]
}}"""


# ---------------------------------------------------------------------------
# Model routing
# ---------------------------------------------------------------------------

def _get_model(max_score: int) -> str:
    """Route to haiku for low-stakes questions, sonnet for higher-value ones."""
    if max_score <= 3:
        return "claude-haiku-4-5-20251001"
    return "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Answer hash caching
# ---------------------------------------------------------------------------

def _cache_key(question_id: str, student_answer: str) -> str:
    """Deterministic SHA-256 hash for a (question, answer) pair."""
    payload = f"{question_id}:{student_answer.strip().lower()}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _get_cached_result(answer_hash: str, sb: Client) -> Optional[dict]:
    """Look up a cached marking result. Returns None on miss or error."""
    try:
        row = (
            sb.table("marking_cache")
            .select("result")
            .eq("answer_hash", answer_hash)
            .single()
            .execute()
            .data
        )
        if row:
            return row["result"]
    except Exception:
        pass
    return None


def _store_cached_result(answer_hash: str, result: dict, sb: Client) -> None:
    """Persist a marking result to cache. Best-effort — never raises."""
    try:
        sb.table("marking_cache").upsert(
            {"answer_hash": answer_hash, "result": result},
            on_conflict="answer_hash",
        ).execute()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Syllabus context fetching
# ---------------------------------------------------------------------------

def _fetch_syllabus_context(topic: str, subject_id: str, sb: Client) -> str:
    """
    Fetch relevant syllabus content for the given topic and subject.
    Returns the first matching chunk truncated to ~1200 chars (≈300 tokens).
    Returns empty string on miss or error.
    """
    try:
        rows = (
            sb.table("syllabus_chunk")
            .select("content")
            .eq("subject_id", subject_id)
            .ilike("topic_name", f"%{topic}%")
            .limit(1)
            .execute()
            .data
        )
        if rows:
            return rows[0]["content"][:1200]
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# MCQ marking — answer-key lookup (zero Claude cost)
# ---------------------------------------------------------------------------

async def mark_mcq(q: dict, sb: Client) -> dict:
    """Compare student's MCQ selection against the stored answer key."""
    question_id = q["question_id"]
    student_answer = (q.get("student_answer") or "").strip().upper()
    max_score = q.get("max_score", 1)

    try:
        row = (
            sb.table("mcq_answer")
            .select("correct_option")
            .eq("question_id", question_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        row = None

    if not row:
        return {
            "question_id": question_id,
            "score": 0,
            "max_score": max_score,
            "correct_points": [],
            "missing_points": ["Answer key not available for this question."],
            "feedback_summary": "This question could not be marked automatically.",
            "study_references": [],
        }

    correct = row["correct_option"]
    is_correct = student_answer == correct

    return {
        "question_id": question_id,
        "score": max_score if is_correct else 0,
        "max_score": max_score,
        "correct_points": [f"Selected {correct} — correct."] if is_correct else [],
        "missing_points": (
            []
            if is_correct
            else [f"Correct answer is {correct}; you selected '{student_answer or 'nothing'}'."]
        ),
        "feedback_summary": "Correct!" if is_correct else f"The correct answer was {correct}.",
        "study_references": [] if is_correct else [q.get("topic", "Review this topic")],
    }


# ---------------------------------------------------------------------------
# Written marking — Anthropic Message Batches API
# ---------------------------------------------------------------------------

def _build_user_message(q: dict, syllabus_context: str = "") -> str:
    """Build the user message content for a marking request."""
    if syllabus_context:
        return MARKING_USER_TEMPLATE_WITH_CONTEXT.format(
            syllabus_context=syllabus_context,
            question_text=q.get("question_text", ""),
            max_score=q.get("max_score", 0),
            student_answer=q.get("student_answer", "(no answer provided)"),
        )
    return MARKING_USER_TEMPLATE.format(
        question_text=q.get("question_text", ""),
        max_score=q.get("max_score", 0),
        student_answer=q.get("student_answer", "(no answer provided)"),
    )


def _build_request(q: dict, syllabus_context: str = "") -> anthropic.types.beta.messages.MessageBatchRequestParam:
    model = _get_model(q.get("max_score", 0))
    return anthropic.types.beta.messages.MessageBatchRequestParam(
        custom_id=q["question_id"],
        params={
            "model": model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": _build_user_message(q, syllabus_context),
                }
            ],
        },
    )


def _parse_result_text(text: str, q: dict) -> dict:
    raw = text.strip()
    # Strip markdown fences if Claude wraps in them despite the prompt
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    try:
        parsed = json.loads(raw)
        return {
            "question_id": q["question_id"],
            "score": int(parsed.get("score", 0)),
            "max_score": int(parsed.get("max_score", q.get("max_score", 0))),
            "correct_points": parsed.get("correct_points", []),
            "missing_points": parsed.get("missing_points", []),
            "feedback_summary": parsed.get("feedback_summary", ""),
            "study_references": parsed.get("study_references", []),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "question_id": q["question_id"],
            "score": 0,
            "max_score": q.get("max_score", 0),
            "correct_points": [],
            "missing_points": ["Could not parse marking result."],
            "feedback_summary": "Marking error — please contact support.",
            "study_references": [],
        }


async def mark_written_batch(questions: list[dict], sb: Optional[Client] = None) -> list[dict]:
    """
    Mark written answers via Anthropic Messages Batches API.
    Provides ~50% cost reduction vs standard per-message calls.
    Polls until the batch is complete (typically < 2 minutes for small batches).
    Checks marking_cache before sending to Claude; stores new results after.
    """
    if not questions:
        return []

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    q_map = {q["question_id"]: q for q in questions}

    # Split into cached and uncached
    cached_results: list[dict] = []
    uncached_questions: list[dict] = []

    for q in questions:
        if sb:
            key = _cache_key(q["question_id"], q.get("student_answer", ""))
            cached = _get_cached_result(key, sb)
            if cached:
                log.debug("Cache hit for question %s", q["question_id"])
                result = dict(cached)
                result["question_id"] = q["question_id"]
                cached_results.append(result)
                continue
        uncached_questions.append(q)

    if not uncached_questions:
        return cached_results

    # Create batch for uncached questions
    batch = client.beta.messages.batches.create(
        requests=[_build_request(q) for q in uncached_questions]
    )
    batch_id = batch.id
    log.info("Anthropic batch created: %s (%d questions)", batch_id, len(uncached_questions))

    # Poll until processing_status == "ended" (max ~5 minutes)
    for poll_num in range(60):
        await asyncio.sleep(5)
        status = client.beta.messages.batches.retrieve(batch_id)
        log.debug("Batch %s status: %s (poll %d)", batch_id, status.processing_status, poll_num)
        if status.processing_status == "ended":
            break
    else:
        raise RuntimeError(
            "Batch marking timed out after 5 minutes. Please retry submission."
        )

    # Collect results
    batch_results: list[dict] = []
    for result in client.beta.messages.batches.results(batch_id):
        q = q_map.get(result.custom_id, {"question_id": result.custom_id, "max_score": 0})
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            parsed = _parse_result_text(text, q)
            batch_results.append(parsed)
            # Store in cache
            if sb:
                key = _cache_key(q["question_id"], q.get("student_answer", ""))
                _store_cached_result(key, parsed, sb)
        else:
            batch_results.append({
                "question_id": result.custom_id,
                "score": 0,
                "max_score": q.get("max_score", 0),
                "correct_points": [],
                "missing_points": [f"Batch result type: {result.result.type}"],
                "feedback_summary": "Marking failed for this question.",
                "study_references": [],
            })

    all_results = cached_results + batch_results

    # Preserve original order
    result_map = {r["question_id"]: r for r in all_results}
    return [result_map[q["question_id"]] for q in questions if q["question_id"] in result_map]


# ---------------------------------------------------------------------------
# Single written question marking — standard API (for practice mode)
# ---------------------------------------------------------------------------

async def mark_written_single(q: dict, sb: Client) -> dict:
    """
    Mark a single written question immediately using the standard Claude API.
    Uses model routing, checks cache first, stores result after.
    Accepts the same q dict shape as batch marking.
    """
    question_id = q["question_id"]
    student_answer = q.get("student_answer", "")
    max_score = q.get("max_score", 0)

    # Check cache first
    key = _cache_key(question_id, student_answer)
    cached = _get_cached_result(key, sb)
    if cached:
        log.debug("Cache hit (single) for question %s", question_id)
        result = dict(cached)
        result["question_id"] = question_id
        return result

    # Fetch syllabus context if topic and subject_id are available
    syllabus_context = ""
    topic = q.get("topic", "")
    subject_id = q.get("subject_id", "")
    if topic and subject_id:
        syllabus_context = _fetch_syllabus_context(topic, subject_id, sb)

    model = _get_model(max_score)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _build_user_message(q, syllabus_context),
                }
            ],
        )
        text = message.content[0].text
        result = _parse_result_text(text, q)
    except Exception as exc:
        log.exception("Single marking error for question %s", question_id)
        result = {
            "question_id": question_id,
            "score": 0,
            "max_score": max_score,
            "correct_points": [],
            "missing_points": ["Marking service error."],
            "feedback_summary": f"Could not mark this answer: {exc}",
            "study_references": [],
        }

    # Store in cache
    _store_cached_result(key, result, sb)
    return result


# ---------------------------------------------------------------------------
# Unified batch marking entry point
# ---------------------------------------------------------------------------

async def mark_all(questions: list[dict], sb: Client) -> list[dict]:
    """
    Route each question to the correct marking path:
    - MCQ  → answer-key lookup (zero Claude cost)
    - Written → Anthropic batch API (50% cost savings)
    """
    mcq_qs = [q for q in questions if q.get("question_type") == "mcq"]
    written_qs = [q for q in questions if q.get("question_type") != "mcq"]

    mcq_results = [await mark_mcq(q, sb) for q in mcq_qs]
    written_results = await mark_written_batch(written_qs, sb)

    # Preserve original order
    result_map = {r["question_id"]: r for r in mcq_results + written_results}
    return [result_map[q["question_id"]] for q in questions if q["question_id"] in result_map]
