"""Redis client for caching.

Provides async Redis connection with error handling.
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client.
    
    Returns:
        Redis client instance
    """
    global _redis_client
    
    if _redis_client is None:
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        logger.info(f"Redis client created: {redis_url}")
    
    return _redis_client


async def close_redis():
    """Close Redis client (cleanup on shutdown)."""
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


async def ping_redis() -> bool:
    """Check Redis connectivity.
    
    Returns:
        True if Redis is accessible, False otherwise
    """
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except RedisError as e:
        logger.warning(f"Redis ping failed: {e}")
        return False
