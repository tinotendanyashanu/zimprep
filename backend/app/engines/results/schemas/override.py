"""Schema definitions for mark override functionality.

CRITICAL: These schemas define how examiners can adjust AI marks.
All overrides must be immutable and fully audited.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class MarkOverride(BaseModel):
    """Immutable record of human mark adjustment.
    
    LEGAL SIGNIFICANCE: This record is part of the audit trail.
    Once created, it cannot be modified or deleted.
    """
    
    override_id: str = Field(
        ...,
        description="Unique identifier for this override"
    )
    
    trace_id: str = Field(
        ...,
        description="Original exam attempt trace ID"
    )
    
    question_id: str = Field(
        ...,
        description="Question that was re-marked"
    )
    
    original_mark: float = Field(
        ...,
        description="AI-assigned mark before override",
        ge=0.0
    )
    
    adjusted_mark: float = Field(
        ...,
        description="Human-assigned mark after review",
        ge=0.0
    )
    
    override_reason: str = Field(
        ...,
        description="Examiner's justification for the adjustment",
        min_length=10,
        max_length=2000
    )
    
    overridden_by_user_id: str = Field(
        ...,
        description="User ID of the examiner who made the override"
    )
    
    overridden_by_role: str = Field(
        ...,
        description="Role of the user (must be examiner or admin)"
    )
    
    overridden_at: datetime = Field(
        ...,
        description="Timestamp when override was applied"
    )
    
    # Metadata
    ai_validation_confidence: float | None = Field(
        None,
        description="Original AI validation confidence score",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        frozen = True  # Immutable
        json_schema_extra = {
            "example": {
                "override_id": "ovr_abc123",
                "trace_id": "trace_xyz789",
                "question_id": "q_math_01",
                "original_mark": 6.5,
                "adjusted_mark": 8.0,
                "override_reason": "Student demonstrated clear understanding of Pythagoras theorem. AI undervalued the alternative solution approach which is mathematically valid.",
                "overridden_by_user_id": "examiner_001",
                "overridden_by_role": "examiner",
                "overridden_at": "2024-12-23T14:30:00Z",
                "ai_validation_confidence": 0.85
            }
        }


class MarkOverrideRequest(BaseModel):
    """Request to override an AI mark.
    
    Submitted by examiners via API.
    """
    
    question_id: str = Field(
        ...,
        description="Question to re-mark"
    )
    
    adjusted_mark: float = Field(
        ...,
        description="New mark being assigned",
        ge=0.0
    )
    
    override_reason: str = Field(
        ...,
        description="Justification (min 10 characters)",
        min_length=10,
        max_length=2000
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_math_01",
                "adjusted_mark": 8.0,
                "override_reason": "Alternative solution method is valid and demonstrates understanding"
            }
        }


class MarkOverrideResponse(BaseModel):
    """Response after applying override."""
    
    success: bool
    override_id: str
    message: str
    
    # Updated result summary
    original_total: float | None = None
    adjusted_total: float | None = None
    grade_changed: bool = False
    new_grade: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "override_id": "ovr_abc123",
                "message": "Mark override applied successfully",
                "original_total": 78.5,
                "adjusted_total": 80.0,
                "grade_changed": True,
                "new_grade": "A"
            }
        }
