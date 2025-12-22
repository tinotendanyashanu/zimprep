"""API Gateway for ZimPrep backend.

This is the AUTHENTICATION and VALIDATION boundary.
All requests are validated here before being forwarded to the orchestrator.

CRITICAL RULES:
1. All endpoints MUST use Pydantic schemas (no raw dicts)
2. All endpoints MUST enforce authentication via JWT
3. Gateway creates trace context (orchestrator never creates trace_id)
4. Gateway does NOT contain business logic
5. Gateway forwards to orchestrator only
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import logging

from app.api.dependencies import get_current_user, User
from app.api.schemas import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    EngineExecutionResult,
)
from app.orchestrator.orchestrator import orchestrator, PipelineExecutionError
from app.orchestrator.execution_context import ExecutionContext


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["gateway"])


@router.post(
    "/pipeline/execute",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a pipeline",
    description="Execute a complete pipeline with all engines in canonical order"
)
async def execute_pipeline(
    request: PipelineExecutionRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> PipelineExecutionResponse:
    """Execute a pipeline with full authentication and validation.
    
    This is the ONLY way to execute engines in production.
    
    Args:
        request: Pipeline execution request with schema validation
        current_user: Authenticated user from JWT token
        
    Returns:
        PipelineExecutionResponse with all engine outputs
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    # Create execution context (GATEWAY CREATES TRACE)
    context = ExecutionContext.create(
        user_id=current_user.id,
        request_source="api",  # Could be extracted from headers
        feature_flags={}  # Could be fetched from feature flag service
    )
    
    logger.info(
        "Pipeline execution request received",
        extra={
            "pipeline_name": request.pipeline_name,
            "trace_id": context.trace_id,
            "request_id": context.request_id,
            "user_id": current_user.id
        }
    )
    
    try:
        # Execute pipeline via orchestrator
        result = orchestrator.execute_pipeline(
            pipeline_name=request.pipeline_name,
            payload=request.input_data,
            context=context
        )
        
        # Convert engine outputs to response schema
        engine_results = {
            name: EngineExecutionResult(**output)
            for name, output in result["engine_outputs"].items()
        }
        
        # Build response
        response = PipelineExecutionResponse(
            trace_id=result["trace_id"],
            request_id=result["request_id"],
            pipeline_name=result["pipeline_name"],
            success=result["success"],
            engine_outputs=engine_results,
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            total_duration_ms=result["total_duration_ms"]
        )
        
        logger.info(
            "Pipeline execution completed successfully",
            extra={
                "trace_id": context.trace_id,
                "pipeline_name": request.pipeline_name,
                "duration_ms": result["total_duration_ms"]
            }
        )
        
        return response
        
    except PipelineExecutionError as e:
        logger.error(
            "Pipeline execution failed",
            extra={
                "trace_id": context.trace_id,
                "pipeline_name": request.pipeline_name,
                "failed_engine": e.failed_engine,
                "error": str(e)
            }
        )
        
        # Return error response with partial results if available
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trace_id": context.trace_id,
                "error": str(e),
                "pipeline_name": request.pipeline_name,
                "failed_engine": e.failed_engine
            }
        )
    
    except Exception as e:
        logger.exception(
            "Unexpected error during pipeline execution",
            extra={
                "trace_id": context.trace_id,
                "pipeline_name": request.pipeline_name
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trace_id": context.trace_id,
                "error": "Internal server error",
                "pipeline_name": request.pipeline_name
            }
        )


@router.get(
    "/pipelines",
    summary="List available pipelines",
    description="Get all available pipeline names"
)
async def list_pipelines(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, list[str]]:
    """List all available pipelines.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Dictionary with pipeline names
    """
    from app.orchestrator.pipelines import get_all_pipeline_names
    
    return {
        "pipelines": get_all_pipeline_names()
    }


@router.get(
    "/engines",
    summary="List registered engines",
    description="Get all registered engine names"
)
async def list_engines(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, list[str]]:
    """List all registered engines.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Dictionary with engine names
    """
    return {
        "engines": list(orchestrator.registry._engines.keys())
    }
