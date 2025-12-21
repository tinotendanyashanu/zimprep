"""Subscription resolver service.

Resolves subscription state from account with lifecycle validation.
"""

import logging
from typing import Optional
from datetime import datetime

from app.engines.identity_subscription.schemas.entitlements import (
    SubscriptionState,
    SubscriptionTier,
    SubscriptionStatus,
)
from app.engines.identity_subscription.repositories import SubscriptionRepository
from app.engines.identity_subscription.repositories.models import Account

logger = logging.getLogger(__name__)


class SubscriptionResolver:
    """Resolves subscription state from account."""
    
    def __init__(self):
        self.subscription_repo = SubscriptionRepository()
    
    async def resolve(
        self,
        account: Account,
        trace_id: Optional[str] = None
    ) -> Optional[SubscriptionState]:
        """Resolve subscription state for account.
        
        Args:
            account: Account database record
            trace_id: Trace ID for logging
        
        Returns:
            SubscriptionState if active subscription exists, None otherwise
        """
        # Fetch active subscription
        subscription = await self.subscription_repo.get_active_by_account(
            account.id,
            trace_id=trace_id
        )
        
        if subscription is None:
            logger.info(
                f"No active subscription for account: {account.id}",
                extra={"trace_id": trace_id}
            )
            return None
        
        # Check if expired
        if self.subscription_repo.is_expired(subscription):
            logger.info(
                f"Subscription expired: {subscription.id}",
                extra={
                    "trace_id": trace_id,
                    "account_id": account.id,
                    "end_date": subscription.end_date
                }
            )
            return None
        
        # Build subscription state
        state = SubscriptionState(
            subscription_id=subscription.id,
            tier=SubscriptionTier(subscription.tier),
            status=SubscriptionStatus(subscription.status),
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            is_trial=self.subscription_repo.is_trial(subscription),
            trial_end_date=subscription.trial_end_date,
            base_features=self.subscription_repo.get_base_features(subscription),
            addon_features=self.subscription_repo.get_addon_features(subscription),
            metadata=subscription.metadata or {},
        )
        
        logger.info(
            f"Subscription resolved: {subscription.id}",
            extra={
                "trace_id": trace_id,
                "tier": state.tier.value,
                "status": state.status.value,
                "is_trial": state.is_trial
            }
        )
        
        return state
    
    @staticmethod
    def get_default_free_tier() -> SubscriptionState:
        """Get default free tier subscription for accounts without subscription.
        
        Returns:
            SubscriptionState representing free tier
        """
        return SubscriptionState(
            subscription_id="free-default",
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.utcnow(),
            end_date=None,  # Indefinite
            is_trial=False,
            trial_end_date=None,
            base_features=["exam_access", "basic_analytics"],
            addon_features=[],
            metadata={"default": True},
        )
