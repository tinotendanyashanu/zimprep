"""Cache service for AI routing decisions.

Manages cache lookup and storage across Redis (hot) and MongoDB (persistent).
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

from app.engines.ai.ai_routing_cost_control.schemas.decision import CacheDecision
from app.engines.ai.ai_routing_cost_control.errors import CacheServiceUnavailableError

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching AI results to avoid redundant expensive API calls.
    
    Cache Strategy:
    - Hot cache: Redis (TTL: 24 hours, fast access)
    - Persistent cache: MongoDB (long-term, slower access)
    - Cache key: SHA-256(prompt_hash + evidence_hash + syllabus_version)
    
    Cache Invalidation:
    - Syllabus update invalidates all cached results for that subject
    - TTL expiration (24 hours for Redis)
    """
    
    REDIS_TTL_SECONDS = 24 * 60 * 60  # 24 hours
    
    def __init__(self, redis_client=None, mongodb_client=None):
        """Initialize cache service with Redis and MongoDB clients.
        
        Args:
            redis_client: Redis client (optional, cache disabled if None)
            mongodb_client: MongoDB client (optional, persistent cache disabled if None)
        """
        self.redis_client = redis_client
        self.mongodb_client = mongodb_client
        self.cache_enabled = redis_client is not None or mongodb_client is not None
    
    def generate_cache_key(
        self,
        prompt_hash: str,
        evidence_hash: str,
        syllabus_version: str
    ) -> str:
        """Generate cache key from request parameters.
        
        Cache key = SHA-256(prompt_hash + evidence_hash + syllabus_version)
        
        This ensures:
        - Same question + same evidence + same syllabus = cache hit
        - Different evidence = cache miss (evidence changed)
        - Different syllabus = cache miss (syllabus updated)
        
        Args:
            prompt_hash: SHA-256 hash of AI prompt
            evidence_hash: SHA-256 hash of evidence/context
            syllabus_version: Syllabus version identifier
            
        Returns:
            SHA-256 cache key (64 hex characters)
        """
        combined = f"{prompt_hash}:{evidence_hash}:{syllabus_version}"
        cache_key = hashlib.sha256(combined.encode()).hexdigest()
        
        logger.debug(f"Generated cache key: {cache_key[:16]}... from {combined[:50]}...")
        return cache_key
    
    async def lookup(self, cache_key: str, trace_id: str) -> CacheDecision:
        """Look up cached result.
        
        Search order:
        1. Redis (hot cache, fast)
        2. MongoDB (persistent cache, slower)
        3. Cache miss
        
        Args:
            cache_key: Cache key to look up
            trace_id: Trace ID for logging
            
        Returns:
            CacheDecision with cache hit status and cached data
        """
        if not self.cache_enabled:
            logger.debug(f"[{trace_id}] Cache disabled, returning cache miss")
            return CacheDecision(
                cache_hit=False,
                cache_key=cache_key,
                cache_source="none"
            )
        
        # Try Redis first (hot cache)
        if self.redis_client:
            try:
                cached_value = await self._lookup_redis(cache_key)
                if cached_value:
                    logger.info(f"[{trace_id}] Cache HIT (Redis): {cache_key[:16]}...")
                    return CacheDecision(
                        cache_hit=True,
                        cache_key=cache_key,
                        cached_at=cached_value.get("cached_at"),
                        cache_source="redis"
                    )
            except Exception as e:
                logger.warning(f"[{trace_id}] Redis lookup failed: {str(e)}")
        
        # Try MongoDB (persistent cache)
        if self.mongodb_client:
            try:
                cached_value = await self._lookup_mongodb(cache_key)
                if cached_value:
                    logger.info(f"[{trace_id}] Cache HIT (MongoDB): {cache_key[:16]}...")
                    # Promote to Redis for faster future access
                    if self.redis_client:
                        await self._store_redis(cache_key, cached_value)
                    
                    return CacheDecision(
                        cache_hit=True,
                        cache_key=cache_key,
                        cached_at=cached_value.get("cached_at"),
                        cache_source="mongodb"
                    )
            except Exception as e:
                logger.warning(f"[{trace_id}] MongoDB lookup failed: {str(e)}")
        
        # Cache miss
        logger.info(f"[{trace_id}] Cache MISS: {cache_key[:16]}...")
        return CacheDecision(
            cache_hit=False,
            cache_key=cache_key,
            cache_source="none"
        )
    
    async def store(
        self,
        cache_key: str,
        result: dict[str, Any],
        trace_id: str
    ):
        """Store AI result in cache.
        
        Stores in both Redis (hot) and MongoDB (persistent).
        
        Args:
            cache_key: Cache key
            result: AI execution result to cache
            trace_id: Trace ID for logging
        """
        if not self.cache_enabled:
            logger.debug(f"[{trace_id}] Cache disabled, skipping storage")
            return
        
        cached_value = {
            "result": result,
            "cached_at": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
        }
        
        # Store in Redis (hot cache)
        if self.redis_client:
            try:
                await self._store_redis(cache_key, cached_value)
                logger.info(f"[{trace_id}] Stored in Redis: {cache_key[:16]}...")
            except Exception as e:
                logger.error(f"[{trace_id}] Redis storage failed: {str(e)}")
        
        # Store in MongoDB (persistent cache)
        if self.mongodb_client:
            try:
                await self._store_mongodb(cache_key, cached_value)
                logger.info(f"[{trace_id}] Stored in MongoDB: {cache_key[:16]}...")
            except Exception as e:
                logger.error(f"[{trace_id}] MongoDB storage failed: {str(e)}")
    
    async def invalidate_by_syllabus(self, syllabus_version: str):
        """Invalidate all cached results for a syllabus version.
        
        Called when syllabus is updated to ensure fresh marking.
        
        Args:
            syllabus_version: Syllabus version to invalidate
        """
        logger.warning(f"Invalidating cache for syllabus: {syllabus_version}")
        
        # For now, this is a placeholder. In production, you would:
        # 1. Store syllabus_version in cache entries
        # 2. Query MongoDB for all entries with that syllabus_version
        # 3. Delete them  from both Redis and MongoDB
        
        # This is a critical feature for legal defensibility
        pass
    
    async def _lookup_redis(self, cache_key: str) -> dict[str, Any] | None:
        """Look up value in Redis (not implemented - placeholder)."""
        # Placeholder: In production, implement Redis lookup
        # import redis.asyncio as redis
        # value = await self.redis_client.get(f"ai_cache:{cache_key}")
        # if value:
        #     return json.loads(value)
        return None
    
    async def _store_redis(self, cache_key: str, value: dict[str, Any]):
        """Store value in Redis (not implemented - placeholder)."""
        # Placeholder: In production, implement Redis storage
        # import json
        # await self.redis_client.setex(
        #     f"ai_cache:{cache_key}",
        #     self.REDIS_TTL_SECONDS,
        #     json.dumps(value)
        # )
        pass
    
    async def _lookup_mongodb(self, cache_key: str) -> dict[str, Any] | None:
        """Look up value in MongoDB (not implemented - placeholder)."""
        # Placeholder: In production, implement MongoDB lookup
        # collection = self.mongodb_client.ai_routing_cache
        # doc = await collection.find_one({"cache_key": cache_key})
        # if doc:
        #     return doc.get("cached_value")
        return None
    
    async def _store_mongodb(self, cache_key: str, value: dict[str, Any]):
        """Store value in MongoDB (not implemented - placeholder)."""
        # Placeholder: In production, implement MongoDB storage
        # collection = self.mongodb_client.ai_routing_cache
        # await collection.update_one(
        #     {"cache_key": cache_key},
        #     {"$set": {"cached_value": value, "updated_at": datetime.utcnow()}},
        #     upsert=True
        # )
        pass
