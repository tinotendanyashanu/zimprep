"""Cost tracking service for AI usage monitoring.

Tracks cumulative costs per user and school, enforces limits.
"""

import logging
from datetime import datetime, timedelta
from typing import Literal

from app.engines.ai.ai_routing_cost_control.schemas.decision import CostPolicy
from app.engines.ai.ai_routing_cost_control.errors import CostLimitExceededError

logger = logging.getLogger(__name__)


class CostTracker:
    """Service for tracking AI usage costs and enforcing limits.
    
    Tracks:
    - Per-user daily/monthly costs
    - Per-school monthly costs
    - Enforces limits with graceful degradation (queue vs hard fail)
    """
    
    def __init__(self, mongodb_client=None):
        """Initialize cost tracker with MongoDB client.
        
        Args:
            mongodb_client: MongoDB client for persistent cost storage
        """
        self.mongodb_client = mongodb_client
        self.tracking_enabled = mongodb_client is not None
    
    async def get_user_cost_today(self, user_id: str) -> float:
        """Get user's cumulative cost today in USD.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cumulative cost in USD
        """
        if not self.tracking_enabled:
            return 0.0
        
        try:
            # Access ai_cost_tracking collection
            db = self.mongodb_client.zimprep
            collection = db.ai_cost_tracking
            
            # Get today's date range
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            # Aggregate costs for today
            result = await collection.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": today_start}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$cost_usd"}
                    }
                }
            ]).to_list(1)
            
            return result[0]["total"] if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get user cost today: {e}")
            return 0.0
    
    async def get_user_cost_month(self, user_id: str) -> float:
        """Get user's cumulative cost this month in USD.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cumulative cost in USD
        """
        if not self.tracking_enabled:
            return 0.0
        
        try:
            # Access ai_cost_tracking collection
            db = self.mongodb_client.zimprep
            collection = db.ai_cost_tracking
            
            # Get current month range
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Aggregate costs for current month
            result = await collection.aggregate([
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": month_start}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$cost_usd"}
                    }
                }
            ]).to_list(1)
            
            return result[0]["total"] if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get user cost month: {e}")
            return 0.0
    
    async def get_school_cost_month(self, school_id: str) -> float:
        """Get school's cumulative cost this month in USD.
        
        Args:
            school_id: School identifier
            
        Returns:
            Cumulative cost in USD
        """
        if not self.tracking_enabled:
            return 0.0
        
        try:
            # Access ai_cost_tracking collection
            db = self.mongodb_client.zimprep
            collection = db.ai_cost_tracking
            
            # Get current month range
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Aggregate costs for current month
            result = await collection.aggregate([
                {
                    "$match": {
                        "school_id": school_id,
                        "timestamp": {"$gte": month_start}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$cost_usd"}
                    }
                }
            ]).to_list(1)
            
            return result[0]["total"] if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get school cost month: {e}")
            return 0.0
    
    async def record_usage(
        self,
        user_id: str,
        school_id: str,
        request_type: str,
        model: str,
        cost_usd: float,
        trace_id: str
    ):
        """Record AI usage for cost tracking.
        
        Args:
            user_id: User identifier
            school_id: School identifier
            request_type: Type of AI request
            model: Model used
            cost_usd: Estimated cost in USD
            trace_id: Trace ID for audit trail
        """
        if not self.tracking_enabled:
            logger.debug(f"[{trace_id}] Cost tracking disabled, skipping")
            return
        
        usage_record = {
            "trace_id": trace_id,
            "user_id": user_id,
            "school_id": school_id,
            "request_type": request_type,
            "model": model,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow(),
        }
        
        logger.info(
            f"[{trace_id}] Recording usage: user={user_id}, "
            f"model={model}, cost=${cost_usd:.4f}"
        )
        
        # Insert into MongoDB
        try:
            db = self.mongodb_client.zimprep
            collection = db.ai_cost_tracking
            await collection.insert_one(usage_record)
        except Exception as e:
            logger.error(f"[{trace_id}] Failed to record usage: {e}")
    
    async def check_limits(
        self,
        user_id: str,
        school_id: str,
        estimated_cost: float,
        cost_policy: CostPolicy,
        trace_id: str
    ) -> tuple[bool, str]:
        """Check if request would exceed cost limits.
        
        Args:
            user_id: User identifier
            school_id: School identifier
            estimated_cost: Estimated cost for this request
            cost_policy: Cost policy with limits
            trace_id: Trace ID for logging
            
        Returns:
            Tuple of (within_limits, reason)
            - within_limits: True if request is within limits
            - reason: Human-readable reason if limits exceeded
        """
        # Emergency kill switch
        if cost_policy.emergency_kill_switch:
            logger.warning(f"[{trace_id}] Emergency kill switch activated")
            return (False, "Emergency cost control activated - all AI requests queued")
        
        # Check user daily limit
        user_cost_today = await self.get_user_cost_today(user_id)
        if user_cost_today + estimated_cost > cost_policy.daily_limit_usd:
            logger.warning(
                f"[{trace_id}] User daily limit exceeded: "
                f"${user_cost_today:.2f} + ${estimated_cost:.2f} > ${cost_policy.daily_limit_usd:.2f}"
            )
            return (
                False,
                f"Daily cost limit exceeded (${user_cost_today:.2f}/${cost_policy.daily_limit_usd:.2f})"
            )
        
        # Check user monthly limit
        user_cost_month = await self.get_user_cost_month(user_id)
        if user_cost_month + estimated_cost > cost_policy.monthly_limit_usd:
            logger.warning(
                f"[{trace_id}] User monthly limit exceeded: "
                f"${user_cost_month:.2f} + ${estimated_cost:.2f} > ${cost_policy.monthly_limit_usd:.2f}"
            )
            return (
                False,
                f"Monthly cost limit exceeded (${user_cost_month:.2f}/${cost_policy.monthly_limit_usd:.2f})"
            )
        
        # Check school monthly limit
        school_cost_month = await self.get_school_cost_month(school_id)
        if school_cost_month + estimated_cost > cost_policy.school_monthly_limit_usd:
            logger.warning(
                f"[{trace_id}] School monthly limit exceeded: "
                f"${school_cost_month:.2f} + ${estimated_cost:.2f} > ${cost_policy.school_monthly_limit_usd:.2f}"
            )
            return (
                False,
                f"School monthly limit exceeded (${school_cost_month:.2f}/${cost_policy.school_monthly_limit_usd:.2f})"
            )
        
        # Within all limits
        return (True, "Within cost limits")
    
    async def get_remaining_budget(
        self,
        user_id: str,
        school_id: str,
        cost_policy: CostPolicy
    ) -> dict[str, float]:
        """Get remaining cost budget for user and school.
        
        Args:
            user_id: User identifier
            school_id: School identifier
            cost_policy: Cost policy with limits
            
        Returns:
            Dict with remaining budgets
        """
        user_cost_today = await self.get_user_cost_today(user_id)
        user_cost_month = await self.get_user_cost_month(user_id)
        school_cost_month = await self.get_school_cost_month(school_id)
        
        return {
            "daily_remaining": cost_policy.daily_limit_usd - user_cost_today,
            "monthly_remaining": cost_policy.monthly_limit_usd - user_cost_month,
            "school_monthly_remaining": cost_policy.school_monthly_limit_usd - school_cost_month,
        }
