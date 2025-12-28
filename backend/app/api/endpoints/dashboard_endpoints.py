"""Dashboard Endpoints

Dedicated endpoints for student dashboard functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import logging

from app.api.dependencies import get_current_user, User
from app.orchestrator.orchestrator import orchestrator, PipelineExecutionError
from app.orchestrator.execution_context import ExecutionContext
from app.api.utils.dashboard_helpers import merge_recommendations_into_dashboard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get student dashboard",
    description="Fetch student dashboard with performance metrics and AI-powered recommendations"
)
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """Get student dashboard with integrated recommendations.
    
    This endpoint executes the student_dashboard_v1 pipeline which includes:
    1. Identity & Subscription verification
    2. Reporting Engine (performance metrics)
    3. Recommendation Engine (AI-powered study recommendations)
    
    The recommendations from the Recommendation Engine are merged into the
    dashboard response automatically.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        Dashboard data with performance metrics and recommendations
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    # Create execution context
    context = ExecutionContext.create(
        user_id=current_user.id,
        request_source="api",
        feature_flags={}
    )
    
    logger.info(
        "Dashboard request received",
        extra={
            "trace_id": context.trace_id,
            "user_id": current_user.id
        }
    )
    
    try:
        # Execute student_dashboard_v1 pipeline
        # This executes: identity_subscription → reporting → recommendation
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "user_id": current_user.id,
                "role": current_user.role,
                "reporting_scope": "DASHBOARD",
                "export_format": "NONE"
            },
            context=context
        )
        
        # Extract outputs from pipeline
        reporting_output = result["engine_outputs"].get("reporting", {})
        recommendation_output = result["engine_outputs"].get("recommendation", {})
        
        # Get reporting data
        reporting_data = reporting_output.get("data")
        if not reporting_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "trace_id": context.trace_id,
                    "error": "Reporting engine did not produce output"
                }
            )
        
        # Get recommendation data (may be None if engine failed/skipped)
        recommendation_data = recommendation_output.get("data") if recommendation_output.get("success") else None
        
        # Merge recommendations into dashboard
        merged_data = merge_recommendations_into_dashboard(
            reporting_data=reporting_data if hasattr(reporting_data, 'model_dump') else reporting_data,
            recommendation_data=recommendation_data
        )
        
        logger.info(
            "Dashboard request completed",
            extra={
                "trace_id": context.trace_id,
                "user_id": current_user.id,
                "has_recommendations": bool(recommendation_data),
                "duration_ms": result["total_duration_ms"]
            }
        )
        
        return merged_data
        
    except PipelineExecutionError as e:
        logger.error(
            "Dashboard pipeline failed",
            extra={
                "trace_id": context.trace_id,
                "user_id": current_user.id,
                "failed_engine": e.failed_engine,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trace_id": context.trace_id,
                "error": str(e),
                "failed_engine": e.failed_engine
            }
        )
    
    except Exception as e:
        logger.exception(
            "Unexpected error during dashboard request",
            extra={
                "trace_id": context.trace_id,
                "user_id": current_user.id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "trace_id": context.trace_id,
                "error": "Internal server error"
            }
        )
