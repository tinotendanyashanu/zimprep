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
        .single()
        .execute()
    )
    if not result.data:
        return "starter"
    return result.data.get("subscription_tier", "starter")


def _get_student_id_from_session(session_id: str) -> str | None:
    """Look up the student_id owning a session."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("student_id")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return result.data["student_id"] if result.data else None


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
    """
    Check whether a student can submit another practice answer.

    - MCQ questions are always allowed (cost zero AI calls).
    - Starter tier: max DAILY_FREE_LIMIT written submissions per day.
    - Paid tiers: unlimited.
    """
    # MCQ never counts against quota
    if question_type == "mcq":
        return QuotaStatus(
            tier="starter",
            allowed=True,
            used=0,
            limit=None,
            feature="practice",
        )

    student_id = _get_student_id_from_session(session_id)
    if not student_id:
        # Can't find session — let the route handler deal with it
        return QuotaStatus(tier="starter", allowed=True, used=0, limit=None, feature="practice")

    tier = _get_student_tier(student_id)

    if tier in PAID_TIERS:
        return QuotaStatus(tier=tier, allowed=True, used=0, limit=None, feature="practice")

    # Starter tier: count today's submissions
    used = _count_submissions_today(student_id)
    limit = tier_daily_limit(tier) or DAILY_FREE_LIMIT
    allowed = used < limit

    return QuotaStatus(
        tier=tier,
        allowed=allowed,
        used=used,
        limit=limit,
        feature="practice",
    )


def check_exam_quota(student_id: str) -> QuotaStatus:
    """
    Check whether a student can start an exam session.
    Starter tier does not have exam mode access.
    """
    tier = _get_student_tier(student_id)
    allowed = tier_allows_exam(tier)
    return QuotaStatus(
        tier=tier,
        allowed=allowed,
        used=0,
        limit=None,
        feature="exam",
    )


def get_quota_status(student_id: str) -> QuotaStatus:
    """
    Return the current quota status for the dashboard / QuotaBar.
    Shows daily usage for starter tier; unlimited for paid tiers.
    """
    tier = _get_student_tier(student_id)
    if tier in PAID_TIERS:
        return QuotaStatus(tier=tier, allowed=True, used=0, limit=None, feature="practice")

    used = _count_submissions_today(student_id)
    limit = DAILY_FREE_LIMIT
    return QuotaStatus(
        tier=tier,
        allowed=used < limit,
        used=used,
        limit=limit,
        feature="practice",
    )
