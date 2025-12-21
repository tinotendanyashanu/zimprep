"""Denial reason taxonomy for explicit authorization failures.

All denial decisions must include an explicit reason for legal/audit compliance.
"""

from enum import Enum


class DenialReason(str, Enum):
    """Explicit reasons for authorization denial.
    
    Each reason is legally defensible and maps to a specific failure condition.
    """
    
    # Authentication failures
    UNAUTHENTICATED = "unauthenticated"
    """No auth context provided in request."""
    
    INVALID_TOKEN = "invalid_token"
    """Auth token validation failed."""
    
    # Identity resolution failures
    USER_NOT_FOUND = "user_not_found"
    """User identity could not be resolved from auth context."""
    
    ACCOUNT_NOT_FOUND = "account_not_found"
    """Account associated with user not found."""
    
    # Account status failures
    ACCOUNT_SUSPENDED = "account_suspended"
    """Account administratively suspended."""
    
    USER_INACTIVE = "user_inactive"
    """User account is inactive or disabled."""
    
    # Subscription failures
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    """Subscription lifecycle has ended."""
    
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    """Subscription was explicitly cancelled."""
    
    SUBSCRIPTION_SUSPENDED = "subscription_suspended"
    """Subscription suspended (e.g., payment failure)."""
    
    NO_ACTIVE_SUBSCRIPTION = "no_active_subscription"
    """No active subscription found for account."""
    
    # Feature entitlement failures
    FEATURE_NOT_ENTITLED = "feature_not_entitled"
    """Requested feature not included in subscription tier."""
    
    FEATURE_DISABLED = "feature_disabled"
    """Feature explicitly disabled via feature flag."""
    
    # Usage limit failures
    USAGE_LIMIT_EXCEEDED = "usage_limit_exceeded"
    """Rate limit or quota exceeded for this action."""
    
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    """Daily usage limit exceeded."""
    
    WEEKLY_LIMIT_EXCEEDED = "weekly_limit_exceeded"
    """Weekly usage limit exceeded."""
    
    # Infrastructure failures (fail-closed)
    DATABASE_ERROR = "database_error"
    """Database connection or query failed."""
    
    CACHE_ERROR = "cache_error"
    """Cache operation failed (non-fatal, but logged)."""
    
    CACHE_INCONSISTENCY = "cache_inconsistency"
    """Cache validation failed, data inconsistency detected."""
    
    # Ambiguity failures (fail-closed)
    AMBIGUOUS_STATE = "ambiguous_state"
    """Multiple conflicting states detected (e.g., multiple active subscriptions)."""
    
    INVALID_INPUT = "invalid_input"
    """Input validation failed."""
    
    # Generic fallback
    UNKNOWN_ERROR = "unknown_error"
    """Unclassified error (should be avoided, log for investigation)."""
