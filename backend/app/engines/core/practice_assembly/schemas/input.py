"""Input schema for Practice Assembly Engine."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class PracticeAssemblyInput(BaseModel):
    """Input contract for Practice Assembly Engine."""
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    user_id: str = Field(
        ...,
        description="User ID for personalization"
    )
    
    session_type: Literal["targeted", "mixed", "exam_simulation"] = Field(
        ...,
        description="Type of practice session to create"
    )
    
    # Topic selection
    primary_topic_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Primary topics to practice"
    )
    
    include_related_topics: bool = Field(
        default=True,
        description="Whether to expand topics using Topic Intelligence"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity for related topic expansion"
    )
    
    # Question criteria
    subject: str = Field(
        ...,
        description="Subject for the practice session"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version to use"
    )
    
    difficulty_distribution: dict[str, float] = Field(
        default_factory=lambda: {"easy": 0.4, "medium": 0.4, "hard": 0.2},
        description="Target difficulty distribution (must sum to ~1.0)"
    )
    
    # Session configuration
    max_questions: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of questions"
    )
    
    time_limit_minutes: int | None = Field(
        default=None,
        description="Time limit for session (None = untimed)"
    )
    
    # Personalization
    exclude_recent_days: int = Field(
        default=7,
        ge=0,
        description="Exclude questions attempted in last N days"
    )
    
    preferred_question_types: list[str] | None = Field(
        default=None,
        description="Preferred question types (None = all types)"
    )
    
    @field_validator("difficulty_distribution")
    @classmethod
    def validate_difficulty_distribution(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate difficulty distribution sums to ~1.0."""
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(
                f"Difficulty distribution must sum to ~1.0, got {total:.2f}"
            )
        
        # Must have easy, medium, hard
        required_keys = {"easy", "medium", "hard"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(
                f"Difficulty distribution must include {required_keys}, got {set(v.keys())}"
            )
        
        return v
