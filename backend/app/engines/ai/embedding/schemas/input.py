"""Input schema for Embedding Engine."""

from datetime import datetime
from typing import Union
from enum import Enum

from pydantic import BaseModel, Field


class AnswerType(str, Enum):
    """Enumeration of supported answer types."""
    
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"
    STRUCTURED = "structured"
    CALCULATION = "calculation"


class EmbeddingInput(BaseModel):
    """Input contract for Embedding Engine.
    
    All inputs are immutable and legally recorded. This payload has already
    passed through Identity, Exam Structure, Session, Question Delivery, and
    Submission engines.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    student_id: str = Field(
        ...,
        description="Pseudonymized student identifier"
    )
    
    subject: str = Field(
        ...,
        description="Subject name (e.g., 'Mathematics', 'Physics')"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier"
    )
    
    paper_id: str = Field(
        ...,
        description="Paper identifier"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier"
    )
    
    max_marks: int = Field(
        ...,
        ge=1,
        description="Maximum marks allocated for this question"
    )
    
    answer_type: AnswerType = Field(
        ...,
        description="Type of answer submitted"
    )
    
    raw_student_answer: Union[str, dict] = Field(
        ...,
        description="Raw student answer (string or structured JSON)"
    )
    
    submission_timestamp: datetime = Field(
        ...,
        description="ISO-8601 timestamp of submission"
    )
