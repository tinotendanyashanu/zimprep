"""Error definitions for Recommendation Engine.

FAIL-CLOSED PRINCIPLE:
If any error occurs, the engine must stop and return a clear error.
Recommendations are advisory; failed recommendations are better than wrong recommendations.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RecommendationErrorCode(str, Enum):
    """Typed error codes for recommendation failures."""
    
    # Input validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_RESULTS = "MISSING_RESULTS"
    MISSING_MARKING_SUMMARY = "MISSING_MARKING_SUMMARY"
    
    # LLM errors
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    
    # Processing errors
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SYLLABUS_LOOKUP_FAILED = "SYLLABUS_LOOKUP_FAILED"
    PLAN_GENERATION_FAILED = "PLAN_GENERATION_FAILED"
    
    # Confidence errors
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"


class RecommendationError(BaseModel):
    """
    Typed error response for Recommendation Engine.
    
    This is returned to the orchestrator when the engine cannot produce recommendations.
    """
    
    error_code: RecommendationErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    trace_id: str = Field(..., description="Original trace ID for debugging")
    recoverable: bool = Field(..., description="Whether the error is potentially recoverable with retry")
    details: Optional[str] = Field(None, description="Additional error details for debugging")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "LLM_UNAVAILABLE",
                "message": "LLM service is currently unavailable",
                "trace_id": "trace_20250101_123456",
                "recoverable": True,
                "details": "Connection timeout after 30s"
            }
        }
