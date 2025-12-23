"""Metrics endpoint for Prometheus scraping.

PHASE B5: Exposes metrics in Prometheus format for monitoring.
"""

from fastapi import APIRouter
from fastapi.responses import Response
from app.observability.metrics import get_metrics


router = APIRouter(prefix="/metrics", tags=["observability"])


@router.get("", response_class=Response)
async def metrics_endpoint():
    """Expose Prometheus metrics.
    
    Returns metrics in Prometheus text format for scraping.
    This endpoint should be publicly accessible but can be
    restricted with firewall rules or authentication.
    """
    return Response(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
