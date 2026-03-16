"""
Parent routes — list children, link child by email, read-only child progress.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from db.client import get_supabase
from services import dashboard as svc

router = APIRouter()


class LinkChildRequest(BaseModel):
    child_email: str


def _verify_parent(parent_id: str, authorization: Optional[str]) -> None:
    """Verify the bearer token belongs to this parent_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    supabase = get_supabase()
    user = supabase.auth.get_user(token)
    if not user or not user.user or user.user.id != parent_id:
        raise HTTPException(status_code=403, detail="Forbidden")


# ── Endpoints ──────────────────────────────────────────────────────────────────

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

    # Find student by email
    student_result = (
        supabase.table("student")
        .select("id, name, email")
        .eq("email", body.child_email)
        .single()
        .execute()
    )
    if not student_result.data:
        raise HTTPException(status_code=404, detail="No student found with that email")

    student = student_result.data

    # Set parent_id on the student record
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
    supabase = get_supabase()

    # Verify this student is actually linked to this parent
    student_result = (
        supabase.table("student")
        .select("id, parent_id")
        .eq("id", student_id)
        .single()
        .execute()
    )
    if not student_result.data or student_result.data.get("parent_id") != parent_id:
        raise HTTPException(status_code=403, detail="This student is not linked to your account")

    return svc.get_dashboard_data(student_id, subject_id)
