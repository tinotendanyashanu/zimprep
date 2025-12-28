"""Input schemas for Partial Offline Buffering Engine.

PHASE SIX: These schemas define inputs for answer buffering and sync operations.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


class BufferAnswerInput(BaseModel):
    """Input for buffering a single answer during connectivity loss.
    
    CRITICAL RULES:
    - client_timestamp is ADVISORY ONLY
    - Server timestamp is canonical
    - Session validity checked on sync, not on buffer
    """
    
    session_id: str = Field(..., description="Active exam session ID")
    student_id: str = Field(..., description="Student identifier")
    question_id: str = Field(..., description="Question being answered")
    answer_content: str = Field(..., description="Student's answer text")
    answer_type: Literal["text", "essay", "multiple_choice", "handwriting"] = Field(
        ..., description="Type of answer"
    )
    client_timestamp: datetime = Field(
        ..., description="Client-side timestamp (advisory only)"
    )
    device_id: str = Field(..., description="Unique device identifier")
    buffered_payload_hash: str = Field(
        ..., description="SHA256 hash of payload for deduplication"
    )
    
    @field_validator("answer_content")
    @classmethod
    def validate_answer_content(cls, v: str) -> str:
        """Validate answer content is not empty."""
        if not v or not v.strip():
            raise ValueError("Answer content cannot be empty")
        return v
    
    @field_validator("buffered_payload_hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Validate hash format."""
        if len(v) != 64:  # SHA256 hex length
            raise ValueError("Invalid SHA256 hash length")
        return v.lower()


class BufferedAnswerBatch(BaseModel):
    """Single buffered answer in a batch sync."""
    
    buffer_id: str
    question_id: str
    answer_content: str
    answer_type: str
    client_timestamp: datetime
    buffered_payload_hash: str


class SyncBuffersInput(BaseModel):
    """Input for syncing buffered answers on reconnect.
    
    CRITICAL RULES:
    - Server validates session is still open
    - Server timestamps all synced answers
    - Duplicates detected via buffered_payload_hash
    - trace_id continuity preserved
    """
    
    session_id: str = Field(..., description="Session to sync buffers for")
    student_id: str = Field(..., description="Student identifier")
    device_id: str = Field(..., description="Device requesting sync")
    buffered_answers: List[BufferedAnswerBatch] = Field(
        ..., description="Batch of buffered answers to sync"
    )
    
    @field_validator("buffered_answers")
    @classmethod
    def validate_batch_size(cls, v: List[BufferedAnswerBatch]) -> List[BufferedAnswerBatch]:
        """Enforce batch size limits."""
        if len(v) > 100:  # Max buffer size
            raise ValueError("Batch size exceeds maximum of 100 answers")
        if len(v) == 0:
            raise ValueError("Cannot sync empty batch")
        return v
