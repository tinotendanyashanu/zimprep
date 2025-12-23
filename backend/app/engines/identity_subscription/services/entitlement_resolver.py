"""Entitlement resolver service.

Resolves feature flags based on subscription tier with optional overrides.
This is the SINGLE SOURCE OF TRUTH for feature access determination.

CRITICAL RULES:
- Feature matrix is immutable and embedded in code
- Pricing changes require code deployment (by design)
- Overrides are applied AFTER base resolution
- All resolutions are deterministic and reproducible
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionTier,
    FeatureFlag,
)

logger = logging.getLogger(__name__)


class EntitlementResolver:
    """Resolves feature entitlements based on subscription tier.
    
    This service implements the authoritative feature matrix that determines
    which features are available to each subscription tier.
    """
    
    # Authoritative feature matrix
    # This is the SINGLE SOURCE OF TRUTH for feature access
    BASE_FEATURE_MATRIX: Dict[SubscriptionTier, Dict[FeatureFlag, bool]] = {
        SubscriptionTier.FREE: {
            FeatureFlag.AI_MARKING_BASIC: True,
            FeatureFlag.AI_MARKING_DETAILED: False,
            FeatureFlag.APPEAL_ACCESS: False,
            FeatureFlag.REPORT_EXPORT_PDF: False,
            FeatureFlag.REPORT_EXPORT_CSV: False,
            FeatureFlag.PARENT_VIEW: False,
            FeatureFlag.SCHOOL_DASHBOARD: False,
            FeatureFlag.HISTORICAL_ANALYTICS: False,
        },
        SubscriptionTier.STUDENT_PLUS: {
            FeatureFlag.AI_MARKING_BASIC: True,
            FeatureFlag.AI_MARKING_DETAILED: True,
            FeatureFlag.APPEAL_ACCESS: True,
            FeatureFlag.REPORT_EXPORT_PDF: True,
            FeatureFlag.REPORT_EXPORT_CSV: False,
            FeatureFlag.PARENT_VIEW: True,
            FeatureFlag.SCHOOL_DASHBOARD: False,
            FeatureFlag.HISTORICAL_ANALYTICS: False,
        },
        SubscriptionTier.SCHOOL: {
            FeatureFlag.AI_MARKING_BASIC: True,
            FeatureFlag.AI_MARKING_DETAILED: True,
            FeatureFlag.APPEAL_ACCESS: True,
            FeatureFlag.REPORT_EXPORT_PDF: True,
            FeatureFlag.REPORT_EXPORT_CSV: True,
            FeatureFlag.PARENT_VIEW: True,
            FeatureFlag.SCHOOL_DASHBOARD: True,
            FeatureFlag.HISTORICAL_ANALYTICS: True,
        },
        SubscriptionTier.INSTITUTION: {
            # Institution tier = School tier + future features
            FeatureFlag.AI_MARKING_BASIC: True,
            FeatureFlag.AI_MARKING_DETAILED: True,
            FeatureFlag.APPEAL_ACCESS: True,
            FeatureFlag.REPORT_EXPORT_PDF: True,
            FeatureFlag.REPORT_EXPORT_CSV: True,
            FeatureFlag.PARENT_VIEW: True,
            FeatureFlag.SCHOOL_DASHBOARD: True,
            FeatureFlag.HISTORICAL_ANALYTICS: True,
        },
        SubscriptionTier.ADMIN: {
            # Admin tier = all features enabled
            FeatureFlag.AI_MARKING_BASIC: True,
            FeatureFlag.AI_MARKING_DETAILED: True,
            FeatureFlag.APPEAL_ACCESS: True,
            FeatureFlag.REPORT_EXPORT_PDF: True,
            FeatureFlag.REPORT_EXPORT_CSV: True,
            FeatureFlag.PARENT_VIEW: True,
            FeatureFlag.SCHOOL_DASHBOARD: True,
            FeatureFlag.HISTORICAL_ANALYTICS: True,
        },
    }
    
    @staticmethod
    def resolve(
        tier: SubscriptionTier,
        overrides: Optional[Dict[str, bool]] = None
    ) -> Dict[FeatureFlag, bool]:
        """Resolve feature flags for a subscription tier.
        
        Args:
            tier: Subscription tier
            overrides: Optional feature flag overrides (feature_key -> enabled)
            
        Returns:
            Dictionary mapping FeatureFlag to boolean (enabled/disabled)
            
        Raises:
            ValueError: If tier not found in feature matrix
        """
        # Get base features for tier
        if tier not in EntitlementResolver.BASE_FEATURE_MATRIX:
            logger.error(f"Unknown subscription tier: {tier}")
            raise ValueError(f"Unknown subscription tier: {tier}")
        
        # Copy base features (immutable base matrix)
        resolved = EntitlementResolver.BASE_FEATURE_MATRIX[tier].copy()
        
        # Apply overrides if provided
        if overrides:
            for feature_key, enabled in overrides.items():
                try:
                    # Convert string key to FeatureFlag enum
                    feature_flag = FeatureFlag(feature_key)
                    resolved[feature_flag] = enabled
                    
                    logger.info(
                        f"Override applied: {feature_key}={enabled} for tier {tier.value}"
                    )
                except ValueError:
                    logger.warning(
                        f"Unknown feature flag in override: {feature_key}, ignoring"
                    )
                    continue
        
        return resolved
    
    @staticmethod
    def get_enabled_features(
        tier: SubscriptionTier,
        overrides: Optional[Dict[str, bool]] = None
    ) -> list[str]:
        """Get list of enabled feature keys.
        
        Args:
            tier: Subscription tier
            overrides: Optional feature flag overrides
            
        Returns:
            List of enabled feature keys (as strings)
        """
        features = EntitlementResolver.resolve(tier, overrides)
        return [
            flag.value for flag, enabled in features.items() if enabled
        ]
    
    @staticmethod
    def is_feature_enabled(
        tier: SubscriptionTier,
        feature: FeatureFlag,
        overrides: Optional[Dict[str, bool]] = None
    ) -> bool:
        """Check if a specific feature is enabled.
        
        Args:
            tier: Subscription tier
            feature: Feature flag to check
            overrides: Optional feature flag overrides
            
        Returns:
            True if feature is enabled, False otherwise
        """
        features = EntitlementResolver.resolve(tier, overrides)
        return features.get(feature, False)
    
    @staticmethod
    def validate_tier_upgrade(
        from_tier: SubscriptionTier,
        to_tier: SubscriptionTier
    ) -> bool:
        """Validate if tier upgrade is valid.
        
        Args:
            from_tier: Current tier
            to_tier: Target tier
            
        Returns:
            True if upgrade is valid, False otherwise
        """
        tier_hierarchy = [
            SubscriptionTier.FREE,
            SubscriptionTier.STUDENT_PLUS,
            SubscriptionTier.SCHOOL,
            SubscriptionTier.INSTITUTION,
            SubscriptionTier.ADMIN,
        ]
        
        try:
            from_index = tier_hierarchy.index(from_tier)
            to_index = tier_hierarchy.index(to_tier)
            return to_index >= from_index
        except ValueError:
            return False
