"""Session and question data schemas."""

from typing import Literal
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    """Question item in a practice session."""
    
    question_id: str = Field(
        ...,
        description="Unique question identifier"
    )
    
    question_text: str = Field(
        ...,
        description="Question text (for display)"
    )
    
    question_type: Literal["multiple_choice", "calculation", "essay", "structured"] = Field(
        ...,
        description="Type of question"
    )
    
    topic_id: str = Field(
        ...,
        description="Primary topic for this question"
    )
    
    topic_name: str = Field(
        ...,
        description="Topic name (for display)"
    )
    
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Question difficulty level"
    )
    
    max_marks: int = Field(
        ...,
        ge=1,
        description="Maximum marks for this question"
    )
    
    estimated_minutes: int = Field(
        ...,
        ge=1,
        description="Estimated time to complete (minutes)"
    )
    
    order_index: int = Field(
        ...,
        ge=0,
        description="Position in session (0-based)"
    )


class PracticeSession(BaseModel):
    """Practice session with selected questions."""
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    session_type: Literal["targeted", "mixed", "exam_simulation"] = Field(
        ...,
        description="Type of practice session"
    )
    
    user_id: str = Field(
        ...,
        description="User this session is for"
    )
    
    subject: str = Field(
        ...,
        description="Subject for this session"
    )
    
    topics: list[str] = Field(
        ...,
        description="All topics included in session"
    )
    
    questions: list[QuestionItem] = Field(
        ...,
        description="Selected questions in order"
    )
    
    total_questions: int = Field(
        ...,
        ge=1,
        description="Total number of questions"
    )
    
    time_limit_minutes: int | None = Field(
        default=None,
        description="Time limit in minutes (None = untimed)"
    )
    
    estimated_duration_minutes: int = Field(
        ...,
        ge=1,
        description="Estimated total duration"
    )
    
    created_at: str = Field(
        ...,
        description="ISO timestamp when session was created"
    )
