"""Idempotency policy for safe job re-execution.

Ensures jobs can be safely re-executed without side effects.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.engines.background_processing.schemas.output import JobOutput

logger = logging.getLogger(__name__)


class IdempotencyPolicy:
    """Enforces idempotent job execution.
    
    Features:
    - Duplicate job_id detection
    - Cached result retrieval for duplicate jobs
    - Time-based cache expiration
    - Safe re-execution guarantees
    
    Note:
        This is a reference in-memory implementation. Production systems
        should use distributed caching (Redis) for multi-instance deployments.
    """
    
    def __init__(self, cache_ttl_seconds: int = 3600):
        """Initialize idempotency policy.
        
        Args:
            cache_ttl_seconds: Time-to-live for cached results (default: 1 hour)
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self._result_cache: Dict[str, tuple[JobOutput, datetime]] = {}
        
        logger.info(f"Idempotency policy initialized (TTL={cache_ttl_seconds}s)")
    
    async def check_duplicate(self, job_id: str, trace_id: str) -> Optional[JobOutput]:
        """Check if job has already been executed.
        
        Args:
            job_id: Job ID to check
            trace_id: Trace ID for logging
            
        Returns:
            Cached JobOutput if job already executed, None otherwise
        """
        # Clean expired cache entries
        self._clean_expired_cache()
        
        if job_id in self._result_cache:
            cached_output, cached_at = self._result_cache[job_id]
            
            logger.info(
                f"Duplicate job detected: {job_id}",
                extra={
                    "trace_id": trace_id,
                    "job_id": job_id,
                    "cached_at": cached_at.isoformat(),
                    "cached_status": cached_output.status.value
                }
            )
            
            return cached_output
        
        return None
    
    async def cache_result(
        self,
        job_id: str,
        job_output: JobOutput,
        trace_id: str
    ) -> None:
        """Cache job execution result.
        
        Args:
            job_id: Job ID
            job_output: Job execution output
            trace_id: Trace ID for logging
        """
        self._result_cache[job_id] = (job_output, datetime.utcnow())
        
        logger.debug(
            f"Job result cached: {job_id}",
            extra={
                "trace_id": trace_id,
                "job_id": job_id,
                "status": job_output.status.value,
                "cache_size": len(self._result_cache)
            }
        )
    
    def _clean_expired_cache(self) -> None:
        """Remove expired cache entries.
        
        Called before each duplicate check to prevent unbounded growth.
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=self.cache_ttl_seconds)
        
        # Find expired entries
        expired_keys = [
            job_id for job_id, (_, cached_at) in self._result_cache.items()
            if cached_at < cutoff_time
        ]
        
        # Remove expired entries
        for job_id in expired_keys:
            del self._result_cache[job_id]
        
        if expired_keys:
            logger.debug(
                f"Cleaned {len(expired_keys)} expired cache entries",
                extra={"cache_size": len(self._result_cache)}
            )
    
    async def invalidate(self, job_id: str, trace_id: str) -> None:
        """Manually invalidate cached result for a job.
        
        Args:
            job_id: Job ID to invalidate
            trace_id: Trace ID for logging
        """
        if job_id in self._result_cache:
            del self._result_cache[job_id]
            
            logger.info(
                f"Cache invalidated for job: {job_id}",
                extra={"trace_id": trace_id, "job_id": job_id}
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=self.cache_ttl_seconds)
        
        valid_entries = sum(
            1 for _, (_, cached_at) in self._result_cache.items()
            if cached_at >= cutoff_time
        )
        
        return {
            "total_entries": len(self._result_cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._result_cache) - valid_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }
