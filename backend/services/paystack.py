"""
Paystack API client.
Wraps the Paystack REST API for plan creation, checkout initialization,
payment verification, and subscription management.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import httpx

PAYSTACK_BASE = "https://api.paystack.co"


def _headers() -> dict[str, str]:
    key = os.environ.get("PAYSTACK_SECRET_KEY", "")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _get(path: str) -> dict[str, Any]:
    resp = httpx.get(f"{PAYSTACK_BASE}{path}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{PAYSTACK_BASE}{path}",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Plans ──────────────────────────────────────────────────────────────────────

def create_plan(name: str, amount_usd: float, interval: str = "monthly") -> dict[str, Any]:
    """Create a recurring Paystack plan. amount_usd is converted to kobo (USD cents × 100)."""
    # Paystack amounts are in the smallest currency unit.
    # USD: amount in cents, so $5.00 = 500.
    amount_kobo = int(amount_usd * 100)
    data = _post("/plan", {
        "name": name,
        "interval": interval,
        "amount": amount_kobo,
        "currency": "USD",
    })
    return data.get("data", {})


def list_plans() -> list[dict[str, Any]]:
    data = _get("/plan")
    return data.get("data", [])


# ── Transactions / Checkout ────────────────────────────────────────────────────

def initialize_transaction(
    email: str,
    amount_usd: float,
    reference: str,
    callback_url: str,
    metadata: dict[str, Any] | None = None,
    plan_code: str | None = None,
) -> dict[str, Any]:
    """
    Initialize a Paystack transaction (checkout).
    Returns {authorization_url, access_code, reference}.
    """
    amount_kobo = int(amount_usd * 100)
    payload: dict[str, Any] = {
        "email": email,
        "amount": amount_kobo,
        "currency": "USD",
        "reference": reference,
        "callback_url": callback_url,
    }
    if metadata:
        payload["metadata"] = metadata
    if plan_code:
        payload["plan"] = plan_code

    data = _post("/transaction/initialize", payload)
    return data.get("data", {})


def verify_transaction(reference: str) -> dict[str, Any]:
    """Verify a transaction by reference. Returns the full transaction data."""
    data = _get(f"/transaction/verify/{reference}")
    return data.get("data", {})


# ── Subscription management ────────────────────────────────────────────────────

def disable_subscription(subscription_code: str, email_token: str) -> dict[str, Any]:
    """Cancel (disable) a Paystack subscription."""
    data = _post("/subscription/disable", {
        "code": subscription_code,
        "token": email_token,
    })
    return data.get("data", {})


def get_subscription(subscription_code: str) -> dict[str, Any]:
    data = _get(f"/subscription/{subscription_code}")
    return data.get("data", {})


# ── Webhook signature verification ────────────────────────────────────────────

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Validate the X-Paystack-Signature header.
    Paystack signs the raw request body with HMAC-SHA512 using the webhook secret.
    """
    secret = os.environ.get("PAYSTACK_WEBHOOK_SECRET", "")
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
