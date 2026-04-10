"""
Employee management routes — invite, list, update, and deactivate employees.
All routes require the caller to be an authenticated admin employee.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Auth dependency ──────────────────────────────────────────────────────────


def get_current_employee(authorization: str = Header(...)):
    """
    Validate the Supabase JWT and confirm the caller is an active employee.

    On first login the employee record has user_id=null (invited but not yet
    signed up). We look up by email as a fallback and link the user_id.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[len("Bearer "):]
    sb = get_supabase()
    try:
        result = sb.auth.get_user(token)
        user = result.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Primary lookup: by user_id (fast path after first login)
    resp = (
        sb.table("employee")
        .select("id, role, is_active, user_id")
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )
    emp = resp.data

    if not emp:
        # Fallback: look up by email (invited but not yet linked)
        email_resp = (
            sb.table("employee")
            .select("id, role, is_active, user_id")
            .eq("email", user.email)
            .maybe_single()
            .execute()
        )
        emp = email_resp.data
        if emp and emp.get("user_id") is None:
            # Link user_id now
            sb.table("employee").update({"user_id": user.id}).eq("id", emp["id"]).execute()
            emp["user_id"] = user.id

    if not emp or not emp.get("is_active"):
        raise HTTPException(status_code=403, detail="Not an active employee")
    return {"user_id": user.id, **emp}


def require_admin(current: dict = Depends(get_current_employee)):
    """Restrict endpoint to admin-role employees only."""
    if current.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current


# ── Request / Response schemas ───────────────────────────────────────────────


class InviteEmployeeRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "employee"  # 'admin' | 'employee'


class UpdateEmployeeRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None


class EmployeeOut(BaseModel):
    id: str
    user_id: Optional[str]
    email: str
    name: str
    role: str
    is_active: bool
    invited_by: Optional[str]
    created_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/me", response_model=EmployeeOut)
def get_me(current: dict = Depends(get_current_employee)):
    """Return the current employee's profile."""
    sb = get_supabase()
    resp = (
        sb.table("employee")
        .select("*")
        .eq("id", current["id"])
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Not found")
    return resp.data


@router.get("/", response_model=list[EmployeeOut])
def list_employees(_current: dict = Depends(get_current_employee)):
    """List all employees (any authenticated employee can view)."""
    sb = get_supabase()
    resp = (
        sb.table("employee")
        .select("*")
        .order("created_at", desc=False)
        .execute()
    )
    return resp.data or []


@router.post("/invite", response_model=EmployeeOut, status_code=201)
def invite_employee(
    payload: InviteEmployeeRequest,
    current: dict = Depends(require_admin),
):
    """
    Invite a new employee.
    1. Creates the employee record in the employee table.
    2. Sends a Supabase invitation email via auth.admin.invite_user_by_email.
       The invited person clicks the link, sets a password, and their
       user_id is automatically linked on first /admin/employees/me call.
    """
    if payload.role not in ("admin", "employee"):
        raise HTTPException(status_code=422, detail="Invalid role")

    sb = get_supabase()

    # Check for duplicate employee record
    existing = (
        sb.table("employee").select("id").eq("email", payload.email).execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Employee already exists")

    # Send Supabase invitation email — this creates the auth.users record
    # and emails a magic link so the person can set their password.
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    redirect_to = f"{frontend_url}/auth/callback?next=/reset-password"

    try:
        invite_resp = sb.auth.admin.invite_user_by_email(
            payload.email,
            options={
                "data": {"name": payload.name, "employee_role": payload.role},
                "redirect_to": redirect_to,
            },
        )
        auth_user_id = invite_resp.user.id if invite_resp.user else None
    except Exception as exc:
        logger.error("Supabase invite failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to send invitation email: {exc}")

    # Create the employee record, linking user_id immediately since Supabase
    # already created the auth user.
    employee_id = str(uuid.uuid4())
    new_emp = {
        "id": employee_id,
        "user_id": auth_user_id,
        "email": payload.email,
        "name": payload.name,
        "role": payload.role,
        "is_active": True,
        "invited_by": current.get("id"),
    }
    resp = sb.table("employee").insert(new_emp).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create employee record")
    return resp.data[0]


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: str,
    payload: UpdateEmployeeRequest,
    _current: dict = Depends(require_admin),
):
    """Update an employee's role, status, or name (admin only)."""
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")
    if "role" in updates and updates["role"] not in ("admin", "employee"):
        raise HTTPException(status_code=422, detail="Invalid role")

    sb = get_supabase()
    resp = (
        sb.table("employee")
        .update(updates)
        .eq("id", employee_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return resp.data[0]


@router.delete("/{employee_id}", status_code=204)
def deactivate_employee(
    employee_id: str,
    current: dict = Depends(require_admin),
):
    """Deactivate an employee (soft delete — sets is_active=false)."""
    if current.get("id") == employee_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    sb = get_supabase()
    sb.table("employee").update({"is_active": False}).eq("id", employee_id).execute()


@router.post("/{employee_id}/reset-password", status_code=200)
def reset_employee_password(
    employee_id: str,
    _current: dict = Depends(require_admin),
):
    """Send a password-reset email to the employee (admin only)."""
    import httpx

    sb = get_supabase()
    emp = sb.table("employee").select("email, user_id").eq("id", employee_id).maybe_single().execute()
    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not emp.data.get("user_id"):
        raise HTTPException(status_code=400, detail="Employee has not signed up yet — resend the invite instead")

    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    redirect_to = f"{frontend_url}/auth/callback?next=/reset-password"

    try:
        r = httpx.post(
            f"{supabase_url}/auth/v1/recover",
            headers={"apikey": supabase_key, "Content-Type": "application/json"},
            json={"email": emp.data["email"]},
            params={"redirect_to": redirect_to},
            timeout=10,
        )
        if r.status_code not in (200, 204):
            raise HTTPException(status_code=500, detail="Failed to send reset email")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Password reset failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return {"sent": True, "email": emp.data["email"]}


@router.delete("/{employee_id}/permanent", status_code=204)
def delete_employee_permanently(
    employee_id: str,
    current: dict = Depends(require_admin),
):
    """Permanently remove an employee record (irreversible)."""
    if current.get("id") == employee_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    sb = get_supabase()
    result = sb.table("employee").delete().eq("id", employee_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Employee not found")
