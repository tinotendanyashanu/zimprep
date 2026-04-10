"""
Employee management routes — invite, list, update, and deactivate employees.
All routes require the caller to be an authenticated admin employee.
"""
from __future__ import annotations

import logging
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
    Create a new employee record. The invited person must sign up with the
    same email address — their user_id will be linked on first login.
    """
    if payload.role not in ("admin", "employee"):
        raise HTTPException(status_code=422, detail="Invalid role")

    sb = get_supabase()

    # Check for duplicate
    existing = (
        sb.table("employee").select("id").eq("email", payload.email).execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Employee already exists")

    employee_id = str(uuid.uuid4())
    new_emp = {
        "id": employee_id,
        "email": payload.email,
        "name": payload.name,
        "role": payload.role,
        "is_active": True,
        "invited_by": current.get("id"),
    }
    resp = sb.table("employee").insert(new_emp).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create employee")
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
