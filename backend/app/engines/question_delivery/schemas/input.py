"""Input schema for Question Delivery Engine.

Defines the action-based contract for question navigation and delivery.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class QuestionDeliveryAction:
    """Navigation actions supported by the engine."""
    LOAD = "load"
    NEXT = "next"
    PREVIOUS = "previous"
    JUMP = "jump"
    RESUME = "resume"


class QuestionDeliveryInput(BaseModel):
    """Input contract for question delivery operations.
    
    All navigation decisions are server-authoritative and validated
    against current session progress and locking rules.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace ID for request tracking and audit"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier from Session & Timing Engine"
    )
    
    action: Literal["load", "next", "previous", "jump", "resume"] = Field(
        ...,
        description="Navigation action to perform"
    )
    
    requested_question_index: Optional[int] = Field(
        None,
        ge=0,
        description="Target question index for 'jump' action (0-indexed)"
    )
    
    client_state_hash: Optional[str] = Field(
        None,
        description="Hash of client-side state for tamper detection"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable inputs
