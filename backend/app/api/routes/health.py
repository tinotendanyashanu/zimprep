from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "zimprep-api"
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ZimPrep API",
        "version": "1.0.0",
        "docs": "/docs"
    }
