"""
Subscription tier configuration, Pydantic schemas, and validation helpers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Tier configuration ─────────────────────────────────────────────────────────

TIER_CONFIG: dict[str, dict] = {
    "starter": {
        "label": "Starter",
        "price_usd": 0,
        "daily_limit": 5,         # max written submissions per day (None = unlimited)
        "subject_count": 1,        # number of subjects included (0 = any 1 at a time)
        "handwriting": False,
        "exam_mode": False,
        "paystack_plan_code": None,
    },
    "standard": {
        "label": "Standard",
        "price_usd": 5,
        "daily_limit": None,
        "subject_count": 1,
        "handwriting": True,
        "exam_mode": True,
        "paystack_plan_code": None,  # filled after create-plans call
    },
    "bundle": {
        "label": "Bundle",
        "price_usd": 12,
        "daily_limit": None,
        "subject_count": 3,
        "handwriting": True,
        "exam_mode": True,
        "paystack_plan_code": None,
    },
    "all_subjects": {
        "label": "All Subjects",
        "price_usd": 18,
        "daily_limit": None,
        "subject_count": None,  # None = all subjects
        "handwriting": True,
        "exam_mode": True,
        "paystack_plan_code": None,
    },
}

PAID_TIERS = {"standard", "bundle", "all_subjects"}

# Paystack plan names (used when creating plans)
PAYSTACK_PLAN_NAMES = {
    "standard": "ZimPrep Standard",
    "bundle": "ZimPrep Bundle",
    "all_subjects": "ZimPrep All Subjects",
}

DAILY_FREE_LIMIT = 5


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class SubscriptionRow(BaseModel):
    id: str
    student_id: str
    tier: str
    status: str
    subject_ids: list[str]
    paystack_customer_code: Optional[str]
    paystack_subscription_code: Optional[str]
    paystack_plan_code: Optional[str]
    amount_usd: float
    period_start: datetime
    period_end: datetime
    created_at: datetime
    updated_at: datetime


class QuotaStatus(BaseModel):
    tier: str
    allowed: bool
    used: int
    limit: Optional[int]  # None = unlimited
    feature: str          # "practice" | "exam" | "handwriting"


class InitializeCheckoutRequest(BaseModel):
    student_id: str
    tier: str
    subject_ids: list[str]
    email: str
    callback_url: str


class InitializeCheckoutResponse(BaseModel):
    authorization_url: str
    reference: str
    access_code: str


class VerifyPaymentRequest(BaseModel):
    reference: str
    student_id: str


class SubscriptionStatusResponse(BaseModel):
    tier: str
    subscription: Optional[dict]
    quota: QuotaStatus


class CancelSubscriptionRequest(BaseModel):
    student_id: str


# ── Validation helpers ─────────────────────────────────────────────────────────

def validate_subject_count(tier: str, subject_ids: list[str]) -> None:
    """Raise ValueError if subject_ids count doesn't match the tier requirements."""
    config = TIER_CONFIG.get(tier)
    if not config:
        raise ValueError(f"Unknown tier: {tier}")
    required = config["subject_count"]
    if required is None:
        return  # all_subjects — any count OK
    if len(subject_ids) != required:
        raise ValueError(
            f"Tier '{tier}' requires exactly {required} subject(s), "
            f"got {len(subject_ids)}"
        )


def tier_allows_exam(tier: str) -> bool:
    return True


def tier_allows_handwriting(tier: str) -> bool:
    return True


def tier_daily_limit(tier: str) -> Optional[int]:
    return None
