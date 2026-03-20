"""
Student-facing marking + question routes.

POST /mark/batch              — submit all answers; returns marking results for every question
GET  /papers/{id}/questions   — return approved questions for a paper (student view)
POST /practice/mark           — mark a single practice question immediately
GET  /practice/next           — fetch next practice question (optionally weighted by weak topics)
POST /attempts/{id}/flag      — flag an attempt for review
"""

from __future__ import annotations

import random
import uuid
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from supabase import create_client

from core.config import settings
from services.batch_marking_service import mark_all, mark_mcq, mark_written_single

log = logging.getLogger(__name__)
router = APIRouter()


def _get_sb():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnswerSubmission(BaseModel):
    question_id: str
    question_text: str
    student_answer: str
    max_score: int
    question_type: Literal["written", "mcq"] = "written"
    answer_image_url: Optional[str] = None
    topic: Optional[str] = None


class BatchMarkRequest(BaseModel):
    paper_id: str
    answers: list[AnswerSubmission]


class QuestionMarkResult(BaseModel):
    question_id: str
    score: int
    max_score: int
    correct_points: list[str]
    missing_points: list[str]
    feedback_summary: str
    study_references: list[str]


class BatchMarkResponse(BaseModel):
    attempt_id: str
    total_score: int
    total_max_score: int
    results: list[QuestionMarkResult]


class PracticeMarkRequest(BaseModel):
    question_id: str
    question_text: str
    student_answer: str
    max_score: int
    question_type: Literal["written", "mcq"] = "written"
    answer_image_url: Optional[str] = None
    topic: Optional[str] = None
    subject_id: Optional[str] = None
    student_id: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /mark/batch
# ---------------------------------------------------------------------------

@router.post("/mark/batch", response_model=BatchMarkResponse)
async def batch_mark(req: BatchMarkRequest):
    """
    Mark all submitted answers in one call.
    - MCQ questions use answer-key lookup (zero Claude cost).
    - Written questions use Anthropic Message Batches API (50% cost savings).
    """
    if not req.answers:
        raise HTTPException(status_code=400, detail="No answers submitted.")

    sb = _get_sb()
    attempt_id = f"attempt-{uuid.uuid4().hex[:12]}"

    questions = [a.model_dump() for a in req.answers]

    try:
        results = await mark_all(questions, sb)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        log.exception("Batch marking error")
        raise HTTPException(status_code=500, detail=f"Marking error: {exc}")

    # Persist attempts to Supabase (best-effort — don't fail the request on DB error)
    for res in results:
        ans = next((a for a in req.answers if a.question_id == res["question_id"]), None)
        try:
            sb.table("attempt").upsert(
                {
                    "id": str(uuid.uuid4()),
                    "question_id": res["question_id"],
                    "student_answer": ans.student_answer if ans else "",
                    "answer_image_url": ans.answer_image_url if ans else None,
                    "ai_score": res["score"],
                    "ai_feedback": {
                        "feedback_summary": res["feedback_summary"],
                        "correct_points": res["correct_points"],
                        "missing_points": res["missing_points"],
                    },
                    "ai_references": res["study_references"],
                },
                on_conflict="question_id",
            ).execute()
        except Exception:
            pass  # non-fatal

    total_score = sum(r["score"] for r in results)
    total_max = sum(r["max_score"] for r in results)

    return BatchMarkResponse(
        attempt_id=attempt_id,
        total_score=total_score,
        total_max_score=total_max,
        results=[QuestionMarkResult(**r) for r in results],
    )


# ---------------------------------------------------------------------------
# GET /papers/{paper_id}/questions
# ---------------------------------------------------------------------------

@router.get("/papers/{paper_id}/questions")
def get_paper_questions(paper_id: str):
    """
    Return approved questions for a paper (student-facing).
    Includes MCQ options where present.
    """
    sb = _get_sb()
    rows = (
        sb.table("question")
        .select("*, mcq_answer(*)")
        .eq("paper_id", paper_id)
        .eq("qa_status", "approved")
        .order("question_number")
        .execute()
        .data
    )
    return rows


# ---------------------------------------------------------------------------
# POST /practice/mark
# ---------------------------------------------------------------------------

