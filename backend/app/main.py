from fastapi import FastAPI
import logging

from app.observability.logging import configure_logging
from app.api.gateway import router as gateway_router
from app.api.routes.health import router as health_router


# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI(title="ZimPrep API")

# Include routers
app.include_router(health_router)
app.include_router(gateway_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    from app.orchestrator.engine_registry import engine_registry
    
    # Register Identity & Subscription Engine
    engine_registry.register(
        "identity_subscription",
        IdentitySubscriptionEngine()
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Registered identity_subscription engine")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass

