"""Audit record schema structures.

Defines the core audit record that gets persisted to MongoDB
for regulatory compliance and appeal reconstruction.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """Core audit record document.
    
    This is the primary forensic record stored in MongoDB.
    It is APPEND-ONLY and IMMUTABLE once written.
    """
    
    audit_record_id: str = Field(
        ...,
        description="Unique audit record identifier"
    )
    
    trace_id: str = Field(
        ...,
        description="Global trace ID linking all related records"
    )
    
    # Exam context (pseudonymized)
    student_id: str = Field(
        ...,
        description="Student identifier (should be hashed/pseudonymized)"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam identifier"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    
    submission_id: str = Field(
        ...,
        description="Submission identifier"
    )
    
    # Execution metadata
    total_engines_executed: int = Field(
        ...,
        ge=0,
        description="Total number of engines executed"
    )
    
    total_execution_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Total execution time across all engines (milliseconds)"
    )
    
    orchestration_started_at: datetime = Field(
        ...,
        description="When orchestration began (UTC)"
    )
    
    orchestration_completed_at: datetime = Field(
        ...,
        description="When orchestration completed (UTC)"
    )
    
    # Results metadata
    final_grade: Optional[str] = Field(
        None,
        description="Final grade assigned (if applicable)"
    )
    
    final_score: Optional[float] = Field(
        None,
        description="Final score achieved (if applicable)"
    )
    
    # Integrity and versioning
    input_fingerprint: str = Field(
        ...,
        description="SHA-256 hash of complete input payload"
    )
    
    output_fingerprint: str = Field(
        ...,
        description="SHA-256 hash of complete exam output"
    )
    
    platform_version: str = Field(
        ...,
        description="ZimPrep platform version"
    )
    
    marking_scheme_version: str = Field(
        ...,
        description="Marking scheme version applied"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version"
    )
    
    # Feature flags snapshot
    feature_flags_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Active feature flags at execution time"
    )
    
    # Request metadata (logged, not trusted)
    request_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request context"
    )
    
    # Timestamps (server-authoritative)
    created_at: datetime = Field(
        ...,
        description="When this audit record was created (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable once created
