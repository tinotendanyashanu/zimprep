"""Subscription repository for subscription data access."""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.identity_subscription.repositories.models import Subscription
from app.engines.identity_subscription.repositories.database import get_session
from app.engines.identity_subscription.errors import (
    DatabaseError,
    AmbiguousStateError,
)

logger = logging.getLogger(__name__)


class SubscriptionRepository:
    """Repository for subscription operations."""
    
    @staticmethod
    async def get_active_by_account(
        account_id: str,
        trace_id: Optional[str] = None
    ) -> Optional[Subscription]:
        """Get active subscription for account.
        
        Args:
            account_id: Account identifier
            trace_id: Trace ID for logging
        
        Returns:
            Active subscription or None if not found
        
        Raises:
            AmbiguousStateError: If multiple active subscriptions found
            DatabaseError: If database query fails
        """
        try:
            async with get_session(trace_id=trace_id) as session:
                # Query for active subscriptions
                result = await session.execute(
                    select(Subscription).where(
                        and_(
                            Subscription.account_id == account_id,
                            Subscription.status.in_([
                                "active",
                                "trial"
                            ])
                        )
                    )
                )
                subscriptions = result.scalars().all()
                
                if len(subscriptions) == 0:
                    logger.debug(
                        f"No active subscription for account: {account_id}",
                        extra={"trace_id": trace_id}
                    )
                    return None
                
                if len(subscriptions) > 1:
                    logger.error(
                        f"Multiple active subscriptions found for account: {account_id}",
                        extra={
                            "trace_id": trace_id,
                            "count": len(subscriptions)
                        }
                    )
                    raise AmbiguousStateError(
                        message=f"Account {account_id} has {len(subscriptions)} active subscriptions",
                        trace_id=trace_id,
                        metadata={
                            "account_id": account_id,
                            "subscription_ids": [s.id for s in subscriptions]
                        }
                    )
                
                subscription = subscriptions[0]
                logger.debug(
                    f"Active subscription found: {subscription.id}",
                    extra={
                        "trace_id": trace_id,
                        "tier": subscription.tier,
                        "status": subscription.status
                    }
                )
                
                return subscription
        
        except (DatabaseError, AmbiguousStateError):
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching subscription for account: {account_id}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            raise DatabaseError(
                message=f"Failed to fetch subscription for account {account_id}: {str(e)}",
                trace_id=trace_id,
                metadata={"account_id": account_id}
            )
    
    @staticmethod
    def is_expired(subscription: Subscription) -> bool:
        """Check if subscription is expired.
        
        Args:
            subscription: Subscription instance
        
        Returns:
            True if expired, False otherwise
        """
        if subscription.status == "expired":
            return True
        
        if subscription.end_date and subscription.end_date < datetime.utcnow():
            return True
        
        return False
    
    @staticmethod
    def is_trial(subscription: Subscription) -> bool:
        """Check if subscription is in trial period.
        
        Args:
            subscription: Subscription instance
        
        Returns:
            True if trial, False otherwise
        """
        if not subscription.is_trial:
            return False
        
        if subscription.trial_end_date and subscription.trial_end_date < datetime.utcnow():
            return False
        
        return True
    
    @staticmethod
    def get_base_features(subscription: Subscription) -> list[str]:
        """Get base features from subscription.
        
        Args:
            subscription: Subscription instance
        
        Returns:
            List of feature keys
        """
        if subscription.features and isinstance(subscription.features, dict):
            return subscription.features.get("base_features", [])
        return []
    
    @staticmethod
    def get_addon_features(subscription: Subscription) -> list[str]:
        """Get addon features from subscription.
        
        Args:
            subscription: Subscription instance
        
        Returns:
            List of addon feature keys
        """
        if subscription.features and isinstance(subscription.features, dict):
            return subscription.features.get("addon_features", [])
        return []
