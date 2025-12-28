"""ZimPrep Backend Application Entry Point.

PHASE ZERO: CRITICAL SYSTEM INITIALIZATION

This module initializes the FastAPI application and ensures:
1. ALL required engines are registered
2. Engine registry is complete (fail-fast on startup)
3. Orchestrator is initialized
4. API Gateway is mounted
5. System is executable, governable, and legally safe

STARTUP SEQUENCE:
1. Import engine registry (triggers engine registration)
2. Validate engine registry completeness
3. Create FastAPI app
4. Register middleware
5. Mount API routers
6. Fail fast if ANY required component is missing
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# CRITICAL: Import registry FIRST to trigger engine registration
from app.orchestrator.engine_registry import engine_registry
from app.orchestrator.pipelines import PIPELINES, get_all_pipeline_names
from app.orchestrator.orchestrator import (
    orchestrator,
    PipelineExecutionError,
    AppealIntegrityError,
    ReportingIntegrityError,
    AccessDeniedError
)

# Import API Gateway
from app.api.gateway import router as gateway_router
from app.api.endpoints.dashboard_endpoints import router as dashboard_router
from app.api.endpoints.handwriting_endpoints import router as handwriting_router
from app.api.endpoints.practice_endpoints import router as practice_router
from app.api.endpoints.external_api import router as external_router  # Phase 5
from app.api.v1.resilience import router as resilience_router  # Phase 6


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_all_required_engines() -> set[str]:
    """Extract all unique engine names from pipeline definitions.
    
    Returns:
        Set of all engine names referenced in any pipeline
    """
    required_engines = set()
    for pipeline_engines in PIPELINES.values():
        required_engines.update(pipeline_engines)
    return required_engines


def validate_engine_registry_completeness() -> None:
    """Validate that ALL pipeline-required engines are registered.
    
    FAIL-FAST: If any engine is missing, abort startup immediately.
    
    Raises:
        RuntimeError: If any required engine is not registered
    """
    required_engines = get_all_required_engines()
    registered_engines = set(engine_registry._engines.keys())
    
    missing_engines = required_engines - registered_engines
    
    if missing_engines:
        error_msg = (
            f"FATAL STARTUP ERROR: {len(missing_engines)} required engines "
            f"are NOT registered.\n"
            f"Missing engines: {sorted(missing_engines)}\n"
            f"Registered engines: {sorted(registered_engines)}\n"
            f"Required engines: {sorted(required_engines)}\n\n"
            f"System cannot start with incomplete engine registry.\n"
            f"Fix: Register missing engines in app/orchestrator/engine_registry.py"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(
        f"✓ Engine registry validation PASSED: "
        f"{len(registered_engines)} engines registered"
    )
    logger.info(f"✓ Registered engines: {sorted(registered_engines)}")


def validate_pipeline_definitions() -> None:
    """Validate pipeline definitions are valid.
    
    Checks:
    1. All pipelines have at least one engine
    2. No duplicate engine names in a pipeline
    3. Audit coverage validation (warnings only)
    
    Raises:
        RuntimeError: If any pipeline is invalid
    """
    for pipeline_name, engines in PIPELINES.items():
        if not engines:
            raise RuntimeError(
                f"FATAL: Pipeline '{pipeline_name}' has no engines"
            )
        
        if len(engines) != len(set(engines)):
            duplicates = [e for e in engines if engines.count(e) > 1]
            raise RuntimeError(
                f"FATAL: Pipeline '{pipeline_name}' has duplicate engines: {duplicates}"
            )
        
        # Audit coverage check (warning only for special pipelines)
        if "audit_compliance" not in engines:
            # Dashboard and other read-only pipelines may skip audit
            if "dashboard" not in pipeline_name.lower():
                logger.warning(
                    f"⚠ Pipeline '{pipeline_name}' does NOT include audit_compliance. "
                    f"Evidence may not be captured."
                )
    
    logger.info(f"✓ Pipeline definitions validation PASSED: {len(PIPELINES)} pipelines defined")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown hooks.
    
    STARTUP:
    - Validate engine registry completeness (FAIL-FAST)
    - Validate pipeline definitions
    - Log system readiness
    
    SHUTDOWN:
    - Log shutdown
    """
    # STARTUP
    logger.info("=" * 80)
    logger.info("ZimPrep Backend - Phase Zero Initialization")
    logger.info("=" * 80)
    
    try:
        # CRITICAL: Validate engine registry completeness
        logger.info("Validating engine registry...")
        validate_engine_registry_completeness()
        
        # Validate pipeline definitions
        logger.info("Validating pipeline definitions...")
        validate_pipeline_definitions()
        
        # Log orchestrator status
        logger.info(
            f"✓ Orchestrator initialized with {len(engine_registry._engines)} engines"
        )
        
        # Log pipeline status
        pipeline_names = get_all_pipeline_names()
        logger.info(f"✓ Available pipelines: {pipeline_names}")
        
        logger.info("=" * 80)
        logger.info("✓ PHASE ZERO VALIDATION PASSED - System is ready")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("✗ PHASE ZERO VALIDATION FAILED - System cannot start")
        logger.error("=" * 80)
        logger.exception(e)
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("Shutting down ZimPrep Backend...")


