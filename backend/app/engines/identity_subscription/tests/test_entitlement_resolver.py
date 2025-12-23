"""Unit tests for EntitlementResolver service.

Tests the feature resolution matrix for all subscription tiers and
verifies override application logic.
"""

import pytest
from app.engines.identity_subscription.services.entitlement_resolver import EntitlementResolver
from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionTier,
    FeatureFlag,
)


class TestEntitlementResolver:
    """Test cases for entitlement resolution."""
    
    def test_free_tier_features(self):
        """Test that FREE tier has only basic AI marking enabled."""
        features = EntitlementResolver.resolve(SubscriptionTier.FREE)
        
        assert features[FeatureFlag.AI_MARKING_BASIC] == True
        assert features[Feature Flag.AI_MARKING_DETAILED] == False
        assert features[FeatureFlag.APPEAL_ACCESS] == False
        assert features[FeatureFlag.REPORT_EXPORT_PDF] == False
        assert features[FeatureFlag.REPORT_EXPORT_CSV] == False
        assert features[FeatureFlag.PARENT_VIEW] == False
        assert features[FeatureFlag.SCHOOL_DASHBOARD] == False
        assert features[FeatureFlag.HISTORICAL_ANALYTICS] == False
    
    def test_student_plus_features(self):
        """Test that STUDENT_PLUS tier has appropriate features."""
        features = EntitlementResolver.resolve(SubscriptionTier.STUDENT_PLUS)
        
        assert features[FeatureFlag.AI_MARKING_BASIC] == True
        assert features[FeatureFlag.AI_MARKING_DETAILED] == True
        assert features[FeatureFlag.APPEAL_ACCESS] == True
        assert features[FeatureFlag.REPORT_EXPORT_PDF] == True
        assert features[FeatureFlag.REPORT_EXPORT_CSV] == False  # School only
        assert features[FeatureFlag.PARENT_VIEW] == True
        assert features[FeatureFlag.SCHOOL_DASHBOARD] == False  # School only
        assert features[FeatureFlag.HISTORICAL_ANALYTICS] == False  # School only
    
    def test_school_tier_all_access(self):
        """Test that SCHOOL tier has all features enabled."""
        features = EntitlementResolver.resolve(SubscriptionTier.SCHOOL)
        
        # All features should be enabled for SCHOOL tier
        assert all(features.values())
    
    def test_admin_tier_all_access(self):
        """Test that ADMIN tier has all features enabled."""
        features = EntitlementResolver.resolve(SubscriptionTier.ADMIN)
        
        # All features should be enabled for ADMIN tier
        assert all(features.values())
    
    def test_override_application(self):
        """Test that overrides are applied correctly over base tier."""
        overrides = {"appeal_access": True}
        features = EntitlementResolver.resolve(
            SubscriptionTier.FREE,
            overrides=overrides
        )
        
        # Override applied - FREE user gets appeal access
        assert features[FeatureFlag.APPEAL_ACCESS] == True
        # Base features still intact
        assert features[FeatureFlag.AI_MARKING_BASIC] == True
    
    def test_override_can_disable_feature(self):
        """Test that overrides can disable features."""
        overrides = {"ai_marking_detailed": False}
        features = EntitlementResolver.resolve(
            SubscriptionTier.STUDENT_PLUS,
            overrides=overrides
        )
        
        # Override applied - disabled detailed AI
        assert features[FeatureFlag.AI_MARKING_DETAILED] == False
        # Other features still enabled
        assert features[FeatureFlag.AI_MARKING_BASIC] == True
        assert features[FeatureFlag.APPEAL_ACCESS] == True
    
    def test_get_enabled_features(self):
        """Test get_enabled_features returns only enabled features."""
        enabled = EntitlementResolver.get_enabled_features(
            SubscriptionTier.FREE
        )
        
        assert "ai_marking_basic" in enabled
        assert "ai_marking_detailed" not in enabled
        assert "appeal_access" not in enabled
    
    def test_is_feature_enabled(self):
        """Test is_feature_enabled check."""
        assert EntitlementResolver.is_feature_enabled(
            SubscriptionTier.STUDENT_PLUS,
            FeatureFlag.APPEAL_ACCESS
        ) == True
        
        assert EntitlementResolver.is_feature_enabled(
            SubscriptionTier.FREE,
            FeatureFlag.APPEAL_ACCESS
        ) == False
    
    def test_validate_tier_upgrade(self):
        """Test tier upgrade validation."""
        # Valid upgrades
        assert EntitlementResolver.validate_tier_upgrade(
            SubscriptionTier.FREE,
            SubscriptionTier.STUDENT_PLUS
        ) == True
        
        assert EntitlementResolver.validate_tier_upgrade(
            SubscriptionTier.STUDENT_PLUS,
            SubscriptionTier.SCHOOL
        ) == True
        
        # No downgrade from SCHOOL to FREE
        assert EntitlementResolver.validate_tier_upgrade(
            SubscriptionTier.SCHOOL,
            SubscriptionTier.FREE
        ) == False
        
        # Same tier is valid
        assert EntitlementResolver.validate_tier_upgrade(
            SubscriptionTier.STUDENT_PLUS,
            SubscriptionTier.STUDENT_PLUS
        ) == True
