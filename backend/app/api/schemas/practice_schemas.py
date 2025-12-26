"""Request/Response schemas for topic practice sessions."""

from typing import List, Dict, Literal
from pydantic import BaseModel, Field, field_validator


class TopicPracticeRequest(BaseModel):
    """Request to create a topic practice session."""
    
    student_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    primary_topics: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Primary topics to practice (1-5 topics)"
    )
    
    subject: str = Field(
        ...,
        description="Subject (e.g., Mathematics, Science, English)"
    )
    
    max_questions: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Maximum number of questions (5-50)"
    )
    
    difficulty_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"easy": 0.4, "medium": 0.4, "hard": 0.2},
        description="Difficulty distribution (must sum to ~1.0)"
    )
    
    session_type: Literal["targeted", "mixed", "exam_simulation"] = Field(
        default="targeted",
        description="Type of practice session"
    )
    
    include_related_topics: bool = Field(
        default=True,
        description="Whether to include semantically related topics"
    )
    
    time_limit_minutes: int | None = Field(
        default=None,
        description="Optional time limit in minutes"
    )
    
    @field_validator("difficulty_distribution")
    @classmethod
    def validate_difficulty_distribution(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate difficulty distribution sums to ~1.0."""
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Difficulty distribution must sum to ~1.0, got {total:.2f}")
        
        required_keys = {"easy", "medium", "hard"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"Must include easy, medium, hard")
        
        return v


class TopicPracticeResponse(BaseModel):
    """Response after creating practice session."""
    
    success: bool
    trace_id: str
    session_id: str
    total_questions: int
    topics_included: List[str]
    related_topics_added: List[str] = []
    estimated_duration_minutes: int
    difficulty_breakdown: Dict[str, int]
    questions: List[Dict] = []  # Question details
