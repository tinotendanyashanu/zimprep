"""Output schema for Identity & Subscription Engine.

Defines the immutable entitlement snapshot returned to the orchestrator.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.engines.identity_subscription.schemas.denial_reasons import DenialReason
from app.engines.identity_subscription.schemas.entitlements import (
    ResolvedIdentity,
    UserRole,
    SubscriptionState,
    SubscriptionTier,
    FeatureFlag,
    UsageLimits,
)


class EntitlementSnapshot(BaseModel):
    """Immutable snapshot of entitlements at request time.
    
    This snapshot is created once at the start of a request and
    remains frozen for the entire request lifecycle.
    """
    
    subscription_tier: SubscriptionTier = Field(
        ...,
        description="Subscription tier at request time"
    )
    
    features: Dict[str, bool] = Field(
        ...,
        description="Feature flag values (FeatureFlag.value -> bool)"
    )
    
    resolved_at: datetime = Field(
        ...,
        description="Timestamp when entitlements were resolved"
    )
    
    expires_at: Optional[datetime] = Field(
        None,
        description="When subscription expires (null if indefinite)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make snapshot immutable


class IdentitySubscriptionOutput(BaseModel):
    """Immutable entitlement snapshot.
    
    Contains the complete authorization decision and supporting data.
    This is the single source of truth for request authorization.
    """
    
    allowed: bool = Field(
        ...,
        description="Final authorization decision (true = allow, false = deny)"
    )
    
    resolved_identity: Optional[ResolvedIdentity] = Field(
        None,
        description="Resolved user identity (null if unauthenticated or failed resolution)"
    )
    
    resolved_role: Optional[UserRole] = Field(
        None,
        description="User role (null if identity not resolved)"
    )
    
    subscription_state: Optional[SubscriptionState] = Field(
        None,
        description="Current subscription state (null if no subscription)"
    )
    
    enabled_features: list[str] = Field(
        default_factory=list,
        description="List of enabled feature keys for this user"
    )
    
    entitlement_snapshot: Optional[EntitlementSnapshot] = Field(
        None,
        description="Immutable entitlement snapshot (frozen at request start)"
    )
    
    usage_limits: Optional[UsageLimits] = Field(
        None,
        description="Current usage limits and quotas"
    )
    
    denial_reason: Optional[DenialReason] = Field(
        None,
        description="Explicit reason if denied (null if allowed)"
    )
    
    denial_message: Optional[str] = Field(
        None,
        description="Human-readable denial message (null if allowed)"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in decision (1.0 = all DB lookups succeeded, lower if fallback)"
    )
    
    cached: bool = Field(
        default=False,
        description="Whether result was served from cache"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional trace metadata for debugging"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make output immutable
