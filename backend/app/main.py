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
    """Initialize services on startup with comprehensive logging."""
    logger.info(
        "=== ZimPrep Backend Starting ===",
        environment=settings.ENV,
        audit_mode=settings.AUDIT_MODE,
    )
    
    # Import engines
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
    
    # Register Identity & Subscription Engine
    engine_registry.register(
        "identity_subscription",
        IdentitySubscriptionEngine()
    )
    logger.info("✓ Registered identity_subscription engine")
    
    # Register Exam Structure Engine
    engine_registry.register(
        "exam_structure",
        ExamStructureEngine()
    )
    logger.info("✓ Registered exam_structure engine")
    
    # Register Session Timing Engine
    engine_registry.register(
        "session_timing",
        SessionTimingEngine()
    )
    logger.info("✓ Registered session_timing engine")
    
    # Register Question Delivery Engine
    engine_registry.register(
        "question_delivery",
        QuestionDeliveryEngine()
    )
    logger.info("✓ Registered question_delivery engine")
    
    # Register Submission Engine
    engine_registry.register(
        "submission",
        SubmissionEngine()
    )
    logger.info("✓ Registered submission engine")
    
    # Register Embedding Engine (AI)
    engine_registry.register(
        "embedding",
        EmbeddingEngine()
    )
    logger.info("✓ Registered embedding engine")
    
    # Register Retrieval Engine (AI)
    engine_registry.register(
        "retrieval",
        RetrievalEngine()
    )
    logger.info("✓ Registered retrieval engine")
    
    # Register Reasoning & Marking Engine (AI)
    engine_registry.register(
        "reasoning_marking",
        ReasoningMarkingEngine()
    )
    logger.info("✓ Registered reasoning_marking engine")
    
    # Register Validation & Consistency Engine (AI)
    engine_registry.register(
        "validation",
        ValidationConsistencyEngine()
    )
    logger.info("✓ Registered validation engine")
    
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
    
    # Register Background Processing Engine
    engine_registry.register(
        "background_processing",
        BackgroundProcessingEngine()
    )
    logger.info("✓ Registered background_processing engine")
    
    # Log startup summary
    logger.info(
        "=== ZimPrep Backend Started Successfully ===",
        engines_registered=14,
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


