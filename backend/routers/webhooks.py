"""
Paystack webhook handler.

Always returns HTTP 200 — even on handler errors — so Paystack doesn't retry.
Signature is verified before any processing.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Request, Response

from db.client import get_supabase
from services.paystack import verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _update_subscription_from_event(event: str, data: dict[str, Any]) -> None:
    """Dispatch webhook event to the appropriate handler."""
    handlers = {
        "charge.success": _handle_charge_success,
        "subscription.create": _handle_subscription_create,
        "subscription.disable": _handle_subscription_disable,
        "subscription.not_renew": _handle_subscription_not_renew,
        "invoice.payment_failed": _handle_invoice_failed,
        "subscription.expiring_cards": _handle_expiring_cards,
    }
    handler = handlers.get(event)
    if handler:
        handler(data)
    else:
        logger.debug("Unhandled webhook event: %s", event)


def _find_sub_by_customer(customer_code: str) -> dict | None:
    supabase = get_supabase()
    result = (
        supabase.table("subscription")
        .select("*")
        .eq("paystack_customer_code", customer_code)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def _find_sub_by_code(subscription_code: str) -> dict | None:
    supabase = get_supabase()
    result = (
        supabase.table("subscription")
        .select("*")
        .eq("paystack_subscription_code", subscription_code)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


# ── Event handlers ─────────────────────────────────────────────────────────────

def _handle_charge_success(data: dict[str, Any]) -> None:
    """Update billing period when a recurring charge succeeds."""
    supabase = get_supabase()
    customer_code = data.get("customer", {}).get("customer_code")
    if not customer_code:
        return

    sub = _find_sub_by_customer(customer_code)
    if not sub:
        logger.warning("charge.success: no subscription for customer %s", customer_code)
        return

    # Extend period by 30 days from now
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)
    supabase.table("subscription").update({
        "status": "active",
        "period_start": now.isoformat(),
        "period_end": period_end.isoformat(),
    }).eq("id", sub["id"]).execute()

    # Ensure student tier is correct
    supabase.table("student").update(
        {"subscription_tier": sub["tier"]}
    ).eq("id", sub["student_id"]).execute()

    logger.info("charge.success: renewed sub %s for student %s", sub["id"], sub["student_id"])


def _handle_subscription_create(data: dict[str, Any]) -> None:
    """Store subscription_code and email_token when Paystack creates a subscription."""
    supabase = get_supabase()
    customer_code = data.get("customer", {}).get("customer_code")
    sub_code = data.get("subscription_code")
    email_token = data.get("email_token")
    plan_code = data.get("plan", {}).get("plan_code")

    if not customer_code or not sub_code:
        return

    sub = _find_sub_by_customer(customer_code)
    if not sub:
        logger.warning("subscription.create: no local sub for customer %s", customer_code)
        return

    supabase.table("subscription").update({
        "paystack_subscription_code": sub_code,
        "paystack_email_token": email_token,
        "paystack_plan_code": plan_code,
    }).eq("id", sub["id"]).execute()

    logger.info("subscription.create: stored codes for sub %s", sub["id"])


def _handle_subscription_disable(data: dict[str, Any]) -> None:
    """Mark subscription as cancelled when disabled on Paystack."""
    supabase = get_supabase()
    sub_code = data.get("subscription_code")
    if not sub_code:
        return

    sub = _find_sub_by_code(sub_code)
    if not sub:
        return

    supabase.table("subscription").update(
        {"status": "cancelled"}
    ).eq("id", sub["id"]).execute()

    logger.info("subscription.disable: marked cancelled %s", sub["id"])


def _handle_subscription_not_renew(data: dict[str, Any]) -> None:
    """Mark subscription as cancelled (won't renew next cycle)."""
    _handle_subscription_disable(data)


def _handle_invoice_failed(data: dict[str, Any]) -> None:
    """Mark subscription as past_due on payment failure."""
    supabase = get_supabase()
    sub_code = data.get("subscription", {}).get("subscription_code")
    customer_code = data.get("customer", {}).get("customer_code")

    sub = None
    if sub_code:
        sub = _find_sub_by_code(sub_code)
    if not sub and customer_code:
        sub = _find_sub_by_customer(customer_code)
    if not sub:
        return

    supabase.table("subscription").update(
        {"status": "past_due"}
    ).eq("id", sub["id"]).execute()

    logger.info("invoice.payment_failed: marked past_due %s", sub["id"])


def _handle_expiring_cards(data: dict[str, Any]) -> None:
    """Log expiring card notification — no action needed, Paystack handles retry."""
    customer_code = data.get("customer", {}).get("customer_code")
    logger.info("subscription.expiring_cards for customer %s", customer_code)


# ── Webhook endpoint ───────────────────────────────────────────────────────────

@router.post("/webhooks/paystack")
async def paystack_webhook(request: Request) -> Response:
    """
    Receive and process Paystack webhook events.
    Verifies HMAC-SHA512 signature before dispatching.
    Always returns 200 to acknowledge receipt.
    """
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not verify_webhook_signature(body, signature):
        logger.warning("Invalid Paystack webhook signature")
        return Response(status_code=401)

    try:
        import json
        payload = json.loads(body)
        event = payload.get("event", "")
        data = payload.get("data", {})
        logger.info("Paystack webhook received: %s", event)
        _update_subscription_from_event(event, data)
    except Exception:
        logger.exception("Error processing webhook — returning 200 to prevent retry")

    # Always 200
    return Response(status_code=200)
