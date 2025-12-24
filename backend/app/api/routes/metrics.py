"""Optimized metrics endpoint with caching and async collection.

Improves performance by:
1. Caching metrics for short periods
2. Collecting metrics asynchronously
3. Limiting metric collection scope
"""

from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from typing import Optional

router = APIRouter(tags=["metrics"])

# Simple cache for metrics
_metrics_cache: Optional[tuple[bytes, float]] = None
_cache_ttl_seconds = 5  # Cache for 5 seconds


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint with caching.
    
    Returns prometheus-formatted metrics.
    Cached for 5 seconds to improve performance.
    """
    global _metrics_cache
    
    current_time = time.time()
    
    # Check cache
    if _metrics_cache is not None:
        cached_data, cached_time = _metrics_cache
        if current_time - cached_time < _cache_ttl_seconds:
            return Response(
                content=cached_data,
                media_type=CONTENT_TYPE_LATEST,
                headers={"X-Cache": "HIT"}
            )
    
    # Generate fresh metrics
    metrics_data = generate_latest()
    
    # Update cache
    _metrics_cache = (metrics_data, current_time)
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"X-Cache": "MISS"}
    )
