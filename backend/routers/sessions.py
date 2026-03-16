"""
Session routes — manage exam and practice sessions.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from db.client import get_supabase
from services.marking import mark_session
from services.quota import check_exam_quota

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request schemas ────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    student_id: str
    paper_id: str
    mode: str  # 'exam' | 'practice'


class SaveAnswersRequest(BaseModel):
    answers: dict[str, str]  # {question_id: answer_text}


class PracticeSessionRequest(BaseModel):
    student_id: str
    subject_id: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/practice")
def get_or_create_practice_session(body: PracticeSessionRequest) -> dict[str, Any]:
    """Get existing or create a new long-lived practice session for a student+subject pair."""
    supabase = get_supabase()

    # Look for an existing active practice session linked to this subject
    existing = (
        supabase.table("session")
        .select("id, paper_id")
        .eq("student_id", body.student_id)
        .eq("mode", "practice")
        .eq("status", "active")
        .execute()
    )
    for session in (existing.data or []):
        paper = (
            supabase.table("paper")
            .select("subject_id")
            .eq("id", session["paper_id"])
            .single()
            .execute()
        )
        if paper.data and paper.data["subject_id"] == body.subject_id:
            return {"session_id": session["id"]}

    # No existing session — pick a ready paper for the subject
    paper_result = (
        supabase.table("paper")
        .select("id")
        .eq("subject_id", body.subject_id)
        .eq("status", "ready")
        .limit(1)
        .execute()
    )
    if not paper_result.data:
        raise HTTPException(status_code=404, detail="No ready papers for this subject")

    session_id = str(uuid.uuid4())
    supabase.table("session").insert(
        {
            "id": session_id,
            "student_id": body.student_id,
            "paper_id": paper_result.data[0]["id"],
            "mode": "practice",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
    ).execute()
    return {"session_id": session_id}


@router.post("/")
def create_session(body: CreateSessionRequest) -> dict[str, Any]:
    """Create a new exam or practice session."""
    if body.mode not in ("exam", "practice"):
        raise HTTPException(status_code=422, detail="mode must be 'exam' or 'practice'")

    # Exam mode is gated behind paid tiers
    if body.mode == "exam":
        quota = check_exam_quota(body.student_id)
        if not quota.allowed:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "tier_required",
                    "tier": quota.tier,
                    "feature": "exam",
                    "message": "Exam Mode requires a paid subscription. Upgrade to access full past papers.",
                },
            )

    supabase = get_supabase()
    session_id = str(uuid.uuid4())
    supabase.table("session").insert(
        {
            "id": session_id,
            "student_id": body.student_id,
            "paper_id": body.paper_id,
            "mode": body.mode,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
    ).execute()
    return {"session_id": session_id}


@router.get("/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve a session with paper and subject details."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("*, paper!inner(id, year, paper_number, subject!inner(id, name, level))")
        .eq("id", session_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return result.data


@router.patch("/{session_id}/autosave")
def autosave_session(session_id: str, body: SaveAnswersRequest) -> dict[str, Any]:
    """Save draft answers without changing session status or triggering marking."""
    supabase = get_supabase()

    session = supabase.table("session").select("id").eq("id", session_id).single().execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    for question_id, answer_text in body.answers.items():
        supabase.table("attempt").upsert(
            {
                "session_id": session_id,
                "question_id": question_id,
                "student_answer": answer_text,
            },
            on_conflict="session_id,question_id",
        ).execute()

    return {"saved": True}


@router.patch("/{session_id}/submit")
def submit_session(
    session_id: str,
    body: SaveAnswersRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Submit exam: persist all answers, mark session submitted, trigger background marking."""
    supabase = get_supabase()

    session_row = (
        supabase.table("session")
        .select("id, status")
        .eq("id", session_id)
        .single()
        .execute()
    )
    if not session_row.data:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_row.data["status"] != "active":
        raise HTTPException(status_code=409, detail="Session already submitted")

    # Persist final answers
    for question_id, answer_text in body.answers.items():
        supabase.table("attempt").upsert(
            {
                "session_id": session_id,
                "question_id": question_id,
                "student_answer": answer_text,
            },
            on_conflict="session_id,question_id",
        ).execute()

    # Mark session as submitted
    supabase.table("session").update(
        {
            "status": "submitted",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", session_id).execute()

    background_tasks.add_task(mark_session, session_id)
    return {"status": "submitted", "session_id": session_id}


@router.get("/{session_id}/results")
def get_results(session_id: str) -> dict[str, Any]:
    """Poll marking progress. Returns all attempts with marking fields and aggregate stats."""
    supabase = get_supabase()

    attempts_result = (
        supabase.table("attempt")
        .select(
            "id, question_id, student_answer, ai_score, ai_feedback, "
            "ai_references, marked_at, flagged"
        )
        .eq("session_id", session_id)
        .execute()
    )
    attempts = attempts_result.data or []
    total = len(attempts)
    marked = sum(1 for a in attempts if a.get("marked_at") is not None)
    total_score = sum(
        (a.get("ai_score") or 0) for a in attempts if a.get("marked_at") is not None
    )

    return {
        "all_marked": total > 0 and marked == total,
        "marked_count": marked,
        "total_count": total,
        "total_score": total_score,
        "attempts": attempts,
    }
