import json
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from supabase import create_client, Client
from core.config import settings
import services.flutterwave_service as flw

router = APIRouter(prefix="/subscription", tags=["subscription"])


# ---------------------------------------------------------------------------
# Supabase clients
# ---------------------------------------------------------------------------

def _supabase_service() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _supabase_anon() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    sb = _supabase_anon()
    resp = sb.auth.get_user(token)
    if not resp.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return {"id": str(resp.user.id), "email": resp.user.email}


# ---------------------------------------------------------------------------
# Tier → price + Flutterwave plan ID
# ---------------------------------------------------------------------------

TIER_AMOUNTS_USD: dict[str, float] = {
    "standard": 5.00,
    "bundle": 8.00,
    "all_subjects": 10.00,
}


def _get_flw_plan_id(tier: str) -> int:
    """Look up the Flutterwave payment plan ID stored in paystack_plan table (reused)."""
    sb = _supabase_service()
    row = sb.table("paystack_plan").select("plan_code").eq("tier", tier).single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail=f"No payment plan configured for tier '{tier}'")
    try:
        return int(row.data["plan_code"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail="plan_code in DB must be the integer Flutterwave plan ID")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/me")
async def get_my_subscription(user: dict = Depends(get_current_user)):
    sb = _supabase_service()
    row = (
        sb.table("subscription")
        .select("*")
        .eq("student_id", user["id"])
        .maybe_single()
        .execute()
    )
    return {"subscription": row.data}


class CheckoutRequest(BaseModel):
    tier: str          # "standard" | "bundle" | "all_subjects"
    callback_url: str
    customer_name: str = ""


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest, user: dict = Depends(get_current_user)):
    """Initialize a Flutterwave hosted payment and return the redirect URL."""
    tier = body.tier
    if tier not in TIER_AMOUNTS_USD:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {tier}")

    plan_id = _get_flw_plan_id(tier)
    amount = TIER_AMOUNTS_USD[tier]
    tx_ref = f"zimprep-{user['id'][:8]}-{uuid.uuid4().hex[:8]}"

    link = await flw.initialize_payment(
        email=user["email"],
        amount_usd=amount,
        plan_id=plan_id,
        redirect_url=body.callback_url,
        tx_ref=tx_ref,
        customer_name=body.customer_name,
        meta={"student_id": user["id"], "tier": tier},
    )
    return {"authorization_url": link, "tx_ref": tx_ref}


@router.post("/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    sb = _supabase_service()
    row = (
        sb.table("subscription")
        .select("paystack_subscription_code")  # stores Flutterwave subscription ID
        .eq("student_id", user["id"])
        .eq("status", "active")
        .maybe_single()
        .execute()
    )
    if not row.data:
        raise HTTPException(status_code=404, detail="No active subscription found")

    flw_sub_id = row.data.get("paystack_subscription_code")
    if not flw_sub_id:
        raise HTTPException(status_code=400, detail="Subscription is missing a Flutterwave ID")

    try:
        await flw.cancel_subscription(int(flw_sub_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Flutterwave error: {e}")

    sb.table("subscription").update({"status": "cancelled"}).eq("student_id", user["id"]).execute()
    return {"detail": "Subscription cancellation initiated"}


# ---------------------------------------------------------------------------
# Webhook  (POST /subscription/webhook)
# ---------------------------------------------------------------------------

@router.post("/webhook", status_code=200)
async def flutterwave_webhook(
    request: Request,
    verif_hash: str = Header(..., alias="verif-hash"),
):
    raw = await request.body()

    if not flw.verify_webhook_signature(raw, verif_hash):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = json.loads(raw)
    event_type: str = event.get("event", "")
    data: dict = event.get("data", {})

    sb = _supabase_service()

    if event_type == "subscription.activated":
        _handle_subscription_activated(sb, data)
    elif event_type in ("subscription.cancelled", "subscription.deactivated"):
        _handle_subscription_cancelled(sb, data)
    elif event_type == "charge.completed":
        _handle_charge_completed(sb, data)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Webhook handlers
# ---------------------------------------------------------------------------

def _handle_subscription_activated(sb: Client, data: dict):
    customer = data.get("customer", {})
    email = customer.get("customer_email") or customer.get("email")
    if not email:
        return

    student_id = _student_id_from_email(sb, email)
    if not student_id:
        return

    meta: dict = data.get("meta", {}) or {}
    tier = meta.get("tier", "all_subjects")
    amount = TIER_AMOUNTS_USD.get(tier, 10.00)
    now = datetime.now(timezone.utc)

    sb.table("subscription").upsert(
        {
            "student_id": student_id,
            "tier": tier,
            "status": "active",
            "paystack_customer_code": str(customer.get("id", "")),
            "paystack_subscription_code": str(data.get("id", "")),  # Flutterwave sub ID
            "paystack_plan_code": str(data.get("plan", {}).get("id", "")),
            "paystack_email_token": "",
            "amount_usd": amount,
            "period_start": now.isoformat(),
            "period_end": (now + timedelta(days=30)).isoformat(),
        },
        on_conflict="student_id",
    ).execute()

    sb.table("student").update({"subscription_tier": tier}).eq("id", student_id).execute()


def _handle_subscription_cancelled(sb: Client, data: dict):
    flw_sub_id = str(data.get("id", ""))
    if not flw_sub_id:
        return

    row = (
        sb.table("subscription")
        .select("student_id")
        .eq("paystack_subscription_code", flw_sub_id)
        .maybe_single()
        .execute()
    )
    if not row.data:
        return

    student_id = row.data["student_id"]
    sb.table("subscription").update({"status": "cancelled"}).eq(
        "paystack_subscription_code", flw_sub_id
    ).execute()
    sb.table("student").update({"subscription_tier": "starter"}).eq("id", student_id).execute()


def _handle_charge_completed(sb: Client, data: dict):
    """Renew period_end on a successful recurring charge."""
    customer = data.get("customer", {})
    email = customer.get("customer_email") or customer.get("email")
    if not email:
        return

    student_id = _student_id_from_email(sb, email)
    if not student_id:
        return

    now = datetime.now(timezone.utc)
    sb.table("subscription").update(
        {
            "status": "active",
            "period_start": now.isoformat(),
            "period_end": (now + timedelta(days=30)).isoformat(),
        }
    ).eq("student_id", student_id).execute()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _student_id_from_email(sb: Client, email: str) -> str | None:
    row = sb.table("student").select("id").eq("email", email).maybe_single().execute()
    return row.data["id"] if row.data else None
