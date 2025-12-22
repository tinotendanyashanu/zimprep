"""Output schema for Reasoning & Marking Engine.

Defines the immutable, auditable output contract.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class AwardedPoint(BaseModel):
    """A rubric point that was awarded to the student."""
    point_id: str = Field(..., description="Rubric point identifier")
    description: str = Field(..., description="What was being assessed")
    marks: float = Field(..., gt=0, description="Marks awarded for this point")
    awarded: bool = Field(True, description="Always True for awarded points")
    evidence_id: str = Field(..., description="ID of evidence that supports this award")
    evidence_excerpt: Optional[str] = Field(None, description="Brief excerpt from evidence")
    
    class Config:
        frozen = True


class MissingPoint(BaseModel):
    """A rubric point that was NOT awarded."""
    point_id: str = Field(..., description="Rubric point identifier")
    description: str = Field(..., description="What was expected but missing")
    marks: float = Field(..., gt=0, description="Marks that could have been awarded")
    reason: Optional[str] = Field(None, description="Brief explanation of why not awarded")
    
    class Config:
        frozen = True


class ReasoningMarkingOutput(BaseModel):
    """Output contract for Reasoning & Marking Engine.
    
    This output is:
    - Deterministic
    - Serializable
    - Auditable
    - Ready for Validation Engine review
    
    CRITICAL: This engine SUGGESTS marks, it does not finalize them.
    The Validation Engine has veto authority.
    """
    
    # Identification
    question_id: str = Field(..., description="Question identifier")
    trace_id: str = Field(..., description="Orchestrator trace ID")
    
    # Marks (SUGGESTED, not final)
    awarded_marks: float = Field(..., ge=0, description="Total marks suggested for award")
    max_marks: int = Field(..., gt=0, description="Maximum possible marks")
    
    # Detailed breakdown
    mark_breakdown: List[AwardedPoint] = Field(
        default_factory=list,
        description="All rubric points that were awarded with evidence citations"
    )
    missing_points: List[MissingPoint] = Field(
        default_factory=list,
        description="All rubric points that were NOT awarded"
    )
    
    # Examiner-style feedback
    feedback: str = Field(..., min_length=1, description="Professional, constructive feedback")
    
    # Confidence in this assessment
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="AI confidence in this marking (NOT student quality)"
    )
    
    # Engine metadata
    engine_name: str = Field(default="reasoning_marking", description="Engine identifier")
    engine_version: str = Field(default="1.0.0", description="Engine version")
    
    # Additional metadata
    answer_type: str = Field(..., description="Type of answer (essay/short_answer/structured)")
    evidence_count: int = Field(..., ge=0, description="Number of evidence items used")
    
    @validator("awarded_marks")
    def marks_cannot_exceed_maximum(cls, v, values):
        """Enforce hard constraint: awarded marks cannot exceed max_marks."""
        if "max_marks" in values and v > values["max_marks"]:
            raise ValueError(
                f"awarded_marks ({v}) exceeds max_marks ({values['max_marks']}) - "
                "this is a critical constraint violation"
            )
        return v
    
    @validator("mark_breakdown")
    def breakdown_must_match_awarded_marks(cls, v, values):
        """Ensure mark breakdown sum equals awarded_marks."""
        if v and "awarded_marks" in values:
            breakdown_total = sum(point.marks for point in v)
            if abs(breakdown_total - values["awarded_marks"]) > 0.01:  # Floating point tolerance
                raise ValueError(
                    f"mark_breakdown total ({breakdown_total}) does not match "
                    f"awarded_marks ({values['awarded_marks']})"
                )
        return v
    
    @validator("mark_breakdown")
    def evidence_must_be_cited(cls, v):
        """Every awarded point MUST cite evidence."""
        for point in v:
            if not point.evidence_id:
                raise ValueError(
                    f"Awarded point {point.point_id} does not cite evidence - "
                    "this violates the evidence-anchored requirement"
                )
        return v
    
    class Config:
        frozen = True  # Output is immutable for audit trail
