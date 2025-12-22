"""Output schema for the Results Engine.

Defines the immutable final result certificate returned to the orchestrator.
This output becomes the authoritative exam result record.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TopicBreakdown(BaseModel):
    """Performance breakdown for a single topic across all papers.
    
    Aggregates marks for a topic that may appear in multiple papers.
    """
    
    topic_code: str = Field(
        ...,
        description="Topic identifier"
    )
    
    topic_name: str = Field(
        ...,
        description="Human-readable topic name"
    )
    
    total_max_marks: float = Field(
        ...,
        ge=0.0,
        description="Total maximum marks for this topic across all papers"
    )
    
    total_awarded_marks: float = Field(
        ...,
        ge=0.0,
        description="Total marks achieved for this topic across all papers"
    )
    
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage score for this topic"
    )
    
    papers_covered: List[str] = Field(
        ...,
        description="List of paper codes where this topic appears"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable


class PaperResult(BaseModel):
    """Summary of a single paper's performance and contribution to final grade."""
    
    paper_code: str = Field(
        ...,
        description="Paper identifier"
    )
    
    paper_name: str = Field(
        ...,
        description="Human-readable paper name"
    )
    
    max_marks: float = Field(
        ...,
        ge=0.0,
        description="Maximum marks for this paper"
    )
    
    awarded_marks: float = Field(
        ...,
        ge=0.0,
        description="Marks achieved on this paper"
    )
    
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage score for this paper"
    )
    
    weighting: float = Field(
        ...,
        gt=0.0,
        le=1.0,
        description="Paper's weighting in final grade calculation"
    )
    
    weighted_contribution: float = Field(
        ...,
        ge=0.0,
        description="This paper's contribution to the final total (awarded_marks * weighting)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable


class ResultsOutput(BaseModel):
    """Immutable final result certificate.
    
    This is the authoritative exam result that becomes the legal record
    for the candidate's performance. It can be used in appeals and must
    be reproducible from the input data.
    """
    
    # Engine metadata
    trace_id: str = Field(
        ...,
        description="Request trace ID for audit trail"
    )
    
    engine_name: str = Field(
        default="results",
        description="Engine identifier"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for reproducibility"
    )
    
    # Candidate identification
    candidate_id: str = Field(
        ...,
        description="Candidate identifier"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam session identifier"
    )
    
    subject_code: str = Field(
        ...,
        description="Subject code"
    )
    
    subject_name: str = Field(
        ...,
        description="Human-readable subject name"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version"
    )
    
    # Final results
    total_marks: float = Field(
        ...,
        ge=0.0,
        description="Final weighted total marks"
    )
    
    max_total_marks: float = Field(
        ...,
        gt=0.0,
        description="Maximum possible total marks"
    )
    
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall percentage score"
    )
    
    grade: str = Field(
        ...,
        description="Final letter grade (e.g., 'A*', 'A', 'B', etc.)"
    )
    
    pass_status: bool = Field(
        ...,
        description="Whether the candidate has passed"
    )
    
    # Breakdowns
    paper_results: List[PaperResult] = Field(
        ...,
        description="Detailed breakdown by paper"
    )
    
    topic_breakdown: List[TopicBreakdown] = Field(
        default_factory=list,
        description="Optional performance breakdown by topic"
    )
    
    # Metadata
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in result (always 1.0 for deterministic operations)"
    )
    
    issued_at: datetime = Field(
        ...,
        description="Timestamp when result was generated (UTC)"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Optional notes for audit trail"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make output immutable
