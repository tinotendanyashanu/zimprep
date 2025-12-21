"""Policy composer service.

Composes final entitlement decision from all policy evaluations.
"""

import logging
from typing import Optional

from app.engines.identity_subscription.schemas.output import IdentitySubscriptionOutput
from app.engines.identity_subscription.schemas.denial_reasons import DenialReason
from app.engines.identity_subscription.schemas.entitlements import (
    ResolvedIdentity,
    UserRole,
    SubscriptionState,
    UsageLimits,
)

logger = logging.getLogger(__name__)


class PolicyComposer:
    """Composes final authorization decision from policy evaluations."""
    
    @staticmethod
    def compose_allowed(
        resolved_identity: ResolvedIdentity,
        resolved_role: UserRole,
        subscription_state: Optional[SubscriptionState],
        enabled_features: list[str],
        usage_limits: UsageLimits,
        confidence: float = 1.0,
        cached: bool = False,
        metadata: Optional[dict] = None
    ) -> IdentitySubscriptionOutput:
        """Compose allowed decision.
        
        Args:
            resolved_identity: Resolved user identity
            resolved_role: Resolved user role
            subscription_state: Subscription state (may be None for free tier)
            enabled_features: List of enabled feature keys
            usage_limits: Current usage limits
            confidence: Confidence score (0.0-1.0)
            cached: Whether result was from cache
            metadata: Additional metadata
        
        Returns:
            IdentitySubscriptionOutput with allowed=True
        """
        return IdentitySubscriptionOutput(
            allowed=True,
            resolved_identity=resolved_identity,
            resolved_role=resolved_role,
            subscription_state=subscription_state,
            enabled_features=enabled_features,
            usage_limits=usage_limits,
            denial_reason=None,
            denial_message=None,
            confidence=confidence,
            cached=cached,
            metadata=metadata or {},
        )
    
    @staticmethod
    def compose_denied(
        denial_reason: DenialReason,
        denial_message: str,
        resolved_identity: Optional[ResolvedIdentity] = None,
        resolved_role: Optional[UserRole] = None,
        subscription_state: Optional[SubscriptionState] = None,
        enabled_features: Optional[list[str]] = None,
        usage_limits: Optional[UsageLimits] = None,
        confidence: float = 1.0,
        metadata: Optional[dict] = None
    ) -> IdentitySubscriptionOutput:
        """Compose denied decision.
        
        Args:
            denial_reason: Explicit denial reason
            denial_message: Human-readable denial message
            resolved_identity: Resolved identity (if available)
            resolved_role: Resolved role (if available)
            subscription_state: Subscription state (if available)
            enabled_features: Enabled features (if available)
            usage_limits: Usage limits (if available)
            confidence: Confidence score (0.0-1.0)
            metadata: Additional metadata
        
        Returns:
            IdentitySubscriptionOutput with allowed=False
        """
        return IdentitySubscriptionOutput(
            allowed=False,
            resolved_identity=resolved_identity,
            resolved_role=resolved_role,
            subscription_state=subscription_state,
            enabled_features=enabled_features or [],
            usage_limits=usage_limits,
            denial_reason=denial_reason,
            denial_message=denial_message,
            confidence=confidence,
            cached=False,  # Never cache denied responses
            metadata=metadata or {},
        )
    
    @staticmethod
    def get_denial_message(denial_reason: DenialReason) -> str:
        """Get human-readable message for denial reason.
        
        Args:
            denial_reason: Denial reason enum
        
        Returns:
            Human-readable message
        """
        messages = {
            DenialReason.UNAUTHENTICATED: "You must be logged in to access this resource.",
            DenialReason.INVALID_TOKEN: "Your session is invalid. Please log in again.",
            DenialReason.USER_NOT_FOUND: "User account not found.",
            DenialReason.ACCOUNT_NOT_FOUND: "Account not found.",
            DenialReason.ACCOUNT_SUSPENDED: "Your account has been suspended. Please contact support.",
            DenialReason.USER_INACTIVE: "Your account is inactive.",
            DenialReason.SUBSCRIPTION_EXPIRED: "Your subscription has expired. Please renew to continue.",
            DenialReason.SUBSCRIPTION_CANCELLED: "Your subscription was cancelled.",
            DenialReason.SUBSCRIPTION_SUSPENDED: "Your subscription is suspended due to payment issues.",
            DenialReason.NO_ACTIVE_SUBSCRIPTION: "No active subscription found.",
            DenialReason.FEATURE_NOT_ENTITLED: "This feature is not included in your current plan. Upgrade to access.",
            DenialReason.FEATURE_DISABLED: "This feature is currently disabled.",
            DenialReason.USAGE_LIMIT_EXCEEDED: "You have exceeded your usage limit for this action.",
            DenialReason.DAILY_LIMIT_EXCEEDED: "You have reached your daily limit for this action.",
            DenialReason.WEEKLY_LIMIT_EXCEEDED: "You have reached your weekly limit for this action.",
            DenialReason.DATABASE_ERROR: "Service temporarily unavailable. Please try again later.",
            DenialReason.CACHE_ERROR: "Service temporarily unavailable. Please try again later.",
            DenialReason.CACHE_INCONSISTENCY: "Data integrity issue detected. Please try again.",
            DenialReason.AMBIGUOUS_STATE: "Account state is ambiguous. Please contact support.",
            DenialReason.INVALID_INPUT: "Invalid request parameters.",
            DenialReason.UNKNOWN_ERROR: "An unexpected error occurred. Please try again later.",
        }
        
        return messages.get(
            denial_reason,
            "Access denied."
        )
