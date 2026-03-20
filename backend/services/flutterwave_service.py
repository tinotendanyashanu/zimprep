"""
Flutterwave payment service.
Docs: https://developer.flutterwave.com/reference
"""
import hmac
import hashlib
import httpx
from core.config import settings

FLW_BASE = "https://api.flutterwave.com/v3"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.flutterwave_secret_key}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Payment initialisation
# ---------------------------------------------------------------------------

async def initialize_payment(
    email: str,
    amount_usd: float,
    plan_id: int,
    redirect_url: str,
    tx_ref: str,
    customer_name: str = "",
    meta: dict | None = None,
) -> str:
    """
    Create a hosted-payment session for a subscription plan.
    Returns the payment link URL to redirect the user to.
    """
    payload = {
        "tx_ref": tx_ref,
        "amount": amount_usd,
        "currency": "USD",
        "redirect_url": redirect_url,
        "payment_plan": plan_id,
        "customer": {"email": email, "name": customer_name},
        "meta": meta or {},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FLW_BASE}/payments",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
    return data["data"]["link"]


# ---------------------------------------------------------------------------
# Subscription management
# ---------------------------------------------------------------------------

async def list_subscriptions(email: str) -> list[dict]:
    """Return active Flutterwave subscriptions for a given email."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FLW_BASE}/subscriptions",
            params={"email": email},
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def cancel_subscription(flw_subscription_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{FLW_BASE}/subscriptions/{flw_subscription_id}/cancel",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def verify_transaction(transaction_id: str) -> dict:
    """Verify a completed transaction by its Flutterwave transaction ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FLW_BASE}/transactions/{transaction_id}/verify",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()["data"]


# ---------------------------------------------------------------------------
# Webhook verification
# ---------------------------------------------------------------------------

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Flutterwave uses a simple shared secret — the raw value of the
    'verif-hash' header must equal settings.billing_webhook_secret.
    """
    return hmac.compare_digest(signature, settings.billing_webhook_secret)
