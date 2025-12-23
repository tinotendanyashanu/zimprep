"""Output schema for Validation & Consistency Engine.

Defines the orchestrator-compatible output contract.
"""

from typing import List

from pydantic import BaseModel, Field

from app.engines.ai.validation_consistency.schemas.violation import Violation


class ValidationOutput(BaseModel):
    """Output contract for Validation & Consistency Engine.
    
    This output is:
    - Orchestrator-compatible
    - Immutable
    - Audit-ready
    - Contains hard validity flag for pipeline control
    
    CRITICAL: If is_valid = false, the orchestrator MUST halt the pipeline.
    """
    
    # Trace metadata
    trace_id: str = Field(
        ...,
        description="Orchestrator trace ID"
    )
    
    # Validated marks (same as input if valid, else corrected or rejected)
    final_awarded_marks: float = Field(
        ...,
        ge=0,
        description="Final marks after validation (may be corrected or unchanged)"
    )
    
    # Validated feedback (same as input unless sanitized)
    validated_feedback: str = Field(
        ...,
        description="Validated feedback (passed through unless issues)"
    )
    
    # AI confidence (carried forward)
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence (unchanged from input)"
    )
    
    # Violations detected
    violations: List[Violation] = Field(
        default_factory=list,
        description="List of all violations detected"
    )
    
    # CRITICAL: Pipeline control flag
    is_valid: bool = Field(
        ...,
        description="CRITICAL: If false, orchestrator MUST halt pipeline"
    )
    
    # Engine metadata
    engine_name: str = Field(
        default="validation_consistency",
        description="Engine identifier"
    )
    
    engine_version: str = Field(
        default="1.0.0",
        description="Engine version"
    )
    
    class Config:
        frozen = True  # Output is immutable for audit trail
