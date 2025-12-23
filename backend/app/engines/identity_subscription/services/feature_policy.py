"""Feature policy evaluator.

Maps action types to required features and evaluates access.
"""

import logging
from typing import Optional

from app.engines.identity_subscription.schemas.input import ActionType, RequestedAction
from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionState,
    SubscriptionTier,
)

logger = logging.getLogger(__name__)


# Feature mapping from action types to required features
ACTION_FEATURE_MAP = {
    # Exam access actions (free tier)
    ActionType.VIEW_EXAM: "exam_access",
    ActionType.SUBMIT_ANSWER: "exam_access",
    ActionType.VIEW_EXAM_RESULTS: "exam_access",
    ActionType.VIEW_PRACTICE_HISTORY: "exam_access",
    
    # Practice actions (free tier)
    ActionType.START_PRACTICE_SESSION: "practice_mode",
    
    # AI-powered actions (premium tier)
    ActionType.VIEW_AI_EXPLANATION: "ai_explanations",
    ActionType.VIEW_AI_RECOMMENDATIONS: "ai_recommendations",
    
    # Analytics actions (premium tier)
    ActionType.VIEW_ANALYTICS: "advanced_analytics",
    ActionType.EXPORT_ANALYTICS: "data_export",
    
    # Administrative actions
    ActionType.MANAGE_SUBSCRIPTION: None,  # Always allowed if authenticated
    ActionType.VIEW_STUDENT_PROGRESS: "parent_dashboard",
    ActionType.MANAGE_SCHOOL: "school_admin",
}


# Default features per tier
TIER_FEATURES = {
    SubscriptionTier.FREE: [
        "exam_access",
        "basic_analytics",
        "practice_mode",
    ],
    SubscriptionTier.STUDENT_PLUS: [
        "exam_access",
        "basic_analytics",
        "practice_mode",
        "ai_explanations",
        "ai_recommendations",
        "advanced_analytics",
        "data_export",
        "parent_dashboard",
    ],
    SubscriptionTier.SCHOOL: [
        "exam_access",
        "basic_analytics",
        "practice_mode",
        "ai_explanations",
        "ai_recommendations",
        "advanced_analytics",
        "data_export",
        "parent_dashboard",
        "school_admin",
        "bulk_operations",
        "sso",
    ],
}


class FeaturePolicy:
    """Evaluates feature access based on subscription and overrides."""
    
    @staticmethod
    def evaluate(
        subscription_state: Optional[SubscriptionState],
        feature_overrides: dict[str, bool],
        requested_action: RequestedAction,
        trace_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Evaluate if requested action is allowed based on features.
        
        Args:
            subscription_state: Current subscription state (may be None for free tier)
            feature_overrides: User-specific feature flag overrides
            requested_action: Action being requested
            trace_id: Trace ID for logging
        
        Returns:
            Tuple of (is_allowed, required_feature)
        """
        action_type = requested_action.action_type
        
        # Get required feature for this action
        required_feature = ACTION_FEATURE_MAP.get(action_type)
        
        # If no feature required, allow
        if required_feature is None:
            logger.debug(
                f"Action {action_type.value} requires no feature, allowing",
                extra={"trace_id": trace_id}
            )
            return (True, None)
        
        # Check feature override first (highest priority)
        if required_feature in feature_overrides:
            is_enabled = feature_overrides[required_feature]
            logger.info(
                f"Feature override found: {required_feature}={is_enabled}",
                extra={"trace_id": trace_id, "action": action_type.value}
            )
            return (is_enabled, required_feature)
        
        # Check subscription state
        if subscription_state is None:
            # No subscription = free tier
            allowed_features = TIER_FEATURES[SubscriptionTier.FREE]
        else:
            # Get base tier features
            tier_features = TIER_FEATURES.get(
                subscription_state.tier,
                TIER_FEATURES[SubscriptionTier.FREE]
            )
            
            # Combine tier features + subscription base features + addon features
            allowed_features = set(tier_features)
            allowed_features.update(subscription_state.base_features)
            allowed_features.update(subscription_state.addon_features)
            allowed_features = list(allowed_features)
        
        # Check if required feature is in allowed features
        is_allowed = required_feature in allowed_features
        
        logger.info(
            f"Feature policy evaluation: {action_type.value} -> {is_allowed}",
            extra={
                "trace_id": trace_id,
                "required_feature": required_feature,
                "tier": subscription_state.tier.value if subscription_state else "free"
            }
        )
        
        return (is_allowed, required_feature)
    
    @staticmethod
    def get_enabled_features(
        subscription_state: Optional[SubscriptionState],
        feature_overrides: dict[str, bool],
    ) -> list[str]:
        """Get list of all enabled features for user.
        
        Args:
            subscription_state: Current subscription state
            feature_overrides: User-specific feature flag overrides
        
        Returns:
            List of enabled feature keys
        """
        # Start with tier features
        if subscription_state is None:
            enabled = set(TIER_FEATURES[SubscriptionTier.FREE])
        else:
            tier_features = TIER_FEATURES.get(
                subscription_state.tier,
                TIER_FEATURES[SubscriptionTier.FREE]
            )
            enabled = set(tier_features)
            enabled.update(subscription_state.base_features)
            enabled.update(subscription_state.addon_features)
        
        # Apply overrides
        for feature_key, is_enabled in feature_overrides.items():
            if is_enabled:
                enabled.add(feature_key)
            else:
                enabled.discard(feature_key)
        
        return sorted(list(enabled))
