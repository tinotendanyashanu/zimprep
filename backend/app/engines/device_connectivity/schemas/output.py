"""Output schemas for Device Connectivity Awareness Engine.

PHASE SIX: Connectivity state and session status outputs.
"""

from datetime import datetime
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class ConnectivityState(str, Enum):
    """Device connectivity states.
    
    State transitions determine system behavior:
    - CONNECTED: Normal operation, no buffering needed
    - SHORT_DISCONNECT: <30s, buffer locally, continue
    - MEDIUM_DISCONNECT: 30s-2min, buffer + warn user
    - LONG_DISCONNECT: >2min, force pause, must reconnect
    """
    
    CONNECTED = "connected"
    SHORT_DISCONNECT = "short_disconnect"
    MEDIUM_DISCONNECT = "medium_disconnect"
    LONG_DISCONNECT = "long_disconnect"


class HeartbeatOutput(BaseModel):
    """Output from heartbeat processing.
    
    Server-authoritative connectivity assessment and instructions.
    """
    
    connectivity_state: ConnectivityState = Field(
        ..., description="Current connectivity state"
    )
    session_status: Literal["active", "paused", "closed"] = Field(
        ..., description="Current session status (server-authoritative)"
    )
    time_remaining_seconds: Optional[int] = Field(
        default=None, description="Exam time remaining (None if session closed/paused)"
    )
    disconnect_duration_seconds: int = Field(
        default=0, description="Seconds since last heartbeat"
    )
    should_buffer: bool = Field(
        ..., description="Whether client should buffer answers locally"
    )
    should_warn: bool = Field(
        ..., description="Whether client should show connectivity warning"
    )
    should_pause: bool = Field(
        ..., description="Whether client should pause (session paused server-side)"
    )
    last_heartbeat_at: Optional[datetime] = Field(
        default=None, description="Server timestamp of last heartbeat"
    )
    current_server_time: datetime = Field(
        ..., description="Current server time (for client sync)"
    )
    trace_id: str = Field(..., description="Trace ID for audit")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
