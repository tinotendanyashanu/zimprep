"""
Quota enforcement logic.

Checks whether a student is allowed to submit a practice attempt or start
an exam session based on their subscription tier and daily usage.
"""
from __future__ import annotations

from db.client import get_supabase
from db.models_subscription import (
    QuotaStatus,
    DAILY_FREE_LIMIT,
    PAID_TIERS,
    tier_allows_exam,
    tier_daily_limit,
)


def _get_student_tier(student_id: str) -> str:
    """Return the student's current subscription_tier from the DB."""
    supabase = get_supabase()
    result = (
        supabase.table("student")
        .select("subscription_tier")
        .eq("id", student_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return "starter"
    return result.data.get("subscription_tier", "starter")


def _get_student_id_from_session(session_id: str) -> str | None:
    """Look up the student_id owning a session."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("student_id")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    return result.data["student_id"] if (result and result.data) else None


def _count_submissions_today(student_id: str) -> int:
    """
    Count the student's written-question submissions today (UTC).
    Uses a direct table query — MCQ answers are not counted against the quota.
    """
    supabase = get_supabase()
    # Call the DB function defined in migration 005
    result = supabase.rpc(
        "count_student_submissions_today",
        {"p_student_id": student_id},
    ).execute()
    return result.data or 0


# ── Public API ─────────────────────────────────────────────────────────────────

def check_practice_quota(session_id: str, question_type: str = "written") -> QuotaStatus:
    """Quota checks disabled — all students have unlimited access."""
    return QuotaStatus(tier="all_subjects", allowed=True, used=0, limit=None, feature="practice")


def check_exam_quota(student_id: str) -> QuotaStatus:
    """Quota checks disabled — all students have exam mode access."""
    return QuotaStatus(tier="all_subjects", allowed=True, used=0, limit=None, feature="exam")


def get_quota_status(student_id: str) -> QuotaStatus:
    """Quota checks disabled — all students have unlimited access."""
    return QuotaStatus(tier="all_subjects", allowed=True, used=0, limit=None, feature="practice")
