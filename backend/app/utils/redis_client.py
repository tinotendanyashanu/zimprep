"""Redis connection with graceful degradation.

Provides Redis client that gracefully degrades when Redis is unavailable.
Features are disabled rather than causing crashes.
"""

from typing import Optional, Any
import structlog
from redis import asyncio as aioredis
from app.config.settings import settings

logger = structlog.get_logger(__name__)


class GracefulRedisClient:
    """Redis client wrapper with graceful degradation.
    
    When Redis is unavailable:
    - get() returns None
    - set() is ignored
    - delete() is ignored
    - Operations log warnings but don't raise exceptions
    """
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._available = False
        self._connection_attempted = False
    
    async def connect(self) -> bool:
        """Attempt to connect to Redis.
        
        Returns:
            True if connected, False if unavailable
        """
        if self._connection_attempted:
            return self._available
        
        self._connection_attempted = True
        
        try:
            self._client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            await self._client.ping()
            self._available = True
            logger.info("✓ Redis connected successfully")
            return True
        except Exception as e:
            logger.warning(
                "Redis unavailable - running in degraded mode",
                error=str(e)
            )
            self._available = False
            self._client = None
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis.
        
        Returns None if Redis unavailable or key not found.
        """
        if not self._available:
            await self.connect()
        
        if not self._available:
            return None
        
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None
    ) -> bool:
        """Set value in Redis.
        
        Returns True if set, False if Redis unavailable.
        """
        if not self._available:
            await self.connect()
        
        if not self._available:
            logger.debug(f"Skipping Redis set (unavailable): {key}")
            return False
        
        try:
            await self._client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis.
        
        Returns True if deleted, False if Redis unavailable.
        """
        if not self._available:
            return False
        
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._available = False


# Global Redis client instance
redis_client = GracefulRedisClient()
