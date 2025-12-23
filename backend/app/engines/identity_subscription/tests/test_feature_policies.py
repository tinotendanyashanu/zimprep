"""Test feature policy evaluation.

Tests feature access based on subscription tiers and overrides.
"""

import pytest

from app.engines.identity_subscription.services.feature_policy import FeaturePolicy
from app.engines.identity_subscription.schemas.input import ActionType, RequestedAction
from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionState,
    SubscriptionTier,
    SubscriptionStatus,
)
from datetime import datetime


def test_free_tier_exam_access_allowed():
    """Test free tier can access exams."""
    subscription_state = SubscriptionState(
        subscription_id="sub-123",
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=None,
        is_trial=False,
        trial_end_date=None,
        base_features=["exam_access"],
        addon_features=[],
        metadata={}
    )
    
    requested_action = RequestedAction(action_type=ActionType.VIEW_EXAM)
    
    allowed, feature = FeaturePolicy.evaluate(
        subscription_state=subscription_state,
        feature_overrides={},
        requested_action=requested_action
    )
    
    assert allowed is True
    assert feature == "exam_access"


def test_free_tier_ai_explanation_denied():
    """Test free tier cannot access AI explanations."""
    subscription_state = SubscriptionState(
        subscription_id="sub-123",
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=None,
        is_trial=False,
        trial_end_date=None,
        base_features=["exam_access"],
        addon_features=[],
        metadata={}
    )
    
    requested_action = RequestedAction(action_type=ActionType.VIEW_AI_EXPLANATION)
    
    allowed, feature = FeaturePolicy.evaluate(
        subscription_state=subscription_state,
        feature_overrides={},
        requested_action=requested_action
    )
    
    assert allowed is False
    assert feature == "ai_explanations"


def test_premium_tier_ai_explanation_allowed():
    """Test premium tier can access AI explanations."""
    subscription_state = SubscriptionState(
        subscription_id="sub-123",
        tier=SubscriptionTier.STUDENT_PLUS,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=None,
        is_trial=False,
        trial_end_date=None,
        base_features=[],
        addon_features=[],
        metadata={}
    )
    
    requested_action = RequestedAction(action_type=ActionType.VIEW_AI_EXPLANATION)
    
    allowed, feature = FeaturePolicy.evaluate(
        subscription_state=subscription_state,
        feature_overrides={},
        requested_action=requested_action
    )
    
    assert allowed is True


def test_feature_override_enables_access():
    """Test feature override allows access even if not in tier."""
    subscription_state = SubscriptionState(
        subscription_id="sub-123",
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=None,
        is_trial=False,
        trial_end_date=None,
        base_features=["exam_access"],
        addon_features=[],
        metadata={}
    )
    
    requested_action = RequestedAction(action_type=ActionType.VIEW_AI_EXPLANATION)
    
    # Override enables AI explanations
    allowed, feature = FeaturePolicy.evaluate(
        subscription_state=subscription_state,
        feature_overrides={"ai_explanations": True},
        requested_action=requested_action
    )
    
    assert allowed is True


def test_feature_override_disables_access():
    """Test feature override can disable access even if in tier."""
    subscription_state = SubscriptionState(
        subscription_id="sub-123",
        tier=SubscriptionTier.STUDENT_PLUS,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow(),
        end_date=None,
        is_trial=False,
        trial_end_date=None,
        base_features=[],
        addon_features=[],
        metadata={}
    )
    
    requested_action = RequestedAction(action_type=ActionType.VIEW_AI_EXPLANATION)
    
    # Override disables AI explanations
    allowed, feature = FeaturePolicy.evaluate(
        subscription_state=subscription_state,
        feature_overrides={"ai_explanations": False},
        requested_action=requested_action
    )
    
    assert allowed is False
