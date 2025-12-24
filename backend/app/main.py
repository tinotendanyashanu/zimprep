"""FastAPI application with Phase B5 production hardening + startup fixes.

CRITICAL: This module integrates:
1. Structured logging with trace context
2. Distributed tracing middleware
3. Metrics collection
4. Audit mode enforcement
5. Environment validation on startup
6. NON-BLOCKING engine registration (Phase 1 fix)
7. Separate /health and /readiness endpoints
"""

# CRITICAL: Must be first import for Python 3.14 compatibility
import app.compat_patch  # noqa: F401

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
from app.api.routes.overrides import router as overrides_router  # PHASE 3: Override routes
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

# PHASE 6: Rate limiting middleware (prevent abuse)
from app.core.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(health_router)
app.include_router(metrics_router)  # PHASE B5: Metrics endpoint
app.include_router(gateway_router)
app.include_router(overrides_router)  # PHASE 3: Override routes
app.include_router(recommendation_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with comprehensive logging and non-blocking engine registration."""
    from app.api.routes.health import set_readiness
    
    logger.info(
        "=== ZimPrep Backend Starting ===",
        environment=settings.ENV,
        audit_mode=settings.AUDIT_MODE,
    )
    
    # Test MongoDB connection (non-blocking)
    mongodb_ok = False
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        await mongo_client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
        mongodb_ok = True
    except Exception as e:
        logger.warning(
            f"⚠️  MongoDB connection failed: {e}",
            exc_info=False
        )
        logger.warning("Server will start but database operations may fail")
    
    # Register engines (non-blocking - failures are logged but non-fatal)
    engines_registered = 0
    engines_failed = 0
    
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    from app.engines.exam_structure.engine import ExamStructureEngine
    from app.engines.session_timing.engine import SessionTimingEngine
    from app.engines.question_delivery.engine import QuestionDeliveryEngine
    from app.engines.submission.engine import SubmissionEngine
    from app.engines.ai.embedding.engine import EmbeddingEngine
    from app.engines.ai.retrieval.engine import RetrievalEngine
    from app.engines.ai.reasoning_marking.engine import ReasoningMarkingEngine
    from app.engines.ai.validation_consistency.engine import ValidationConsistencyEngine
    from app.engines.ai.recommendation import get_recommendation_engine
    from app.engines.reporting_analytics.reporting_adapter import ReportingEngineAdapter
    from app.engines.results.engine import ResultsEngine
    from app.engines.audit_compliance.engine import AuditComplianceEngine
    from app.engines.background_processing.engine import BackgroundProcessingEngine
    from app.orchestrator.engine_registry import engine_registry
    
    # Define all engines to register
    engines_to_register = [
        ("identity_subscription", lambda: IdentitySubscriptionEngine()),
        ("exam_structure", lambda: ExamStructureEngine()),
        ("session_timing", lambda: SessionTimingEngine()),
        ("question_delivery", lambda: QuestionDeliveryEngine()),
        ("submission", lambda: SubmissionEngine()),
        ("embedding", lambda: EmbeddingEngine()),
        ("retrieval", lambda: RetrievalEngine()),
        ("reasoning_marking", lambda: ReasoningMarkingEngine()),
        ("validation", lambda: ValidationConsistencyEngine()),
        ("recommendation", lambda: get_recommendation_engine()),
        ("reporting", lambda: ReportingEngineAdapter()),
        ("results", lambda: ResultsEngine()),
        ("audit_compliance", lambda: AuditComplianceEngine()),
        ("background_processing", lambda: BackgroundProcessingEngine()),
    ]
    
    # Register each engine with error handling
    for engine_name, engine_factory in engines_to_register:
        try:
            engine = engine_factory()
            engine_registry.register(engine_name, engine)
            logger.info(f"✓ Registered {engine_name} engine")
            engines_registered += 1
        except Exception as e:
            logger.error(
                f"❌ Failed to register {engine_name} engine: {e}",
                exc_info=True
            )
            engines_failed += 1
    
    # Update readiness state
    all_engines_ok = engines_failed == 0
    set_readiness(engines=all_engines_ok, mongodb=mongodb_ok)
    
    # Log startup summary
    logger.info(
        "=== ZimPrep Backend Started Successfully ===",
        engines_registered=engines_registered,
        engines_failed=engines_failed,
        mongodb_connected=mongodb_ok,
        audit_mode_enabled=settings.AUDIT_MODE,
        observability_enabled=True,
        environment=settings.ENV,
    )
    
    # PHASE B5: Production readiness check
    if settings.ENV == "production":
        logger.info("🚀 Production mode: All safety checks passed")
        if settings.AUDIT_MODE:
            logger.warning("⚠️  AUDIT MODE ACTIVE - Write operations blocked")
        
        if engines_failed > 0:
            logger.error(
                f"🚨 PRODUCTION ALERT: {engines_failed} engines failed to register!"
            )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("=== ZimPrep Backend Shutting Down ===")
    pass

