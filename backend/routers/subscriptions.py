"""
Subscription routes — manage student subscriptions and Paystack checkout.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.client import get_supabase
from db.models_subscription import (
    TIER_CONFIG,
    PAID_TIERS,
    validate_subject_count,
    InitializeCheckoutRequest,
    VerifyPaymentRequest,
    CancelSubscriptionRequest,
)
from services import paystack as ps
from services.quota import get_quota_status

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_plan_code(tier: str) -> str:
    """Retrieve stored Paystack plan code from DB config table, or raise."""
    supabase = get_supabase()
    result = (
        supabase.table("paystack_plan")
        .select("plan_code")
        .eq("tier", tier)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(
            status_code=500,
            detail=f"No Paystack plan configured for tier '{tier}'. "
                   "Run POST /admin/paystack/create-plans first.",
        )
    return result.data["plan_code"]


def _get_student_email(student_id: str) -> str:
    supabase = get_supabase()
    result = (
        supabase.table("student")
        .select("email")
        .eq("id", student_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Student not found")
    return result.data["email"]


def _active_subscription(student_id: str) -> Optional[dict]:
    supabase = get_supabase()
    result = (
        supabase.table("subscription")
        .select("*")
        .eq("student_id", student_id)
        .execute()
    )
    rows = result.data or []
    for row in rows:
        if row["status"] in ("active", "cancelled", "past_due"):
            return row
    return None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/subscriptions/status/{student_id}")
def get_subscription_status(student_id: str) -> dict[str, Any]:
    """
    Return the student's current tier, subscription details, and quota usage.
    Used by the frontend to render QuotaBar and gate features.
    """
    supabase = get_supabase()

    # Get tier
    student_result = (
        supabase.table("student")
        .select("subscription_tier")
        .eq("id", student_id)
        .maybe_single()
        .execute()
    )
    if not student_result or not student_result.data:
        raise HTTPException(status_code=404, detail="Student not found")
    tier = student_result.data.get("subscription_tier", "starter")

    # Get subscription row
    sub = _active_subscription(student_id)

    # Get quota
    quota = get_quota_status(student_id)

    return {
        "tier": tier,
        "subscription": sub,
        "quota": quota.model_dump(),
    }


@router.post("/subscriptions/initialize")
def initialize_checkout(body: InitializeCheckoutRequest) -> dict[str, Any]:
    """
    Initialize a Paystack checkout session for a paid tier.
    Returns an authorization_url to redirect the student to.
    """
    if body.tier not in PAID_TIERS:
        raise HTTPException(status_code=400, detail=f"'{body.tier}' is not a paid tier")

    try:
        validate_subject_count(body.tier, body.subject_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Block if student already has an active subscription
    existing = _active_subscription(body.student_id)
    if existing and existing["status"] == "active":
        raise HTTPException(
            status_code=409,
            detail="Student already has an active subscription. Cancel first to change plans.",
        )

    tier_conf = TIER_CONFIG[body.tier]
    amount_usd = tier_conf["price_usd"]

    # Get Paystack plan code
    try:
        plan_code = _get_plan_code(body.tier)
    except HTTPException:
        plan_code = None  # Fall back to one-time charge if no plan configured

    reference = str(uuid.uuid4()).replace("-", "")

    try:
        result = ps.initialize_transaction(
            email=body.email,
            amount_usd=amount_usd,
            reference=reference,
            callback_url=body.callback_url,
            plan_code=plan_code,
            metadata={
                "student_id": body.student_id,
                "tier": body.tier,
                "subject_ids": body.subject_ids,
            },
        )
    except Exception as exc:
        logger.exception("Paystack initialize failed")
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {exc}")

    return {
        "authorization_url": result.get("authorization_url"),
        "reference": result.get("reference"),
        "access_code": result.get("access_code"),
    }


@router.post("/subscriptions/verify")
def verify_payment(body: VerifyPaymentRequest) -> dict[str, Any]:
    """
    Verify a completed Paystack payment and activate the subscription.
    Called from the /subscription/callback page after redirect.
    Idempotent — safe to call multiple times for the same reference.
    """
    supabase = get_supabase()

    try:
        tx = ps.verify_transaction(body.reference)
    except Exception as exc:
        logger.exception("Paystack verify failed")
        raise HTTPException(status_code=502, detail=f"Payment gateway error: {exc}")

    if tx.get("status") != "success":
        raise HTTPException(status_code=402, detail="Payment was not successful")

    metadata = tx.get("metadata") or {}
    student_id = metadata.get("student_id") or body.student_id
    tier = metadata.get("tier", "standard")
    subject_ids = metadata.get("subject_ids", [])

    # Idempotency: if we already have an active sub for this reference, return it
    existing = _active_subscription(student_id)
    if existing and existing["status"] == "active":
        return {"status": "already_active", "tier": tier, "subscription": existing}

    tier_conf = TIER_CONFIG.get(tier, TIER_CONFIG["standard"])
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)

    # Create subscription record
    sub_id = str(uuid.uuid4())
    sub_data = {
        "id": sub_id,
        "student_id": student_id,
        "tier": tier,
        "status": "active",
        "subject_ids": subject_ids,
        "amount_usd": tier_conf["price_usd"],
        "period_start": now.isoformat(),
        "period_end": period_end.isoformat(),
        "paystack_customer_code": tx.get("customer", {}).get("customer_code"),
    }

    # Upsert subscription (on conflict on student_id, update)
    supabase.table("subscription").upsert(
        sub_data, on_conflict="student_id"
    ).execute()

    # Upgrade student tier
    supabase.table("student").update(
        {"subscription_tier": tier}
    ).eq("id", student_id).execute()

    logger.info("Subscription activated: student=%s tier=%s", student_id, tier)
    return {"status": "activated", "tier": tier, "subscription": sub_data}


@router.delete("/subscriptions/{student_id}")
def cancel_subscription(student_id: str) -> dict[str, Any]:
    """
    Cancel a student's subscription. Access remains until period_end.
    """
    supabase = get_supabase()

    sub = _active_subscription(student_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # Attempt to disable on Paystack if we have a subscription code
    sub_code = sub.get("paystack_subscription_code")
    email_token = sub.get("paystack_email_token")
    if sub_code and email_token:
        try:
            ps.disable_subscription(sub_code, email_token)
        except Exception:
            logger.warning("Failed to disable Paystack subscription %s", sub_code)
            # Continue anyway — we still mark cancelled locally

    supabase.table("subscription").update(
        {"status": "cancelled"}
    ).eq("student_id", student_id).execute()

    logger.info("Subscription cancelled: student=%s", student_id)
    return {"status": "cancelled", "access_until": sub["period_end"]}
