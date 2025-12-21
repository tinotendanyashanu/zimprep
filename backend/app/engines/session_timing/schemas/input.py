"""Input schema for Session & Timing Engine.

Defines the action-based contract for session lifecycle operations.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SessionAction(str, Enum):
    """Supported session lifecycle actions.
    
    Each action triggers a specific state transition or query.
    """
    
    CREATE_SESSION = "create_session"
    """Create a new exam session."""
    
    START_SESSION = "start_session"
    """Start the timer for a created session."""
    
    PAUSE_SESSION = "pause_session"
    """Pause a running session."""
    
    RESUME_SESSION = "resume_session"
    """Resume a paused session."""
    
    HEARTBEAT = "heartbeat"
    """Check current session state and remaining time."""
    
    END_SESSION = "end_session"
    """Manually end a session."""


class SessionTimingInput(BaseModel):
    """Complete input contract for Session & Timing Engine.
    
    This is the contract expected by the engine's run() method.
    Action-based design allows single entry point for all operations.
    """
    
    action: SessionAction = Field(
        ...,
        description="Session lifecycle action to perform"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session identifier (required for all actions except CREATE_SESSION)"
    )
    
    # CREATE_SESSION fields
    exam_structure_hash: Optional[str] = Field(
        None,
        description="Hash of exam structure from Exam Structure Engine (required for CREATE_SESSION)"
    )
    
    time_limit_minutes: Optional[int] = Field(
        None,
        description="Official exam duration in minutes (required for CREATE_SESSION)",
        gt=0
    )
    
    user_id: str = Field(
        ...,
        description="ID of student taking exam (required for all actions)"
    )
    
    # Client metadata (logged but NEVER trusted for enforcement)
    client_timestamp: Optional[datetime] = Field(
        None,
        description="Client-reported timestamp (logged for debugging, never trusted)"
    )
    
    client_timezone: Optional[str] = Field(
        None,
        description="Client timezone (logged for context)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "action": "create_session",
                "session_id": None,
                "exam_structure_hash": "abc123...",
                "time_limit_minutes": 120,
                "user_id": "user_123",
                "client_timestamp": "2025-12-22T00:00:00Z",
                "client_timezone": "Africa/Harare"
            }
        }
