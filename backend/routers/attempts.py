"""
Attempt routes — practice mode submission and flagging.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.client import get_supabase
from db.models_subscription import DAILY_FREE_LIMIT
from services.content_formatting import normalize_render_payload
from services.marking import mark_attempt
from services.quota import check_practice_quota

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request schemas ────────────────────────────────────────────────────────────

class SubmitAttemptRequest(BaseModel):
    session_id: str
    question_id: str
    student_answer: Optional[str] = None
    answer_image_url: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/")
def submit_attempt(body: SubmitAttemptRequest) -> dict[str, Any]:
    """
    Submit a single answer (practice mode). Marks synchronously and returns
    the attempt row with AI feedback.

    Re-submissions for the same (session_id, question_id) are allowed — the
    existing attempt is updated and re-marked instead of inserting a duplicate
    (which would violate the unique constraint added in migration 002).
    Re-submissions bypass the daily quota since no new question is consumed.
    """
    supabase = get_supabase()

    # Check whether this is a re-submission for the same question in this session
    existing = (
        supabase.table("attempt")
        .select("id")
        .eq("session_id", body.session_id)
        .eq("question_id", body.question_id)
        .maybe_single()
        .execute()
    )
    is_resubmission = bool(existing and existing.data)

    # Quota check: only applies to first-time submissions of written questions
    if not is_resubmission:
        question_type = "written"
        q_result = (
            supabase.table("question")
            .select("question_type")
            .eq("id", body.question_id)
            .maybe_single()
            .execute()
        )
        if q_result and q_result.data:
            question_type = q_result.data.get("question_type", "written")

        quota = check_practice_quota(body.session_id, question_type)
        if not quota.allowed:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "quota_exceeded",
                    "tier": quota.tier,
                    "used": quota.used,
                    "limit": quota.limit,
                    "feature": "practice",
                    "message": f"Daily limit of {DAILY_FREE_LIMIT} questions reached. "
                               "Upgrade to continue practising.",
                },
            )

    if is_resubmission:
        attempt_id = existing.data["id"]
        # Reset marking fields so mark_attempt re-marks with the new answer
        supabase.table("attempt").update(
            {
                "student_answer": body.student_answer,
                "answer_image_url": body.answer_image_url,
                "ai_score": None,
                "ai_feedback": None,
                "ai_references": None,
                "marked_at": None,
            }
        ).eq("id", attempt_id).execute()
    else:
        attempt_id = str(uuid.uuid4())
        supabase.table("attempt").insert(
            {
                "id": attempt_id,
                "session_id": body.session_id,
                "question_id": body.question_id,
                "student_answer": body.student_answer,
                "answer_image_url": body.answer_image_url,
            }
        ).execute()

    # Synchronous marking for immediate feedback in practice mode
    mark_attempt(attempt_id)

    result = (
        supabase.table("attempt")
        .select("*")
        .eq("id", attempt_id)
        .maybe_single()
        .execute()
    )
    return normalize_render_payload(result.data) if (result and result.data) else {}


@router.get("/{attempt_id}")
def get_attempt(attempt_id: str) -> dict[str, Any]:
    """Retrieve an attempt by ID, including AI feedback if marked."""
    supabase = get_supabase()
    result = (
        supabase.table("attempt")
        .select("*")
        .eq("id", attempt_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return normalize_render_payload(result.data)


class FlagAttemptRequest(BaseModel):
    reason: str  # 'question_issue' | 'marking_issue'


@router.patch("/{attempt_id}/flag")
def flag_attempt(attempt_id: str, body: FlagAttemptRequest) -> dict[str, Any]:
    """
    Flag an attempt with a reason.

    - 'marking_issue'  — student believes AI marked their answer wrong.
    - 'question_issue' — student reports the question itself is wrong/unclear.
                         The question is immediately hidden from all students
                         and queued for admin review.
    """
    if body.reason not in ("question_issue", "marking_issue"):
        raise HTTPException(status_code=422, detail="reason must be 'question_issue' or 'marking_issue'")

    supabase = get_supabase()

    attempt = (
        supabase.table("attempt")
        .select("id, question_id")
        .eq("id", attempt_id)
        .maybe_single()
        .execute()
    )
    if not attempt or not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    supabase.table("attempt").update({
        "flagged": True,
        "flag_reason": body.reason,
    }).eq("id", attempt_id).execute()

    # For question issues: hide the question from all students immediately
    # and send it to the admin review queue.
    if body.reason == "question_issue":
        question_id = attempt.data["question_id"]
        supabase.table("question").update({
            "hidden": True,
            "needs_review": True,
            "review_reasons": ["student_flag"],
        }).eq("id", question_id).execute()

    return {"flagged": True, "reason": body.reason}
