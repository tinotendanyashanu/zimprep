"""Output schema for Practice Assembly Engine."""

from typing import Any
from pydantic import BaseModel, Field

from app.engines.core.practice_assembly.schemas.session import PracticeSession


class PracticeAssemblyOutput(BaseModel):
    """Output contract for Practice Assembly Engine."""
    
    trace_id: str = Field(
        ...,
        description="Trace identifier from input"
    )
    
    session_id: str = Field(
        ...,
        description="Generated session identifier"
    )
    
    practice_session: PracticeSession = Field(
        ...,
        description="Assembled practice session"
    )
    
    # Metadata
    topics_included: list[str] = Field(
        ...,
        description="All topic names included in session"
    )
    
    related_topics_added: list[str] = Field(
        default_factory=list,
        description="Topics added via Topic Intelligence expansion"
    )
    
    total_questions: int = Field(
        ...,
        ge=1,
        description="Total questions in session"
    )
    
    estimated_duration_minutes: int = Field(
        ...,
        ge=1,
        description="Estimated completion time"
    )
    
    difficulty_breakdown: dict[str, int] = Field(
        ...,
        description="Actual count per difficulty level"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for audit trail"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional assembly metadata"
    )
