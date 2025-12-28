"""Input schemas for Device Connectivity Awareness Engine.

PHASE SIX: Heartbeat and connectivity tracking inputs.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class HeartbeatInput(BaseModel):
    """Input for session heartbeat tracking.
    
    CRITICAL RULES:
    - client_timestamp is ADVISORY ONLY
    - Server calculates disconnect duration
    - Client cannot control timing decisions
    """
    
    session_id: str = Field(..., description="Active exam session ID")
    student_id: str = Field(..., description="Student identifier")
    device_id: str = Field(..., description="Unique device identifier")
    client_timestamp: datetime = Field(
        ..., description="Client timestamp (advisory only)"
    )
    network_type: Literal["wifi", "cellular", "ethernet", "unknown"] = Field(
        default="unknown", description="Network connection type"
    )
    signal_strength: Optional[int] = Field(
        default=None, ge=0, le=100, description="Signal strength percentage"
    )
    
    @field_validator("session_id", "student_id", "device_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate IDs are not empty."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()
