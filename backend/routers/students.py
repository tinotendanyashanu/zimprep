"""
Student routes — dashboard, coverage, sessions, streak.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header

from db.client import get_supabase
from services import dashboard as svc

router = APIRouter()


def _verify_student(student_id: str, authorization: Optional[str]) -> None:
    """Verify the bearer token belongs to this student_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    supabase = get_supabase()
    user = supabase.auth.get_user(token)
    if not user or not user.user or user.user.id != student_id:
        raise HTTPException(status_code=403, detail="Forbidden")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/{student_id}/dashboard")
def get_dashboard(
    student_id: str,
    subject_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Full dashboard data: readiness index, streak, coverage, weak topics, recent sessions."""
    _verify_student(student_id, authorization)
    return svc.get_dashboard_data(student_id, subject_id)


@router.get("/{student_id}/subjects")
def get_subjects(
    student_id: str,
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    """Distinct subjects the student has attempted sessions for."""
    _verify_student(student_id, authorization)
    return svc.get_student_subjects(student_id)


@router.get("/{student_id}/coverage/{subject_id}")
def get_coverage(
    student_id: str,
    subject_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Detailed syllabus coverage: covered and uncovered topic lists."""
    _verify_student(student_id, authorization)
    return svc.get_syllabus_coverage(student_id, subject_id)


@router.get("/{student_id}/sessions")
def get_sessions(
    student_id: str,
    limit: int = 10,
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    """Recent session history with scores."""
    _verify_student(student_id, authorization)
    return svc.get_recent_sessions(student_id, limit)


@router.get("/{student_id}/streak")
def get_streak(
    student_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, int]:
    """Current and longest study streak."""
    _verify_student(student_id, authorization)
    return svc.get_streak(student_id)
