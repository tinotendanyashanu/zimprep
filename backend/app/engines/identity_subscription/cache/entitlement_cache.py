"""Entitlement cache for fast authorization lookups.

Caches entitlement snapshots with TTL and invalidation.
"""

import logging
import json
from typing import Optional

from redis.exceptions import RedisError

from app.engines.identity_subscription.cache.redis_client import get_redis_client
from app.engines.identity_subscription.schemas.output import IdentitySubscriptionOutput
from app.engines.identity_subscription.schemas.input import ActionType
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EntitlementCache:
    """Cache for entitlement snapshots."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.default_ttl = getattr(settings, "IDENTITY_CACHE_TTL_SECONDS", 300)
    
    def _get_key(self, user_id: str, action_type: ActionType) -> str:
        """Generate cache key.
        
        Args:
            user_id: User identifier
            action_type: Action type
        
        Returns:
            Cache key string
        """
        return f"entitlement:{user_id}:{action_type.value}"
    
    async def get(
        self,
        user_id: str,
        action_type: ActionType,
        trace_id: Optional[str] = None
    ) -> Optional[IdentitySubscriptionOutput]:
        """Get cached entitlement.
        
        Args:
            user_id: User identifier
            action_type: Action type
            trace_id: Trace ID for logging
        
        Returns:
            Cached IdentitySubscriptionOutput or None if not found
        """
        key = self._get_key(user_id, action_type)
        
        try:
            data = await self.redis.get(key)
            
            if data is None:
                logger.debug(
                    "Cache miss",
                    extra={
                        "trace_id": trace_id,
                        "user_id": user_id,
                        "action": action_type.value
                    }
                )
                return None
            
            # Deserialize
            output_dict = json.loads(data)
            output = IdentitySubscriptionOutput(**output_dict)
            
            logger.debug(
                "Cache hit",
                extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "action": action_type.value
                }
            )
            
            return output
        
        except (RedisError, json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Cache get failed: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
            return None
    
    async def set(
        self,
        user_id: str,
        action_type: ActionType,
        output: IdentitySubscriptionOutput,
        ttl: Optional[int] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Set cached entitlement.
        
        Args:
            user_id: User identifier
            action_type: Action type
            output: IdentitySubscriptionOutput to cache
            ttl: Time to live in seconds (default from config)
            trace_id: Trace ID for logging
        """
        # Don't cache denied responses
        if not output.allowed:
            logger.debug(
                "Skipping cache for denied response",
                extra={"trace_id": trace_id}
            )
            return
        
        key = self._get_key(user_id, action_type)
        ttl = ttl or self.default_ttl
        
        try:
            # Serialize (use model_dump for Pydantic v2)
            data = json.dumps(output.model_dump())
            
            # Set with TTL
            await self.redis.setex(key, ttl, data)
            
            logger.debug(
                f"Cached entitlement (TTL={ttl}s)",
                extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "action": action_type.value
                }
            )
        
        except (RedisError, TypeError) as e:
            logger.warning(
                f"Cache set failed: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
    
    async def invalidate(
        self,
        user_id: str,
        trace_id: Optional[str] = None
    ) -> None:
        """Invalidate all cached entitlements for user.
        
        Args:
            user_id: User identifier
            trace_id: Trace ID for logging
        """
        pattern = f"entitlement:{user_id}:*"
        
        try:
            # Scan for matching keys
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(
                f"Invalidated {deleted} cache entries",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
        
        except RedisError as e:
            logger.error(
                f"Cache invalidation failed: {e}",
                extra={"trace_id": trace_id, "user_id": user_id}
            )
