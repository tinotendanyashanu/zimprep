from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from db.client import get_supabase
from services import email as email_service

router = APIRouter()

PHONE_NUMBER_PATTERN = re.compile(r"^\+?[0-9()\-\s]{7,20}$")


class JoinWaitlistRequest(BaseModel):
    email: EmailStr
    phone_number: str
    source_page: str = "/"

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        phone_number = value.strip()
        if not PHONE_NUMBER_PATTERN.fullmatch(phone_number):
            raise ValueError("Enter a valid phone number")
        return phone_number

    @field_validator("source_page")
    @classmethod
    def normalize_source_page(cls, value: str) -> str:
        source_page = value.strip() or "/"
        return source_page[:255]


@router.post("/waitlist")
def join_waitlist(body: JoinWaitlistRequest) -> dict[str, Any]:
    supabase = get_supabase()

    existing = (
        supabase.table("waitlist_entry")
        .select("id")
        .eq("email", body.email)
        .maybe_single()
        .execute()
    )

    payload = {
        "email": body.email,
        "phone_number": body.phone_number,
        "source_page": body.source_page,
    }

    try:
        if existing and existing.data:
            result = (
                supabase.table("waitlist_entry")
                .update(payload)
                .eq("id", existing.data["id"])
                .execute()
            )
            email_service.send_waitlist_notification(
                email=body.email,
                phone_number=body.phone_number,
                source_page=body.source_page,
                already_joined=True,
            )
            return {
                "success": True,
                "already_joined": True,
                "entry": (result.data or [payload])[0],
            }

        result = supabase.table("waitlist_entry").insert(payload).execute()
        email_service.send_waitlist_notification(
            email=body.email,
            phone_number=body.phone_number,
            source_page=body.source_page,
            already_joined=False,
        )
        return {
            "success": True,
            "already_joined": False,
            "entry": (result.data or [payload])[0],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not save waitlist details",
        ) from exc
