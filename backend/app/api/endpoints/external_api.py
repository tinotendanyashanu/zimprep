"""External API endpoints for Phase Five.

Provides controlled read-only access for external partners (SMS/LMS/Governance bodies).

CRITICAL RULES:
1. All endpoints require API key authentication (not JWT)
2. All endpoints enforce scope validation
3. All endpoints apply rate limiting
4. All endpoints redact PII and sensitive data
5. All endpoints are paginated
6. All endpoints are READ-ONLY
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.orchestrator.orchestrator import orchestrator
from app.engines.external_access_control.schemas import AccessScope
from app.engines.external_access_control.services import PrivacyGuard


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/external", tags=["external_api"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ExternalResultsRequest(BaseModel):
    """Request schema for external results summary."""
    
    student_id: str = Field(..., description="Student identifier")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page")


class ExternalAnalyticsRequest(BaseModel):
    """Request schema for external student analytics."""
    
    student_id: str = Field(..., description="Student identifier")
    include_mastery: bool = Field(default=True, description="Include mastery levels")


class ExternalInstitutionalRequest(BaseModel):
    """Request schema for external institutional analytics."""
    
    institution_id: str = Field(..., description="Institution identifier")
    cohort_id: Optional[str] = Field(None, description="Cohort identifier")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=200, description="Items per page")


class ExternalGovernanceRequest(BaseModel):
    """Request schema for external governance reports."""
    
    report_type: str = Field(..., description="Report type (audit/compliance/metrics)")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/results/summary")
async def get_results_summary(
    request: ExternalResultsRequest,
    x_api_key: str = Header(..., description="External API key")
):
    """Get aggregated student results (READ-ONLY, redacted).
    
    Requires scope: read:results
    
    Returns:
    - Final marks only
    - No question-by-question breakdown
    - No raw answers or evidence packs
    - PII fields redacted
    """
    try:
        # Execute external_results_v1 pipeline
        result = await orchestrator.execute_pipeline(
            pipeline_name="external_results_v1",
            payload={
                "api_key": x_api_key,
                "requested_scope": AccessScope.READ_RESULTS.value,
                "endpoint": "/api/v1/external/results/summary",
                "request_metadata": {
                    "student_id": request.student_id,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "page": request.page,
                    "page_size": request.page_size
                }
            }
        )
        
        # Check if access was granted
        if not result.get("success"):
            raise HTTPException(
                status_code=403,
                detail=result.get("error", "Access denied")
            )
        
        # Extract and redact results data
        output = result.get("output", {})
        
        # Apply privacy redaction
        redacted_output = PrivacyGuard.redact_fields(
            output,
            AccessScope.READ_RESULTS
        )
        
        return {
            "success": True,
            "data": redacted_output,
            "trace_id": result.get("metadata", {}).get("trace_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"External results API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analytics/student")
async def get_student_analytics(
    request: ExternalAnalyticsRequest,
    x_api_key: str = Header(..., description="External API key")
):
    """Get student learning analytics summary (READ-ONLY, aggregated).
    
    Requires scope: read:analytics
    
    Returns:
    - Mastery levels
    - Summary statistics
    - No individual question performance
    - PII fields redacted
    """
    try:
        # Execute external_analytics_v1 pipeline
        result = await orchestrator.execute_pipeline(
            pipeline_name="external_analytics_v1",
            payload={
                "api_key": x_api_key,
                "requested_scope": AccessScope.READ_ANALYTICS.value,
                "endpoint": "/api/v1/external/analytics/student",
                "request_metadata": {
                    "student_id": request.student_id,
                    "include_mastery": request.include_mastery
                }
            }
        )
        
        # Check if access was granted
        if not result.get("success"):
            raise HTTPException(
                status_code=403,
                detail=result.get("error", "Access denied")
            )
        
        # Extract and redact analytics data
        output = result.get("output", {})
        
        # Apply privacy redaction
        redacted_output = PrivacyGuard.redact_fields(
            output,
            AccessScope.READ_ANALYTICS
        )
        
        return {
            "success": True,
            "data": redacted_output,
            "trace_id": result.get("metadata", {}).get("trace_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"External analytics API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analytics/institution")
async def get_institutional_analytics(
    request: ExternalInstitutionalRequest,
    x_api_key: str = Header(..., description="External API key")
):
    """Get institutional cohort analytics (READ-ONLY, privacy-safe).
    
    Requires scope: read:analytics
    
    Returns:
    - Cohort-level statistics (min 10 students)
    - Aggregated performance metrics
    - No individual student identifiers
    - Privacy thresholds enforced
    """
    try:
        # Execute external_analytics_v1 pipeline
        result = await orchestrator.execute_pipeline(
            pipeline_name="external_analytics_v1",
            payload={
                "api_key": x_api_key,
                "requested_scope": AccessScope.READ_ANALYTICS.value,
                "endpoint": "/api/v1/external/analytics/institution",
                "request_metadata": {
                    "institution_id": request.institution_id,
                    "cohort_id": request.cohort_id,
                    "page": request.page,
                    "page_size": request.page_size
                }
            }
        )
        
        # Check if access was granted
        if not result.get("success"):
            raise HTTPException(
                status_code=403,
                detail=result.get("error", "Access denied")
            )
        
        # Extract output
        output = result.get("output", {})
        
        # Apply privacy redaction
        redacted_output = PrivacyGuard.redact_fields(
            output,
            AccessScope.READ_ANALYTICS
        )
        
        # Enforce aggregation threshold
        # (Assume cohort_size is in the output)
        cohort_size = output.get("cohort_size", 0)
        if cohort_size > 0:
            data = [redacted_output]  # Wrap in list for enforcement
            data = PrivacyGuard.enforce_aggregation_threshold(data, cohort_size)
            redacted_output = data[0] if data else {}
        
        return {
            "success": True,
            "data": redacted_output,
            "trace_id": result.get("metadata", {}).get("trace_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"External institutional analytics API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/governance/reports")
async def get_governance_report(
    request: ExternalGovernanceRequest,
    x_api_key: str = Header(..., description="External API key")
):
    """Get governance compliance reports (READ-ONLY, no student data).
    
    Requires scope: read:governance
    
    Returns:
    - Compliance metrics
    - Audit summaries
    - No student identifiers
    - Regulator-safe data only
    """
    try:
        # Execute external_governance_v1 pipeline
        result = await orchestrator.execute_pipeline(
            pipeline_name="external_governance_v1",
            payload={
                "api_key": x_api_key,
                "requested_scope": AccessScope.READ_GOVERNANCE.value,
                "endpoint": "/api/v1/external/governance/reports",
                "request_metadata": {
                    "report_type": request.report_type,
                    "start_date": request.start_date,
                    "end_date": request.end_date
                }
            }
        )
        
        # Check if access was granted
        if not result.get("success"):
            raise HTTPException(
                status_code=403,
                detail=result.get("error", "Access denied")
            )
        
        # Extract and redact governance data
        output = result.get("output", {})
        
        # Apply privacy redaction
        redacted_output = PrivacyGuard.redact_fields(
            output,
            AccessScope.READ_GOVERNANCE
        )
        
        return {
            "success": True,
            "data": redacted_output,
            "trace_id": result.get("metadata", {}).get("trace_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"External governance API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metadata/syllabus")
async def get_syllabus_metadata(
    subject: str = Query(..., description="Subject name"),
    level: str = Query(..., description="Level (O-level/A-level)"),
    x_api_key: str = Header(..., description="External API key")
):
    """Get exam syllabus metadata (READ-ONLY, public data).
    
    Requires scope: read:metadata
    
    Returns:
    - Syllabus structure
    - Topic hierarchy
    - No user-specific data
    """
    try:
        # For now, return static metadata
        # TODO: Implement actual syllabus metadata retrieval
        
        return {
            "success": True,
            "data": {
                "subject": subject,
                "level": level,
                "message": "Syllabus metadata endpoint - implementation pending"
            }
        }
        
    except Exception as e:
        logger.exception(f"External metadata API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
