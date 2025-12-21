"""Entitlement models for authorization output.

These models represent the resolved state of user identity, role, subscription, and limits.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role within the ZimPrep system.
    
    Determines base permissions and UI access.
    """
    
    STUDENT = "student"
    """Individual learner or family account member."""
    
    PARENT = "parent"
    """Guardian with oversight access to student progress."""
    
    SCHOOL_ADMIN = "school_admin"
    """School administrator with multi-student access."""
    
    TEACHER = "teacher"
    """Teacher with class management capabilities."""


class SubscriptionTier(str, Enum):
    """Subscription tier determining feature access.
    
    Each tier includes features from lower tiers plus additional capabilities.
    """
    
    FREE = "free"
    """Free tier with basic exam access."""
    
    PREMIUM = "premium"
    """Premium tier with AI explanations and advanced analytics."""
    
    SCHOOL = "school"
    """School tier with unlimited access and administrative features."""


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle status.
    
    Determines whether subscription features are accessible.
    """
    
    ACTIVE = "active"
    """Subscription is active and features are accessible."""
    
    TRIAL = "trial"
    """Trial period, features accessible until trial end."""
    
    EXPIRED = "expired"
    """Subscription has expired, no feature access."""
    
    CANCELLED = "cancelled"
    """Subscription cancelled by user, may have grace period."""
    
    SUSPENDED = "suspended"
    """Subscription suspended (e.g., payment failure)."""
    
    PENDING = "pending"
    """Subscription pending activation."""


class ResolvedIdentity(BaseModel):
    """Resolved user identity from auth context.
    
    Represents the authenticated user and their account association.
    """
    
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    account_id: str = Field(..., description="Associated account identifier")
    account_name: str = Field(..., description="Account display name")
    account_type: str = Field(
        ...,
        description="Account type (individual, family, school)"
    )


class SubscriptionState(BaseModel):
    """Current subscription state for the account.
    
    Includes tier, status, and feature entitlements.
    """
    
    subscription_id: str = Field(..., description="Subscription record identifier")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    status: SubscriptionStatus = Field(..., description="Lifecycle status")
    
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: Optional[datetime] = Field(
        None,
        description="Subscription end date (null if indefinite)"
    )
    
    is_trial: bool = Field(default=False, description="Whether this is a trial")
    trial_end_date: Optional[datetime] = Field(
        None,
        description="Trial end date if applicable"
    )
    
    base_features: list[str] = Field(
        default_factory=list,
        description="Base features included in tier"
    )
    
    addon_features: list[str] = Field(
        default_factory=list,
        description="Additional features from add-ons or promotions"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional subscription metadata"
    )


class UsageLimit(BaseModel):
    """Single usage limit with current usage and maximum allowed."""
    
    used: int = Field(..., description="Current usage count")
    max: int = Field(..., description="Maximum allowed (999999 = unlimited)")
    remaining: int = Field(..., description="Remaining quota")
    resets_at: Optional[datetime] = Field(
        None,
        description="When the limit resets (null if no reset)"
    )


class UsageLimits(BaseModel):
    """All usage limits for the current subscription.
    
    Tracks rate limits and quotas for various actions.
    """
    
    exams_per_day: Optional[UsageLimit] = Field(
        None,
        description="Daily exam attempt limit"
    )
    
    ai_explanations_per_week: Optional[UsageLimit] = Field(
        None,
        description="Weekly AI explanation request limit"
    )
    
    analytics_exports_per_month: Optional[UsageLimit] = Field(
        None,
        description="Monthly analytics export limit"
    )
    
    practice_sessions_per_day: Optional[UsageLimit] = Field(
        None,
        description="Daily practice session limit"
    )
    
    custom_limits: Dict[str, UsageLimit] = Field(
        default_factory=dict,
        description="Additional custom limits"
    )
