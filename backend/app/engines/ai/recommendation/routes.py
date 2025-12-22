"""FastAPI routes for Recommendation Engine.

Exposes the recommendation engine via REST API endpoints.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.engines.ai.recommendation import (
    get_recommendation_engine,
    RecommendationEngineAdapter,
)
from app.orchestrator.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


class GenerateRecommendationsRequest(BaseModel):
    """Request to generate recommendations."""
    
    student_id: str = Field(..., description="Student identifier")
    subject: str = Field(..., description="Subject code")
    syllabus_version: str = Field(..., description="Syllabus version")
    final_results: Dict[str, Any] = Field(..., description="Final exam results")
    validated_marking_summary: Dict[str, Any] = Field(..., description="Marking summary")
    historical_performance_summary: Dict[str, Any] | None = Field(
        None,
        description="Optional historical performance"
    )
    constraints: Dict[str, Any] = Field(..., description="Student constraints")


class RecommendationHealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    engine_name: str
    engine_version: str
    model: str


@router.post("/generate")
async def generate_recommendations(
    request: GenerateRecommendationsRequest,
    engine: RecommendationEngineAdapter = Depends(get_recommendation_engine),
):
    """
    Generate personalized study recommendations.
    
    This endpoint takes validated exam results and generates evidence-based,
    syllabus-aligned study recommendations for the student.
    
    **Input Requirements:**
    - All scores must be final and immutable
    - Marking summary must be validated
    - All data must be authoritative
    
    **Output:**
    - Performance diagnosis (weak areas)
    - Study recommendations (prioritized)
    - Practice suggestions (targeted)
    - Study plan (if data allows)
    - Motivation message
    
    **Important:**
    - Recommendations are advisory only
    - They do not modify scores or grades
    - All recommendations are evidence-based
    """
    
    try:
        # Create execution context
        context = ExecutionContext.create(user_id=request.student_id)
        
        # Build payload
        payload = {
            "trace_id": context.trace_id,
            "student_id": request.student_id,
            "subject": request.subject,
            "syllabus_version": request.syllabus_version,
            "final_results": request.final_results,
            "validated_marking_summary": request.validated_marking_summary,
            "historical_performance_summary": request.historical_performance_summary,
            "constraints": request.constraints,
        }
        
        # Execute engine
        response = await engine.run(payload, context)
        
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error
            )
        
        return {
            "success": True,
            "data": response.data,
            "trace": {
                "trace_id": response.trace.trace_id,
                "engine_name": response.trace.engine_name,
                "engine_version": response.trace.engine_version,
                "timestamp": response.trace.timestamp.isoformat(),
                "confidence": response.trace.confidence,
            }
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/health", response_model=RecommendationHealthResponse)
async def health_check(
    engine: RecommendationEngineAdapter = Depends(get_recommendation_engine),
):
    """
    Health check for recommendation engine.
    
    Returns:
        Engine status and configuration
    """
    
    try:
        engine_info = engine.core_engine.get_engine_info()
        
        return RecommendationHealthResponse(
            status="healthy",
            engine_name=engine_info["engine_name"],
            engine_version=engine_info["engine_version"],
            model=engine_info["model"],
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation engine is not healthy"
        )


# Example: Integration with orchestrator
@router.post("/orchestrator/execute")
async def orchestrator_execute(
    payload: Dict[str, Any],
    trace_id: str,
    engine: RecommendationEngineAdapter = Depends(get_recommendation_engine),
):
    """
    Execute recommendation engine through orchestrator interface.
    
    This endpoint is called by the orchestrator to execute the recommendation engine
    as part of the exam processing pipeline.
    
    **Orchestrator Contract:**
    - Input: dict payload + trace_id
    - Output: EngineResponse[RecommendationOutput]
    
    **Position in Pipeline:**
    - Runs AFTER Results Engine
    - Runs AFTER Validation Engine
    - Final engine in exam flow (advisory only)
    """
    
    try:
        # Create execution context
        context = ExecutionContext(trace_id=trace_id)
        
        # Execute engine
        response = await engine.run(payload, context)
        
        return {
            "success": response.success,
            "data": response.data.dict() if response.data else None,
            "error": response.error,
            "trace": {
                "trace_id": response.trace.trace_id,
                "engine_name": response.trace.engine_name,
                "engine_version": response.trace.engine_version,
                "timestamp": response.trace.timestamp.isoformat(),
                "confidence": response.trace.confidence,
            }
        }
    
    except Exception as e:
        logger.exception(f"Orchestrator execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engine execution failed: {str(e)}"
        )
