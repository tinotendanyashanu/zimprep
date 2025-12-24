"""Health and readiness check endpoints.

Separate endpoints for liveness and readiness:
- /health: Always responds if process is alive (for K8s liveness probes)
- /readiness: Responds only if all dependencies are ready (for K8s readiness probes)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import time

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: float


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""
    status: str
    timestamp: float
    dependencies: Dict[str, bool]
    message: str | None = None


# Global readiness state (updated by startup events)
_readiness_state = {
    "engines_registered": False,
    "mongodb_connected": False,
    "ready": False
}


def set_readiness(engines: bool = False, mongodb: bool = False):
    """Update readiness state."""
    global _readiness_state
    if engines is not None:
        _readiness_state["engines_registered"] = engines
    if mongodb is not None:
        _readiness_state["mongodb_connected"] = mongodb
    
    # System is ready if engines are registered (MongoDB is optional for some operations)
    _readiness_state["ready"] = _readiness_state["engines_registered"]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe - always responds if process is alive.
    
    This endpoint MUST respond quickly even if dependencies are down.
    Used by Kubernetes liveness probes.
    """
    return HealthResponse(
        status="healthy",
        timestamp=time.time()
    )


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness probe - responds only if system can handle requests.
    
    Checks:
    - Engines registered
    - Database connectivity (optional warning)
    
    Returns 503 if not ready.
    """
    if not _readiness_state["ready"]:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": time.time(),
                "dependencies": _readiness_state,
                "message": "System is still initializing"
            }
        )
    
    # Warn if MongoDB is unavailable but allow operation
    message = None
    if not _readiness_state["mongodb_connected"]:
        message = "MongoDB unavailable - some features may be limited"
    
    return ReadinessResponse(
        status="ready",
        timestamp=time.time(),
        dependencies=_readiness_state,
        message=message
    )
