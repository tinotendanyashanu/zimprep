"""
Parent routes — list children, link child by email, read-only child progress,
family dashboard, weekly report, goals, and alerts.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from db.client import get_supabase
from services import dashboard as svc
from services import parent_service
from services import notification_service

router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────────

class LinkChildRequest(BaseModel):
    child_email: str


class GoalsRequest(BaseModel):
    weekly_hours_target: float = 5.0
    target_grade_percent: int = 70


# ── Auth helper ────────────────────────────────────────────────────────────────

def _verify_parent(parent_id: str, authorization: Optional[str]) -> None:
    """Verify the bearer token belongs to this parent_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    supabase = get_supabase()
    user = supabase.auth.get_user(token)
    if not user or not user.user or user.user.id != parent_id:
        raise HTTPException(status_code=403, detail="Forbidden")


def _verify_child_belongs_to_parent(parent_id: str, student_id: str) -> None:
    """Raise 403 if the student is not linked to this parent."""
    supabase = get_supabase()
    result = (
        supabase.table("student")
        .select("id, parent_id")
        .eq("id", student_id)
        .maybe_single()
        .execute()
    )
    if (
        not result
        or not result.data
        or result.data.get("parent_id") != parent_id
    ):
        raise HTTPException(status_code=403, detail="This student is not linked to your account")


# ── Existing endpoints (unchanged) ────────────────────────────────────────────

@router.get("/{parent_id}/children")
def list_children(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    """List all students linked to this parent."""
    _verify_parent(parent_id, authorization)
    supabase = get_supabase()
    result = (
        supabase.table("student")
        .select("id, name, email, level, created_at")
        .eq("parent_id", parent_id)
        .execute()
    )
    return result.data or []


@router.post("/{parent_id}/children/link")
def link_child(
    parent_id: str,
    body: LinkChildRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Link a child to this parent account by the child's email address."""
    _verify_parent(parent_id, authorization)
    supabase = get_supabase()

    student_result = (
        supabase.table("student")
        .select("id, name, email")
        .eq("email", body.child_email)
        .maybe_single()
        .execute()
    )
    if not student_result or not student_result.data:
        raise HTTPException(status_code=404, detail="No student found with that email")

    student = student_result.data
    supabase.table("student").update({"parent_id": parent_id}).eq("id", student["id"]).execute()

    return {"success": True, "student_id": student["id"], "name": student["name"]}


@router.get("/{parent_id}/children/{student_id}/progress")
def get_child_progress(
    parent_id: str,
    student_id: str,
    subject_id: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Read-only dashboard data for a linked child."""
    _verify_parent(parent_id, authorization)
    _verify_child_belongs_to_parent(parent_id, student_id)
    return svc.get_dashboard_data(student_id, subject_id)


# ── New: Family Dashboard ──────────────────────────────────────────────────────

@router.get("/{parent_id}/family-dashboard")
def get_family_dashboard(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """
    Aggregated family overview: summary stats + per-child cards.
    Each child card includes status (Improving / Stable / At Risk),
    weekly study hours, avg score, strong & weak subjects.
    """
    _verify_parent(parent_id, authorization)
    return parent_service.get_parent_dashboard(parent_id)


# ── New: Weekly Report ─────────────────────────────────────────────────────────

@router.post("/{parent_id}/report/generate")
def generate_report(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Generate (or regenerate) the weekly family report now."""
    _verify_parent(parent_id, authorization)
    return parent_service.generate_weekly_family_report(parent_id)


@router.get("/{parent_id}/report")
def get_report(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Return the latest stored weekly family report, or generate one if none exists."""
    _verify_parent(parent_id, authorization)
    report = parent_service.get_latest_report(parent_id)
    if report is None:
        report = parent_service.generate_weekly_family_report(parent_id)
    return report


# ── New: Goals ─────────────────────────────────────────────────────────────────

@router.get("/{parent_id}/children/{student_id}/goals")
def get_child_goals(
    parent_id: str,
    student_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Return study goals set for a child (defaults if none set)."""
    _verify_parent(parent_id, authorization)
    _verify_child_belongs_to_parent(parent_id, student_id)

    supabase = get_supabase()
    result = (
        supabase.table("parent_goals")
        .select("weekly_hours_target, target_grade_percent, updated_at")
        .eq("parent_id", parent_id)
        .eq("student_id", student_id)
        .maybe_single()
        .execute()
    )
    if result and result.data:
        return result.data
    return {"weekly_hours_target": 5.0, "target_grade_percent": 70, "updated_at": None}


@router.post("/{parent_id}/children/{student_id}/goals")
def set_child_goals(
    parent_id: str,
    student_id: str,
    body: GoalsRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Create or update study goals for a child."""
    _verify_parent(parent_id, authorization)
    _verify_child_belongs_to_parent(parent_id, student_id)

    supabase = get_supabase()
    payload = {
        "parent_id": parent_id,
        "student_id": student_id,
        "weekly_hours_target": body.weekly_hours_target,
        "target_grade_percent": body.target_grade_percent,
    }
    supabase.table("parent_goals").upsert(
        payload, on_conflict="parent_id,student_id"
    ).execute()

    return {"success": True, **payload}


# ── New: Alerts ────────────────────────────────────────────────────────────────

@router.get("/{parent_id}/alerts")
def get_alerts(
    parent_id: str,
    unread_only: bool = False,
    authorization: Optional[str] = Header(default=None),
) -> list[dict[str, Any]]:
    """Return alerts for this parent (newest first)."""
    _verify_parent(parent_id, authorization)
    return notification_service.get_parent_alerts(parent_id, unread_only=unread_only)


@router.patch("/{parent_id}/alerts/{alert_id}/read")
def mark_alert_read(
    parent_id: str,
    alert_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Mark a single alert as read."""
    _verify_parent(parent_id, authorization)
    notification_service.mark_alert_read(parent_id, alert_id)
    return {"success": True}


@router.post("/{parent_id}/alerts/read-all")
def mark_all_read(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Mark all alerts as read."""
    _verify_parent(parent_id, authorization)
    notification_service.mark_all_alerts_read(parent_id)
    return {"success": True}


# ── New: Trigger alert check (can be called by scheduler) ────────────────────

@router.post("/{parent_id}/alerts/check")
def check_alerts(
    parent_id: str,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """
    Run alert checks for all children and create any new alerts.
    Returns list of newly created alerts.
    """
    _verify_parent(parent_id, authorization)
    dashboard = parent_service.get_parent_dashboard(parent_id)
    new_alerts = notification_service.check_and_create_alerts(
        parent_id, dashboard["children"]
    )
    return {"created": len(new_alerts), "alerts": new_alerts}