@router.post("/practice/mark")
async def practice_mark(req: PracticeMarkRequest):
    """
    Mark a single practice question immediately.
    Optionally updates weak_topic and syllabus_coverage tables if student context provided.
    """
    sb = _get_sb()

    q_dict = {
        "question_id": req.question_id,
        "question_text": req.question_text,
        "student_answer": req.student_answer,
        "max_score": req.max_score,
        "question_type": req.question_type,
        "answer_image_url": req.answer_image_url,
        "topic": req.topic or "",
        "subject_id": req.subject_id or "",
    }

    # Mark the answer
    if req.question_type == "mcq":
        result = await mark_mcq(q_dict, sb)
    else:
        result = await mark_written_single(q_dict, sb)

    # Persist attempt and get attempt_id
    attempt_id = str(uuid.uuid4())
    try:
        sb.table("attempt").insert(
            {
                "id": attempt_id,
                "question_id": req.question_id,
                "student_answer": req.student_answer,
                "answer_image_url": req.answer_image_url,
                "ai_score": result["score"],
                "ai_feedback": {
                    "feedback_summary": result["feedback_summary"],
                    "correct_points": result["correct_points"],
                    "missing_points": result["missing_points"],
                },
                "ai_references": result["study_references"],
            }
        ).execute()
    except Exception:
        attempt_id = None  # non-fatal

    # Update weak_topic and syllabus_coverage if student context provided
    if req.student_id and req.topic and req.subject_id:
        now_iso = datetime.now(timezone.utc).isoformat()
        is_fail = result["score"] < req.max_score * 0.5

        # weak_topic: select then update/insert
        try:
            existing = (
                sb.table("weak_topic")
                .select("id, attempt_count, fail_count")
                .eq("student_id", req.student_id)
                .eq("subject_id", req.subject_id)
                .eq("topic_name", req.topic)
                .limit(1)
                .execute()
                .data
            )
            if existing:
                row = existing[0]
                sb.table("weak_topic").update(
                    {
                        "attempt_count": row["attempt_count"] + 1,
                        "fail_count": row["fail_count"] + (1 if is_fail else 0),
                        "last_attempted": now_iso,
                    }
                ).eq("id", row["id"]).execute()
            else:
                sb.table("weak_topic").insert(
                    {
                        "student_id": req.student_id,
                        "subject_id": req.subject_id,
                        "topic_name": req.topic,
                        "attempt_count": 1,
                        "fail_count": 1 if is_fail else 0,
                        "last_attempted": now_iso,
                    }
                ).execute()
        except Exception:
            pass  # non-fatal

        # syllabus_coverage: set attempted=true
        try:
            existing_cov = (
                sb.table("syllabus_coverage")
                .select("id")
                .eq("student_id", req.student_id)
                .eq("subject_id", req.subject_id)
                .eq("topic_name", req.topic)
                .limit(1)
                .execute()
                .data
            )
            if existing_cov:
                sb.table("syllabus_coverage").update(
                    {"attempted": True, "last_attempted": now_iso}
                ).eq("id", existing_cov[0]["id"]).execute()
            else:
                sb.table("syllabus_coverage").insert(
                    {
                        "student_id": req.student_id,
                        "subject_id": req.subject_id,
                        "topic_name": req.topic,
                        "attempted": True,
                        "last_attempted": now_iso,
                    }
                ).execute()
        except Exception:
            pass  # non-fatal

    response = dict(result)
    if attempt_id:
        response["attempt_id"] = attempt_id

    return response


# ---------------------------------------------------------------------------
# GET /practice/next
# ---------------------------------------------------------------------------

@router.get("/practice/next")
def practice_next(
    subject_id: str = Query(...),
    student_id: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
):
    """
    Fetch the next practice question for a student.
    If student_id is provided, uses weak-topic weighting to prioritise weak areas.
    """
    sb = _get_sb()

    query = (
        sb.table("question")
        .select("*, mcq_answer(*)")
        .eq("subject_id", subject_id)
        .eq("qa_status", "approved")
    )

    if topic:
        query = query.contains("topic_tags", [topic])

    rows = query.execute().data

    if not rows:
        raise HTTPException(status_code=404, detail="No questions available for this subject.")

    if not student_id:
        return random.choice(rows)

    # Build weight map from weak_topic rows
    try:
        weak_rows = (
            sb.table("weak_topic")
            .select("topic_name, attempt_count, fail_count")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .execute()
            .data
        ) or []
    except Exception:
        weak_rows = []

    weight_map: dict[str, float] = {}
    for w in weak_rows:
        attempts = max(w.get("attempt_count", 0), 1)
        fail_ratio = w.get("fail_count", 0) / attempts
        weight_map[w["topic_name"]] = fail_ratio

    # Assign weight to each question
    def question_weight(q: dict) -> float:
        tags = q.get("topic_tags") or []
        if not tags:
            return 0.1
        return max((weight_map.get(t, 0.0) for t in tags), default=0.0) + 0.1

    weights = [question_weight(q) for q in rows]
    total = sum(weights)
    if total <= 0:
        return random.choice(rows)

    # Weighted random selection
    r = random.random() * total
    cumulative = 0.0
    for q, w in zip(rows, weights):
        cumulative += w
        if r <= cumulative:
            return q

    return rows[-1]


# ---------------------------------------------------------------------------
# POST /attempts/{attempt_id}/flag
# ---------------------------------------------------------------------------

@router.post("/attempts/{attempt_id}/flag")
def flag_attempt(attempt_id: str):
    """Flag an attempt for review (e.g. student disagrees with AI marking)."""
    sb = _get_sb()
    try:
        sb.table("attempt").update({"flagged": True}).eq("id", attempt_id).execute()
    except Exception as exc:
        log.warning("Could not flag attempt %s: %s", attempt_id, exc)
        raise HTTPException(status_code=500, detail="Could not flag attempt.")
    return {"ok": True}
