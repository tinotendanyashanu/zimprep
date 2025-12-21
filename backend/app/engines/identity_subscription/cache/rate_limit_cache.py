"""Rate limit cache for tracking usage.

Uses Redis sorted sets for sliding window rate limiting.
"""

import logging
import time
from typing import Optional

from redis.exceptions import RedisError

from app.engines.identity_subscription.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitCache:
    """Redis-based rate limiter using sliding window."""
    
    def __init__(self):
        self.redis = get_redis_client()
    
    def _get_key(self, user_id: str, action_type: str) -> str:
        """Generate Redis key for user action.
        
        Args:
            user_id: User identifier
            action_type: Action type identifier
        
        Returns:
            Redis key string
        """
        return f"ratelimit:{user_id}:{action_type}"
    
    async def increment(
        self,
        user_id: str,
        action_type: str,
        window_seconds: int = 86400,
        trace_id: Optional[str] = None
    ) -> int:
        """Increment usage counter for user action.
        
        Args:
            user_id: User identifier
            action_type: Action type identifier
            window_seconds: Time window in seconds
            trace_id: Trace ID for logging
        
        Returns:
            New usage count
        """
        key = self._get_key(user_id, action_type)
        now = time.time()
        
        try:
            # Add current timestamp to sorted set
            await self.redis.zadd(key, {str(now): now})
            
            # Remove entries outside time window
            cutoff = now - window_seconds
            await self.redis.zremrangebyscore(key, 0, cutoff)
            
            # Set expiration to window + buffer
            await self.redis.expire(key, window_seconds + 3600)
            
            # Get count
            count = await self.redis.zcard(key)
            
            logger.debug(
                f"Rate limit incremented: {action_type} = {count}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
            
            return count
        
        except RedisError as e:
            logger.error(
                f"Failed to increment rate limit: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
            # Cache failure is non-fatal, return 0
            return 0
    
    async def get_usage(
        self,
        user_id: str,
        action_type: str,
        window_seconds: int = 86400,
        trace_id: Optional[str] = None
    ) -> int:
        """Get current usage count for user action.
        
        Args:
            user_id: User identifier
            action_type: Action type identifier
            window_seconds: Time window in seconds
            trace_id: Trace ID for logging
        
        Returns:
            Usage count in time window
        """
        key = self._get_key(user_id, action_type)
        now = time.time()
        
        try:
            # Remove entries outside time window
            cutoff = now - window_seconds
            await self.redis.zremrangebyscore(key, 0, cutoff)
            
            # Get count
            count = await self.redis.zcard(key)
            
            return count
        
        except RedisError as e:
            logger.error(
                f"Failed to get rate limit usage: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
            # Cache failure is non-fatal, return 0 (allow action)
            return 0
    
    async def reset(
        self,
        user_id: str,
        action_type: str,
        trace_id: Optional[str] = None
    ) -> None:
        """Reset usage counter for user action.
        
        Args:
            user_id: User identifier
            action_type: Action type identifier
            trace_id: Trace ID for logging
        """
        key = self._get_key(user_id, action_type)
        
        try:
            await self.redis.delete(key)
            
            logger.info(
                f"Rate limit reset: {action_type}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
        
        except RedisError as e:
            logger.error(
                f"Failed to reset rate limit: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
