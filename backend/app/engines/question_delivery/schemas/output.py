"""Output schema for Question Delivery Engine.

Defines the authoritative navigation state returned to the orchestrator.
"""

from typing import List
from pydantic import BaseModel, Field


class NavigationCapabilities(BaseModel):
    """Navigation capabilities for current state."""
    
    can_next: bool = Field(
        ...,
        description="Whether student can navigate to next question"
    )
    
    can_previous: bool = Field(
        ...,
        description="Whether student can navigate to previous question"
    )
    
    can_jump: bool = Field(
        ...,
        description="Whether student can jump to arbitrary questions"
    )


class QuestionDeliveryOutput(BaseModel):
    """Authoritative navigation state output.
    
    This is the single source of truth for question delivery state.
    All fields are deterministic and replayable from snapshots.
    """
    
    trace_id: str = Field(
        ...,
        description="Request trace ID for audit trail"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    
    current_question_index: int = Field(
        ...,
        ge=0,
        description="Current question index (0-indexed)"
    )
    
    allowed_question_indices: List[int] = Field(
        ...,
        description="List of question indices student can access"
    )
    
    locked_questions: List[int] = Field(
        default_factory=list,
        description="List of locked question indices (immutable once locked)"
    )
    
    navigation: NavigationCapabilities = Field(
        ...,
        description="Current navigation capabilities"
    )
    
    snapshot_saved: bool = Field(
        ...,
        description="Whether progress snapshot was successfully persisted"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in output (1.0 = clean execution, lower if degraded)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make output immutable
