"""Output schema for Audit & Compliance Engine.

Defines the immutable confirmation returned to orchestrator after
audit records have been persisted.
"""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class AuditComplianceOutput(BaseModel):
    """Immutable audit persistence confirmation.
    
    This is NOT actionable data - it is proof of logging only.
    The orchestrator should observe this for monitoring but should
    NOT block exam results if audit fails.
    """
    
    audit_record_id: str = Field(
        ...,
        description="Unique audit record identifier (for retrieval)"
    )
    
    trace_id: str = Field(
        ...,
        description="Original request trace ID"
    )
    
    persistence_status: Literal["success", "partial", "failed"] = Field(
        ...,
        description="Status of audit record persistence"
    )
    
    records_written: int = Field(
        ...,
        ge=0,
        description="Number of audit records successfully written to database"
    )
    
    timestamp: datetime = Field(
        ...,
        description="Server timestamp when audit record was created (UTC)"
    )
    
    integrity_hash: str = Field(
        ...,
        description="SHA-256 hash of complete audit record (for tamper detection)"
    )
    
    ai_evidence_count: int = Field(
        default=0,
        ge=0,
        description="Number of AI evidence records written"
    )
    
    validation_decision_count: int = Field(
        default=0,
        ge=0,
        description="Number of validation decisions recorded"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Engine confidence (always 1.0 - no computed logic)"
    )
    
    notes: str = Field(
        default="",
        description="Additional notes or warnings (if any)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable output
