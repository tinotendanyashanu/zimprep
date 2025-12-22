"""Input schema for the Results Engine.

Defines the contract for final result calculation requests.
All inputs are immutable and subject to strict validation.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.engines.results.schemas.grading import GradingScale


class SectionBreakdown(BaseModel):
    """Marks breakdown for a section/topic within a paper.
    
    Example: "Algebra" section in Paper 1 Math.
    """
    
    topic_code: str = Field(
        ...,
        description="Topic/section identifier (e.g., 'ALGEBRA', 'MECHANICS')"
    )
    
    topic_name: str = Field(
        ...,
        description="Human-readable topic name"
    )
    
    max_marks: float = Field(
        ...,
        ge=0.0,
        description="Maximum marks for this topic in this paper"
    )
    
    awarded_marks: float = Field(
        ...,
        ge=0.0,
        description="Marks achieved for this topic"
    )
    
    @field_validator("awarded_marks")
    @classmethod
    def validate_marks_within_bounds(cls, v: float, info) -> float:
        """Ensure awarded marks don't exceed maximum."""
        if "max_marks" in info.data and v > info.data["max_marks"]:
            raise ValueError(
                f"Awarded marks ({v}) exceed max marks ({info.data['max_marks']})"
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable


class PaperInput(BaseModel):
    """Individual paper result data.
    
    Contains validated marks from the AI reasoning engine and
    metadata required for final grade calculation.
    """
    
    paper_code: str = Field(
        ...,
        description="Paper identifier (e.g., 'P1', 'P2', 'P3')"
    )
    
    paper_name: str = Field(
        ...,
        description="Human-readable paper name"
    )
    
    max_marks: float = Field(
        ...,
        gt=0.0,
        description="Maximum possible marks for this paper"
    )
    
    awarded_marks: float = Field(
        ...,
        ge=0.0,
        description="Total marks achieved on this paper (validated by AI engine)"
    )
    
    weighting: float = Field(
        ...,
        gt=0.0,
        le=1.0,
        description="Paper's contribution to final grade (0.0-1.0, e.g., 0.5 for 50%)"
    )
    
    section_breakdown: List[SectionBreakdown] = Field(
        default_factory=list,
        description="Optional topic-level breakdown within this paper"
    )
    
    @field_validator("awarded_marks")
    @classmethod
    def validate_marks_within_bounds(cls, v: float, info) -> float:
        """Ensure awarded marks don't exceed maximum."""
        if "max_marks" in info.data and v > info.data["max_marks"]:
            raise ValueError(
                f"Awarded marks ({v}) exceed max marks ({info.data['max_marks']})"
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable


class ResultsInput(BaseModel):
    """Input contract for final result calculation.
    
    This request triggers the calculation of final grades based on
    validated marks from all required papers.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace ID for request tracking and audit"
    )
    
    candidate_id: str = Field(
        ...,
        description="Candidate/student identifier"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam session identifier"
    )
    
    subject_code: str = Field(
        ...,
        description="Subject code (e.g., 'MATH', 'PHYS', 'CHEM')"
    )
    
    subject_name: str = Field(
        ...,
        description="Human-readable subject name"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version (e.g., '2024', '9702')"
    )
    
    papers: List[PaperInput] = Field(
        ...,
        min_length=1,
        description="List of paper results (must include all required papers)"
    )
    
    grading_scale: GradingScale = Field(
        ...,
        description="Subject-specific grading scale with grade boundaries"
    )
    
    issued_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when result calculation was requested"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Optional notes or context for audit trail"
    )
    
    @field_validator("papers")
    @classmethod
    def validate_paper_weightings_sum_to_one(cls, papers: List[PaperInput]) -> List[PaperInput]:
        """Ensure paper weightings sum to 1.0 (within tolerance)."""
        total_weighting = sum(p.weighting for p in papers)
        tolerance = 0.001  # Allow 0.1% deviation
        
        if abs(total_weighting - 1.0) > tolerance:
            raise ValueError(
                f"Paper weightings sum to {total_weighting:.4f}, "
                f"expected 1.0 ± {tolerance}"
            )
        
        return papers
    
    @field_validator("grading_scale")
    @classmethod
    def validate_grading_scale_matches_subject(cls, v: GradingScale, info) -> GradingScale:
        """Ensure grading scale matches the subject code."""
        if "subject_code" in info.data and v.subject_code != info.data["subject_code"]:
            raise ValueError(
                f"Grading scale subject '{v.subject_code}' does not match "
                f"input subject '{info.data['subject_code']}'"
            )
        
        if "syllabus_version" in info.data and v.syllabus_version != info.data["syllabus_version"]:
            raise ValueError(
                f"Grading scale syllabus '{v.syllabus_version}' does not match "
                f"input syllabus '{info.data['syllabus_version']}'"
            )
        
        return v
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable inputs
