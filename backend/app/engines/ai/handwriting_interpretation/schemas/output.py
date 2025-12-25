"""Output schema for Handwriting Interpretation Engine."""

from typing import Any
from pydantic import BaseModel, Field

from app.engines.ai.handwriting_interpretation.schemas.interpretation import StructuredAnswer


class HandwritingInterpretationOutput(BaseModel):
    """Output contract for Handwriting Interpretation Engine.
    
    Contains the canonical structured representation of the handwritten answer,
    ready for embedding and AI marking.
    
    Confidence represents OCR quality, NOT answer correctness.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace identifier from input (for audit trail)"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier from input"
    )
    
    structured_answer: StructuredAnswer = Field(
        ...,
        description="Canonical structured representation of the handwritten answer"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall OCR confidence score (NOT answer correctness)"
    )
    
    requires_manual_review: bool = Field(
        ...,
        description="True if confidence below threshold or quality issues detected"
    )
    
    ocr_metadata: dict[str, Any] = Field(
        ...,
        description="OCR execution metadata (provider, model, resolution, etc.)"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for audit trail and reproducibility"
    )
    
    # Image quality metrics
    image_quality: dict[str, Any] = Field(
        default_factory=dict,
        description="Image quality metrics (resolution, clarity, detected issues)"
    )
    
    # Cost tracking
    processing_cost: dict[str, Any] = Field(
        default_factory=lambda: {
            "provider": "openai",
            "model": "gpt-4-vision-preview",
            "tokens_used": 0,
            "estimated_cost_usd": 0.0,
        },
        description="Processing cost metadata for cost control"
    )
    
    # Audit trail
    image_reference: str = Field(
        ...,
        description="Original image reference from input (immutable)"
    )
