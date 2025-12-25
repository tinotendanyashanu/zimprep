"""Input schema for Handwriting Interpretation Engine."""

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


class HandwritingInterpretationInput(BaseModel):
    """Input contract for Handwriting Interpretation Engine.
    
    Receives image reference from Submission Engine and performs OCR
    to extract canonical text representation.
    
    CRITICAL: This engine ONLY does interpretation, NOT marking.
    Marking happens in the Reasoning & Marking Engine.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    image_reference: str = Field(
        ...,
        description="Cloud storage reference to the handwritten answer photo"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier for context and audit trail"
    )
    
    subject: str = Field(
        ...,
        description="Subject name (e.g., 'Mathematics', 'Physics') - influences OCR hints"
    )
    
    paper_code: str = Field(
        ...,
        description="Paper code for audit trail (e.g., 'ZIMSEC_O_LEVEL_MATH_4008')"
    )
    
    max_marks: int = Field(
        ...,
        ge=1,
        description="Maximum marks allocated for this question (for context)"
    )
    
    answer_type: Literal["calculation", "essay", "short_answer", "structured"] = Field(
        ...,
        description="Type of answer - influences OCR strategy and structure extraction"
    )
    
    ocr_options: dict[str, Any] = Field(
        default_factory=lambda: {
            "language": "en",
            "enable_math_recognition": True,
            "enable_step_detection": True,
            "quality_threshold": 0.5,
        },
        description="OCR configuration options"
    )
    
    @field_validator("image_reference")
    @classmethod
    def validate_image_reference(cls, v: str) -> str:
        """Validate image reference format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("image_reference cannot be empty")
        
        # Basic format validation (assumes format: storage://bucket/path/to/image.jpg)
        if "://" not in v:
            raise ValueError(
                f"image_reference must be a valid storage URI, got: {v}"
            )
        
        return v
    
    @field_validator("answer_type")
    @classmethod
    def validate_answer_type_consistency(cls, v: str) -> str:
        """Validate answer type is one of the allowed types."""
        allowed = {"calculation", "essay", "short_answer", "structured"}
        if v not in allowed:
            raise ValueError(
                f"answer_type must be one of {allowed}, got: {v}"
            )
        return v
