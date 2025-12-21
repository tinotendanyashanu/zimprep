"""Output schema for Session & Timing Engine.

Defines the authoritative session state contract.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Authoritative session lifecycle states.
    
    State transitions are strictly controlled by the state machine.
    """
    
    CREATED = "created"
    """Session exists but timer has not started."""
    
    RUNNING = "running"
    """Session is actively running, time is being tracked."""
    
    PAUSED = "paused"
    """Session is temporarily suspended, time is not advancing."""
    
    EXPIRED = "expired"
    """Session has exceeded time limit, no further actions allowed."""
    
    ENDED = "ended"
    """Session has been manually ended or submitted."""


class SessionTimingOutput(BaseModel):
    """Authoritative output for session state.
    
    All timestamps and time calculations are server-authoritative.
    Client timestamps are never used for enforcement.
    """
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    status: SessionStatus = Field(
        ...,
        description="Current session state"
    )
    
    # Authoritative server timestamps (ISO 8601 UTC)
    created_at: datetime = Field(
        ...,
        description="Server timestamp when session was created"
    )
    
    started_at: Optional[datetime] = Field(
        None,
        description="Server timestamp when session was started (null if not started)"
    )
    
    ended_at: Optional[datetime] = Field(
        None,
        description="Server timestamp when session ended (null if not ended)"
    )
    
    # Time tracking (all in seconds)
    time_limit_seconds: int = Field(
        ...,
        description="Total allowed time for exam in seconds",
        ge=0
    )
    
    elapsed_seconds: int = Field(
        ...,
        description="Time elapsed since start, excluding pauses",
        ge=0
    )
    
    remaining_seconds: int = Field(
        ...,
        description="Time remaining until expiry (0 if expired)",
        ge=0
    )
    
    # Pause tracking
    is_paused: bool = Field(
        ...,
        description="Whether session is currently paused"
    )
    
    total_pause_duration_seconds: int = Field(
        ...,
        description="Total duration of all pauses in seconds",
        ge=0
    )
    
    pause_count: int = Field(
        ...,
        description="Number of times session has been paused",
        ge=0
    )
    
    # Audit flags
    has_expired: bool = Field(
        ...,
        description="Whether session has exceeded time limit"
    )
    
    is_valid: bool = Field(
        ...,
        description="Whether session is in valid state for continued operations"
    )
    
    # Exam context
    exam_structure_hash: str = Field(
        ...,
        description="Hash linking to exam structure"
    )
    
    user_id: str = Field(
        ...,
        description="ID of student taking exam"
    )
    
    # Engine metadata
    confidence: float = Field(
        default=1.0,
        description="Engine confidence (always 1.0 for non-AI engine)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "status": "running",
                "created_at": "2025-12-22T00:00:00Z",
                "started_at": "2025-12-22T00:01:00Z",
                "ended_at": None,
                "time_limit_seconds": 7200,
                "elapsed_seconds": 300,
                "remaining_seconds": 6900,
                "is_paused": False,
                "total_pause_duration_seconds": 0,
                "pause_count": 0,
                "has_expired": False,
                "is_valid": True,
                "exam_structure_hash": "abc123...",
                "user_id": "user_123",
                "confidence": 1.0
            }
        }