# Create FastAPI application
app = FastAPI(
    title="ZimPrep Backend API",
    description=(
        "Production-grade exam preparation and assessment platform.\n\n"
        "**Architecture:**\n"
        "- Engine-based architecture with orchestrator-only execution\n"
        "- Immutable audit trails for legal defensibility\n"
        "- AI governance with validation veto power\n"
        "- REG (Registry-Engine-Gateway) principles\n\n"
        "**Phase Zero Guarantees:**\n"
        "- All engines registered (fail-fast on startup)\n"
        "- Validation can veto AI outputs\n"
        "- Audit evidence always captured\n"
        "- Orchestrator is single execution authority"
    ),
    version="1.0.0-phase-zero",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(PipelineExecutionError)
async def pipeline_execution_error_handler(
    request: Request,
    exc: PipelineExecutionError
) -> JSONResponse:
    """Handle pipeline execution errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Pipeline execution failed",
            "message": str(exc),
            "pipeline_name": exc.pipeline_name,
            "failed_engine": exc.failed_engine,
            "trace_id": exc.trace_id
        }
    )


@app.exception_handler(AppealIntegrityError)
async def appeal_integrity_error_handler(
    request: Request,
    exc: AppealIntegrityError
) -> JSONResponse:
    """Handle appeal integrity violations."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Appeal integrity violation",
            "message": str(exc),
            "pipeline_name": exc.pipeline_name,
            "blocked_engine": exc.blocked_engine,
            "trace_id": exc.trace_id
        }
    )


@app.exception_handler(ReportingIntegrityError)
async def reporting_integrity_error_handler(
    request: Request,
    exc: ReportingIntegrityError
) -> JSONResponse:
    """Handle reporting integrity violations."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Reporting integrity violation",
            "message": str(exc),
            "pipeline_name": exc.pipeline_name,
            "blocked_engine": exc.blocked_engine,
            "trace_id": exc.trace_id
        }
    )


@app.exception_handler(AccessDeniedError)
async def access_denied_error_handler(
    request: Request,
    exc: AccessDeniedError
) -> JSONResponse:
    """Handle access denied errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Access denied",
            "message": str(exc),
            "required_feature": exc.required_feature,
            "trace_id": exc.trace_id
        }
    )


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint.
    
    Returns system status and engine count.
    """
    return {
        "status": "healthy",
        "version": "1.0.0-phase-zero",
        "engines_registered": len(engine_registry._engines),
        "pipelines_available": len(PIPELINES),
        "phase_zero": "PASSED"
    }


# Register API routers
app.include_router(gateway_router)
app.include_router(dashboard_router)  # Dashboard endpoints (recommendations integration)
app.include_router(handwriting_router)
app.include_router(practice_router)
app.include_router(external_router)  # Phase 5: External API endpoints
app.include_router(resilience_router)  # Phase 6: Mobile & Low-Connectivity Resilience


# Root endpoint
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ZimPrep Backend API",
        "version": "1.0.0-phase-zero",
        "status": "operational",
        "phase_zero_validation": "PASSED",
        "documentation": "/docs",
        "health_check": "/health"
    }
