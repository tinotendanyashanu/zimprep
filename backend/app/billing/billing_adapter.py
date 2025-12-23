"""Billing adapter for handling payment provider webhooks.

This adapter processes subscription lifecycle events from payment providers
(e.g., Stripe) and updates subscription records. It is FULLY DECOUPLED from
pipelines and engines.

CRITICAL RULES:
- Billing NEVER touches pipelines
- Billing NEVER calls engines directly
- Billing only updates subscription database records
- Entitlements are resolved at request time, not billing time
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BillingAdapter:
    """Handles payment provider webhooks and subscription updates."""
    
    async def handle_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment provider webhook event.
        
        Args:
            event: Webhook event data from payment provider
            
        Returns:
            Processing result with status
            
        Raises:
            ValueError: If event type is unknown
        """
        event_type = event.get("type")
        
        logger.info(f"Processing billing webhook: {event_type}")
        
        if event_type == "payment_success":
            return await self._handle_payment_success(event)
        elif event_type == "payment_failed":
            return await self._handle_payment_failed(event)
        elif event_type == "subscription_cancelled":
            return await self._handle_subscription_cancelled(event)
        elif event_type == "trial_started":
            return await self._handle_trial_started(event)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            raise ValueError(f"Unknown event type: {event_type}")
    
    async def _handle_payment_success(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment - upgrade tier.
        
        Args:
            event: Payment success event
            
        Returns:
            Processing result
        """
        user_id = event.get("user_id")
        new_tier = event.get("tier")
        
        logger.info(f"Payment success for user {user_id}, tier: {new_tier}")
        
        # TODO: Update subscription record in database
        # subscription_repo.update_tier(user_id, new_tier)
        
        return {
            "status": "processed",
            "action": "tier_upgraded",
            "user_id": user_id,
            "new_tier": new_tier
        }
    
    async def _handle_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment - downgrade or suspend.
        
        Args:
            event: Payment failure event
            
        Returns:
            Processing result
        """
        user_id = event.get("user_id")
        
        logger.warning(f"Payment failed for user {user_id}")
        
        # TODO: Suspend subscription
        # subscription_repo.suspend(user_id)
        
        return {
            "status": "processed",
            "action": "subscription_suspended",
            "user_id": user_id
        }
    
    async def _handle_subscription_cancelled(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation.
        
        Args:
            event: Cancellation event
            
        Returns:
            Processing result
        """
        user_id = event.get("user_id")
        
        logger.info(f"Subscription cancelled for user {user_id}")
        
        # TODO: Update subscription status
        # subscription_repo.cancel(user_id)
        
        return {
            "status": "processed",
            "action": "subscription_cancelled",
            "user_id": user_id
        }
    
    async def _handle_trial_started(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trial start.
        
        Args:
            event: Trial start event
            
        Returns:
            Processing result
        """
        user_id = event.get("user_id")
        tier = event.get("tier", "student_plus")
        
        logger.info(f"Trial started for user {user_id}, tier: {tier}")
        
        # TODO: Create trial subscription
        # subscription_repo.create_trial(user_id, tier)
        
        return {
            "status": "processed",
            "action": "trial_created",
            "user_id": user_id,
            "tier": tier
        }
