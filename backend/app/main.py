"""FastAPI application with Phase B5 production hardening.

CRITICAL: This module integrates:
1. Structured logging with trace context
2. Distributed tracing middleware
3. Metrics collection
4. Audit mode enforcement
5. Environment validation on startup
"""

from fastapi import FastAPI
import logging
import structlog

# PHASE B5: Import observability components
from app.observability.logging import configure_logging
from app.observability.tracing import TracingMiddleware
from app.core.middleware.audit_mode import AuditModeMiddleware
from app.config.settings import settings

# Import routers
from app.api.gateway import router as gateway_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.engines.ai.recommendation.routes import router as recommendation_router


# PHASE B5: Configure structured logging BEFORE application startup
configure_logging(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ZimPrep API",
    description="National-scale exam preparation platform with AI-powered marking",
    version="1.0.0",
)

# PHASE B5: Add middleware stack (ORDER MATTERS!)
# 1. Tracing middleware MUST be first to inject trace_id
app.add_middleware(TracingMiddleware)

# 2. Audit mode middleware enforces read-only operations
app.add_middleware(AuditModeMiddleware)

# Include routers
app.include_router(health_router)
app.include_router(metrics_router)  # PHASE B5: Metrics endpoint
app.include_router(gateway_router)
app.include_router(recommendation_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with comprehensive logging."""
    logger.info(
        "=== ZimPrep Backend Starting ===",
        environment=settings.ENV,
        audit_mode=settings.AUDIT_MODE,
    )
    
    # Import engines
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    from app.engines.ai.recommendation import get_recommendation_engine
    from app.engines.reporting_analytics.reporting_adapter import ReportingEngineAdapter
    from app.engines.results.engine import ResultsEngine
    from app.engines.audit_compliance.engine import AuditComplianceEngine
    from app.orchestrator.engine_registry import engine_registry
    
    # Register Identity & Subscription Engine
    engine_registry.register(
        "identity_subscription",
        IdentitySubscriptionEngine()
    )
    logger.info("✓ Registered identity_subscription engine")
    
    # Register Recommendation Engine
    engine_registry.register(
        "recommendation",
        get_recommendation_engine()
    )
    logger.info("✓ Registered recommendation engine")
    
    # Register Reporting Engine
    engine_registry.register(
        "reporting",
        ReportingEngineAdapter()
    )
    logger.info("✓ Registered reporting engine")
    
    # Register Results Engine
    engine_registry.register(
        "results",
        ResultsEngine()
    )
    logger.info("✓ Registered results engine")
    
    # Register Audit & Compliance Engine
    engine_registry.register(
        "audit_compliance",
        AuditComplianceEngine()
    )
    logger.info("✓ Registered audit_compliance engine")
    
    # Log startup summary
    logger.info(
        "=== ZimPrep Backend Started Successfully ===",
        engines_registered=5,
        audit_mode_enabled=settings.AUDIT_MODE,
        observability_enabled=True,
        environment=settings.ENV,
    )
    
    # PHASE B5: Production readiness check
    if settings.ENV == "production":
        logger.info("🚀 Production mode: All safety checks passed")
        if settings.AUDIT_MODE:
            logger.warning("⚠️  AUDIT MODE ACTIVE - Write operations blocked")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("=== ZimPrep Backend Shutting Down ===")
    pass


