"""Input schema for Validation & Consistency Engine.

Accepts output from Reasoning & Marking Engine for validation.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class ValidationInput(BaseModel):
    """Input contract for Validation & Consistency Engine.
    
    This schema accepts the output from the Reasoning & Marking Engine
    and contains all data needed to validate AI marking decisions.
    
    CRITICAL: This engine validates, it does not reason or score.
    """
    
    # Trace metadata
    trace_id: str = Field(
        ...,
        description="Orchestrator trace ID for full traceability"
    )
    
    # Exam context
    subject: str = Field(
        ...,
        description="Subject code (e.g., 'MATH', 'PHYS')"
    )
    
    paper: str = Field(
        ...,
        description="Paper code (e.g., 'P1', 'P2')"
    )
    
    # Marks to validate
    max_marks: int = Field(
        ...,
        gt=0,
        description="Maximum possible marks for this question"
    )
    
    awarded_marks: float = Field(
        ...,
        ge=0,
        description="Marks suggested by Reasoning Engine"
    )
    
    # Breakdown per rubric item
    mark_breakdown: Dict[str, float] = Field(
        ...,
        description="Marks allocated per rubric item (rubric_id -> marks)"
    )
    
    # Authoritative rubric
    rubric: Dict[str, Dict] = Field(
        ...,
        description="Authoritative rubric with mark limits per item"
    )
    
    # Evidence tracking
    evidence_ids: List[str] = Field(
        ...,
        description="List of evidence IDs used in marking"
    )
    
    # AI-generated outputs
    feedback: str = Field(
        ...,
        min_length=1,
        description="AI-generated feedback (already generated)"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in marking (0.0 to 1.0)"
    )
    
    class Config:
        frozen = True  # Input is immutable
