"""Limit policy evaluator.

Evaluates usage limits and rate limiting.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from app.engines.identity_subscription.schemas.input import ActionType, RequestedAction
from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionState,
    SubscriptionTier,
    UsageLimits,
    UsageLimit,
)

logger = logging.getLogger(__name__)


# Limit definitions per tier
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "exams_per_day": 5,
        "ai_explanations_per_week": 0,
        "analytics_exports_per_month": 0,
        "practice_sessions_per_day": 10,
    },
    SubscriptionTier.STUDENT_PLUS: {
        "exams_per_day": 999999,  # Unlimited
        "ai_explanations_per_week": 50,
        "analytics_exports_per_month": 10,
        "practice_sessions_per_day": 999999,  # Unlimited
    },
    SubscriptionTier.SCHOOL: {
        "exams_per_day": 999999,  # Unlimited
        "ai_explanations_per_week": 999999,  # Unlimited
        "analytics_exports_per_month": 999999,  # Unlimited
        "practice_sessions_per_day": 999999,  # Unlimited
    },
}


# Action to limit mapping
ACTION_LIMIT_MAP = {
    ActionType.START_EXAM: "exams_per_day",
    ActionType.SUBMIT_EXAM: "exams_per_day",
    ActionType.VIEW_RECOMMENDATIONS: "ai_explanations_per_week",
    ActionType.EXPORT_REPORT_PDF: "analytics_exports_per_month",
    ActionType.EXPORT_REPORT_CSV: "analytics_exports_per_month",
    ActionType.START_PRACTICE: "practice_sessions_per_day",
}


class LimitPolicy:
    """Evaluates usage limits and quotas."""
    
    def __init__(self, usage_cache):
        """Initialize with usage cache.
        
        Args:
            usage_cache: RateLimitCache instance for tracking usage
        """
        self.usage_cache = usage_cache
    
    async def evaluate(
        self,
        subscription_state: Optional[SubscriptionState],
        user_id: str,
        requested_action: RequestedAction,
        trace_id: Optional[str] = None
    ) -> tuple[bool, UsageLimits]:
        """Evaluate usage limits for requested action.
        
        Args:
            subscription_state: Current subscription state
            user_id: User identifier
            requested_action: Action being requested
            trace_id: Trace ID for logging
        
        Returns:
            Tuple of (is_allowed, usage_limits_snapshot)
        """
        # Get tier
        tier = subscription_state.tier if subscription_state else SubscriptionTier.FREE
        
        # Get limits for tier
        limits_config = TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])
        
        # Build usage limits snapshot
        usage_limits = await self._build_usage_limits(
            user_id=user_id,
            limits_config=limits_config,
            trace_id=trace_id
        )
        
        # Check if action requires limit enforcement
        action_type = requested_action.action_type
        limit_key = ACTION_LIMIT_MAP.get(action_type)
        
        if limit_key is None:
            # No limit for this action
            logger.debug(
                f"No usage limit for action: {action_type.value}",
                extra={"trace_id": trace_id}
            )
            return (True, usage_limits)
        
        # Get specific limit
        limit = getattr(usage_limits, limit_key, None)
        
        if limit is None:
            logger.warning(
                f"Limit key not found: {limit_key}",
                extra={"trace_id": trace_id}
            )
            return (True, usage_limits)
        
        # Check if limit exceeded
        is_allowed = limit.remaining > 0
        
        logger.info(
            f"Limit check: {limit_key} = {limit.used}/{limit.max} (allowed={is_allowed})",
            extra={
                "trace_id": trace_id,
                "action": action_type.value,
                "remaining": limit.remaining
            }
        )
        
        return (is_allowed, usage_limits)
    
    async def _build_usage_limits(
        self,
        user_id: str,
        limits_config: dict[str, int],
        trace_id: Optional[str] = None
    ) -> UsageLimits:
        """Build usage limits snapshot from cache.
        
        Args:
            user_id: User identifier
            limits_config: Limits configuration from tier
            trace_id: Trace ID for logging
        
        Returns:
            UsageLimits model with current usage
        """
        now = datetime.utcnow()
        
        # Get daily limits
        exams_used = await self.usage_cache.get_usage(
            user_id=user_id,
            action_type="exams",
            window_seconds=86400,  # 24 hours
            trace_id=trace_id
        )
        practice_used = await self.usage_cache.get_usage(
            user_id=user_id,
            action_type="practice_sessions",
            window_seconds=86400,
            trace_id=trace_id
        )
        
        # Get weekly limits
        ai_explanations_used = await self.usage_cache.get_usage(
            user_id=user_id,
            action_type="ai_explanations",
            window_seconds=604800,  # 7 days
            trace_id=trace_id
        )
        
        # Get monthly limits
        exports_used = await self.usage_cache.get_usage(
            user_id=user_id,
            action_type="analytics_exports",
            window_seconds=2592000,  # 30 days
            trace_id=trace_id
        )
        
        # Build UsageLimits
        return UsageLimits(
            exams_per_day=UsageLimit(
                used=exams_used,
                max=limits_config.get("exams_per_day", 999999),
                remaining=max(0, limits_config.get("exams_per_day", 999999) - exams_used),
                resets_at=now + timedelta(days=1)
            ),
            ai_explanations_per_week=UsageLimit(
                used=ai_explanations_used,
                max=limits_config.get("ai_explanations_per_week", 0),
                remaining=max(0, limits_config.get("ai_explanations_per_week", 0) - ai_explanations_used),
                resets_at=now + timedelta(weeks=1)
            ),
            analytics_exports_per_month=UsageLimit(
                used=exports_used,
                max=limits_config.get("analytics_exports_per_month", 0),
                remaining=max(0, limits_config.get("analytics_exports_per_month", 0) - exports_used),
                resets_at=now + timedelta(days=30)
            ),
            practice_sessions_per_day=UsageLimit(
                used=practice_used,
                max=limits_config.get("practice_sessions_per_day", 999999),
                remaining=max(0, limits_config.get("practice_sessions_per_day", 999999) - practice_used),
                resets_at=now + timedelta(days=1)
            ),
        )
