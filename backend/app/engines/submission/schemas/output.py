"""Output schema for Submission Engine.

Defines the immutable submission confirmation returned to the orchestrator.
"""

from typing import List
from datetime import datetime
from pydantic import BaseModel, Field


class SubmissionOutput(BaseModel):
    """Immutable submission confirmation.
    
    This is the authoritative proof of submission and becomes the
    reference for all downstream engines (grading, results).
    """
    
    submission_id: str = Field(
        ...,
        description="Unique submission identifier (immutable)"
    )
    
    submission_timestamp: datetime = Field(
        ...,
        description="Server timestamp when submission was accepted (UTC)"
    )
    
    trace_id: str = Field(
        ...,
        description="Request trace ID for audit trail"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    
    student_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam identifier"
    )
    
    answer_count: int = Field(
        ...,
        ge=0,
        description="Number of answers submitted"
    )
    
    answered_question_ids: List[str] = Field(
        ...,
        description="List of question IDs that were answered"
    )
    
    session_closed: bool = Field(
        ...,
        description="Whether session was successfully closed (always True on success)"
    )
    
    integrity_hash: str = Field(
        ...,
        description="SHA-256 hash of submission for tamper detection"
    )
    
    submission_reason: str = Field(
        ...,
        description="Reason for submission (manual or time_expired)"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in submission (1.0 = clean execution)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make output immutable
