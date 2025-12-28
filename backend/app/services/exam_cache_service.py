"""Extended cache service for exam schedules.

Adds caching support for upcoming exams to reduce database load.
"""

import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExamCacheService:
    """Cache service for exam schedules.
    
    Uses in-memory dictionary (can be replaced with Redis in production).
    """
    
    # In-memory cache (replace with Redis for production)
    _cache: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
    
    # Default TTL: 15 minutes (900 seconds)
    DEFAULT_TTL = 900
    
    @classmethod
    def get_cache_key(
        cls,
        candidate_id: str,
        cohort_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> str:
        """Generate cache key for upcoming exams.
        
        Args:
            candidate_id: Candidate ID
            cohort_id: Optional cohort ID
            school_id: Optional school ID
            
        Returns:
            Cache key string
        """
        parts = [f"upcoming_exams:{candidate_id}"]
        if cohort_id:
            parts.append(f"cohort:{cohort_id}")
        if school_id:
            parts.append(f"school:{school_id}")
        return ":".join(parts)
    
    @classmethod
    def get_upcoming_exams_cached(
        cls,
        candidate_id: str,
        cohort_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached upcoming exams.
        
        Args:
            candidate_id: Candidate ID
            cohort_id: Optional cohort ID  
            school_id: Optional school ID
            
        Returns:
            Cached exams list or None if cache miss
        """
        import time
        
        cache_key = cls.get_cache_key(candidate_id, cohort_id, school_id)
        
        if cache_key in cls._cache:
            exams, expiry_time = cls._cache[cache_key]
            
            # Check if expired
            if time.time() < expiry_time:
                logger.info(
                    f"Cache HIT: {cache_key}",
                    extra={"cache_key": cache_key, "num_exams": len(exams)}
                )
                return exams
            else:
                # Expired - remove from cache
                del cls._cache[cache_key]
                logger.info(
                    f"Cache EXPIRED: {cache_key}",
                    extra={"cache_key": cache_key}
                )
        
        logger.info(
            f"Cache MISS: {cache_key}",
            extra={"cache_key": cache_key}
        )
        return None
    
    @classmethod
    def set_upcoming_exams_cache(
        cls,
        candidate_id: str,
        cohort_id: Optional[str],
        school_id: Optional[str],
        exams: List[Dict[str, Any]],
        ttl: int = DEFAULT_TTL
    ) -> None:
        """Cache upcoming exams.
        
        Args:
            candidate_id: Candidate ID
            cohort_id: Optional cohort ID
            school_id: Optional school ID
            exams: List of upcoming exams
            ttl: Time-to-live in seconds (default: 900 = 15 minutes)
        """
        import time
        
        cache_key = cls.get_cache_key(candidate_id, cohort_id, school_id)
        expiry_time = time.time() + ttl
        
        cls._cache[cache_key] = (exams, expiry_time)
        
        logger.info(
            f"Cache SET: {cache_key}",
            extra={
                "cache_key": cache_key,
                "num_exams": len(exams),
                "ttl_seconds": ttl
            }
        )
    
    @classmethod
    def invalidate_upcoming_exams_cache(
        cls,
        candidate_id: Optional[str] = None,
        cohort_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> int:
        """Invalidate cache for upcoming exams.
        
        Args:
            candidate_id: If provided, invalidate for this candidate only
            cohort_id: If provided, invalidate for this cohort
            school_id: If provided, invalidate for this school
            
        Returns:
            Number of cache entries invalidated
        """
        count = 0
        keys_to_delete = []
        
        # Find matching cache keys
        for cache_key in list(cls._cache.keys()):
            should_invalidate = False
            
            if candidate_id and f"upcoming_exams:{candidate_id}" in cache_key:
                should_invalidate = True
            elif cohort_id and f"cohort:{cohort_id}" in cache_key:
                should_invalidate = True
            elif school_id and f"school:{school_id}" in cache_key:
                should_invalidate = True
            elif not candidate_id and not cohort_id and not school_id:
                # Invalidate all if no filters provided
                should_invalidate = True
            
            if should_invalidate:
                keys_to_delete.append(cache_key)
        
        # Delete found keys
        for key in keys_to_delete:
            del cls._cache[key]
            count += 1
        
        logger.info(
            f"Cache INVALIDATED: {count} entries",
            extra={
                "candidate_id": candidate_id,
                "cohort_id": cohort_id,
                "school_id": school_id,
                "count": count
            }
        )
        
        return count
    
    @classmethod
    def clear_all_cache(cls) -> int:
        """Clear all cached upcoming exams.
        
        Returns:
            Number of entries cleared
        """
        count = len(cls._cache)
        cls._cache.clear()
        logger.info(f"Cache CLEARED: {count} entries total")
        return count
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        import time
        
        total_entries = len(cls._cache)
        active_entries = 0
        expired_entries = 0
        
        for exams, expiry_time in cls._cache.values():
            if time.time() < expiry_time:
                active_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_type": "in_memory",  # Can be "redis" in production
        }


# Production Redis implementation (commented out)
"""
import redis
from redis import Redis

class RedisCacheService:
    def __init__(self):
        self.redis_client: Redis = redis.from_url(settings.REDIS_URL)
    
    async def get_upcoming_exams_cached(
        self,
        candidate_id: str,
        cohort_id: Optional[str] = None,
        school_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        cache_key = ExamCacheService.get_cache_key(candidate_id, cohort_id, school_id)
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            logger.info(f"Redis Cache HIT: {cache_key}")
            return json.loads(cached_data)
        
        logger.info(f"Redis Cache MISS: {cache_key}")
        return None
    
    async def set_upcoming_exams_cache(
        self,
        candidate_id: str,
        cohort_id: Optional[str],
        school_id: Optional[str],
        exams: List[Dict[str, Any]],
        ttl: int = 900
    ) -> None:
        cache_key = ExamCacheService.get_cache_key(candidate_id, cohort_id, school_id)
        self.redis_client.setex(cache_key, ttl, json.dumps(exams))
        logger.info(f"Redis Cache SET: {cache_key}, TTL: {ttl}s")
    
    async def invalidate_upcoming_exams_cache(
        self,
        candidate_id: Optional[str] = None
    ) -> int:
        pattern = f"upcoming_exams:{candidate_id}:*" if candidate_id else "upcoming_exams:*"
        keys = self.redis_client.keys(pattern)
        
        if keys:
            count = self.redis_client.delete(*keys)
            logger.info(f"Redis Cache INVALIDATED: {count} keys")
            return count
        
        return 0
"""
