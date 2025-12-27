"""Rate limiting service for external API access.

Implements per-key, per-endpoint, and burst rate limiting using Redis.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.engines.identity_subscription.cache.redis_client import get_redis_client


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting enforcement for external API keys."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.redis = get_redis_client()
    
    async def check_rate_limit(
        self,
        api_key_id: str,
        endpoint: str,
        requests_per_hour: int,
        requests_per_minute: int,
        burst_limit: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Check if request should be rate limited.
        
        Args:
            api_key_id: API key identifier
            endpoint: Endpoint being accessed
            requests_per_hour: Hourly limit
            requests_per_minute: Per-minute limit
            burst_limit: Burst limit (10 second window)
            
        Returns:
            Tuple of (allowed, remaining_requests, violation_reason)
        """
        # Check burst limit (10 seconds)
        burst_allowed, burst_remaining = await self._check_window(
            key=f"rate:burst:{api_key_id}:{endpoint}",
            limit=burst_limit,
            window_seconds=10
        )
        
        if not burst_allowed:
            logger.warning(
                f"Burst limit exceeded for {api_key_id} on {endpoint}: "
                f"{burst_limit} requests in 10s"
            )
            return False, 0, "burst_limit_exceeded"
        
        # Check per-minute limit
        minute_allowed, minute_remaining = await self._check_window(
            key=f"rate:minute:{api_key_id}:{endpoint}",
            limit=requests_per_minute,
            window_seconds=60
        )
        
        if not minute_allowed:
            logger.warning(
                f"Per-minute limit exceeded for {api_key_id} on {endpoint}: "
                f"{requests_per_minute} requests/min"
            )
            return False, 0, "per_minute_limit_exceeded"
        
        # Check per-hour limit
        hour_allowed, hour_remaining = await self._check_window(
            key=f"rate:hour:{api_key_id}",
            limit=requests_per_hour,
            window_seconds=3600
        )
        
        if not hour_allowed:
            logger.warning(
                f"Per-hour limit exceeded for {api_key_id}: "
                f"{requests_per_hour} requests/hour"
            )
            return False, 0, "per_hour_limit_exceeded"
        
        # All limits passed - increment counters
        await self._increment_counter(
            f"rate:burst:{api_key_id}:{endpoint}",
            window_seconds=10
        )
        await self._increment_counter(
            f"rate:minute:{api_key_id}:{endpoint}",
            window_seconds=60
        )
        await self._increment_counter(
            f"rate:hour:{api_key_id}",
            window_seconds=3600
        )
        
        # Return most restrictive remaining count
        remaining = min(burst_remaining, minute_remaining, hour_remaining)
        
        return True, remaining, None
    
    async def _check_window(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """Check if request count is within limit for a time window.
        
        Args:
            key: Redis key for this limit
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, remaining_requests)
        """
        try:
            # Get current count
            count = await self.redis.get(key)
            current_count = int(count) if count else 0
            
            # Check if within limit
            if current_count >= limit:
                return False, 0
            
            remaining = limit - current_count
            return True, remaining
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {key}: {e}")
            # Fail open on Redis errors (don't block legitimate traffic)
            return True, limit
    
    async def _increment_counter(self, key: str, window_seconds: int) -> None:
        """Increment counter and set expiration.
        
        Args:
            key: Redis key
            window_seconds: Time window for expiration
        """
        try:
            # Increment counter
            await self.redis.incr(key)
            
            # Set expiration if this is the first increment
            ttl = await self.redis.ttl(key)
            if ttl == -1:  # No expiration set
                await self.redis.expire(key, window_seconds)
                
        except Exception as e:
            logger.error(f"Failed to increment counter {key}: {e}")
    
    async def reset_limits(self, api_key_id: str) -> None:
        """Reset all rate limits for an API key (emergency use only).
        
        Args:
            api_key_id: API key identifier
        """
        try:
            # Delete all rate limit keys for this API key
            pattern = f"rate:*:{api_key_id}*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.warning(f"Reset all rate limits for API key: {api_key_id}")
                
        except Exception as e:
            logger.error(f"Failed to reset rate limits for {api_key_id}: {e}")
