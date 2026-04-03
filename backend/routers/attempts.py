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
    """
    # Quota check: determine question type first (MCQ is free, written counts against limit)
    question_type = "written"
    if body.session_id:
        supabase_check = get_supabase()
        q_result = (
            supabase_check.table("question")
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

    supabase = get_supabase()
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
    return result.data if (result and result.data) else {}


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
    return result.data


@router.patch("/{attempt_id}/flag")
def flag_attempt(attempt_id: str) -> dict[str, Any]:
    """Flag an attempt for review of incorrect marking."""
    supabase = get_supabase()
    result = supabase.table("attempt").select("id").eq("id", attempt_id).maybe_single().execute()
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    supabase.table("attempt").update({"flagged": True}).eq("id", attempt_id).execute()
    return {"flagged": True}
