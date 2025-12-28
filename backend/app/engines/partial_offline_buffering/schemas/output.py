"""Output schemas for Partial Offline Buffering Engine.

PHASE SIX: These schemas define outputs from buffering and sync operations.
"""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class BufferAnswerOutput(BaseModel):
    """Output from buffering a single answer.
    
    Returns buffer confirmation with server timestamp.
    """
    
    buffer_id: str = Field(..., description="Unique buffer identifier")
    buffered_at: datetime = Field(..., description="Server timestamp when buffered")
    expires_at: datetime = Field(..., description="Buffer expiry time (24h default)")
    sync_status: Literal["pending", "syncing", "synced", "failed"] = Field(
        default="pending", description="Current sync status"
    )
    session_valid: bool = Field(..., description="Whether session is still open")
    buffer_count: int = Field(..., description="Total buffered answers for this session")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SyncedAnswer(BaseModel):
    """Details of a successfully synced answer."""
    
    buffer_id: str
    question_id: str
    synced_at: datetime  # Server timestamp
    was_duplicate: bool
    submission_order: int  # Order in final submission


class SyncBuffersOutput(BaseModel):
    """Output from syncing buffered answers.
    
    Returns sync results with server-side validation.
    """
    
    sync_id: str = Field(..., description="Unique sync operation identifier")
    session_id: str = Field(..., description="Session that was synced")
    synced_at: datetime = Field(..., description="Server timestamp of sync")
    total_submitted: int = Field(..., description="Total answers in batch")
    successfully_synced: int = Field(..., description="Successfully synced count")
    duplicates_skipped: int = Field(..., description="Duplicates skipped count")
    failed: int = Field(..., description="Failed to sync count")
    synced_answers: List[SyncedAnswer] = Field(
        default_factory=list, description="Details of synced answers"
    )
    session_still_open: bool = Field(..., description="Whether session remains open")
    trace_id: str = Field(..., description="Trace ID for audit continuity")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
