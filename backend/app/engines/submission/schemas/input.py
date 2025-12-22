"""Input schema for Submission Engine.

Defines the contract for exam answer submission requests.
"""

from typing import Optional, List, Any, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Answer(BaseModel):
    """Individual answer for a question.
    
    Supports multiple answer types: text, MCQ, numeric, matching, file references.
    """
    
    question_id: str = Field(
        ...,
        description="Question identifier from exam structure"
    )
    
    answer_type: Literal["text", "mcq", "numeric", "matching", "file_ref"] = Field(
        ...,
        description="Type of answer provided"
    )
    
    answer_content: Any = Field(
        ...,
        description="Answer content (structure depends on answer_type)"
    )
    
    answered_at: Optional[datetime] = Field(
        None,
        description="Client timestamp when answer was provided"
    )


class SubmissionInput(BaseModel):
    """Input contract for exam submission.
    
    This request permanently seals the exam and makes answers immutable.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace ID for request tracking and audit"
    )
    
    student_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam identifier from exam structure"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier from Session & Timing Engine"
    )
    
    final_answers: List[Answer] = Field(
        ...,
        description="List of all answers for submission"
    )
    
    submission_reason: Literal["manual", "time_expired"] = Field(
        ...,
        description="Reason for submission (manual by student or automatic due to time expiry)"
    )
    
    client_timestamp: Optional[datetime] = Field(
        None,
        description="Client-side timestamp of submission request"
    )
    
    client_timezone: Optional[str] = Field(
        None,
        description="Client timezone for audit purposes"
    )
    
    request_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request context for audit trail"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable inputs
