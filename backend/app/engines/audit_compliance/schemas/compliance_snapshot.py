"""Compliance snapshot schema structures.

Defines structures for capturing complete system state snapshots
to enable exact replay of exam execution environment.
"""

from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ComplianceSnapshot(BaseModel):
    """Complete system state snapshot for appeal reconstruction.
    
    This captures the EXACT configuration and policy state at the
    time of exam execution, enabling deterministic replay.
    """
    
    snapshot_id: str = Field(
        ...,
        description="Unique snapshot identifier"
    )
    
    trace_id: str = Field(
        ...,
        description="Global trace ID"
    )
    
    audit_record_id: str = Field(
        ...,
        description="Parent audit record ID"
    )
    
    # Platform and system versions
    platform_version: str = Field(
        ...,
        description="ZimPrep platform version (e.g., '2.4.1')"
    )
    
    python_version: str = Field(
        ...,
        description="Python runtime version"
    )
    
    engine_versions: Dict[str, str] = Field(
        ...,
        description="All engine versions (key: engine_name, value: version)"
    )
    
    # Policy versions
    marking_scheme_version: str = Field(
        ...,
        description="Marking scheme version applied"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version used"
    )
    
    exam_regulations_version: str = Field(
        ...,
        description="Exam regulations version in effect"
    )
    
    policy_effective_date: datetime = Field(
        ...,
        description="When current policies became effective"
    )
    
    additional_policy_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional policy versions (key: policy_name, value: version)"
    )
    
    # Feature flags snapshot
    feature_flags: Dict[str, Any] = Field(
        default_factory=dict,
        description="All active feature flags and their values"
    )
    
    # Configuration snapshot (sanitized - no secrets)
    configuration_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant configuration values (sanitized, no secrets)"
    )
    
    # AI model versions (if AI was used)
    ai_models_used: Dict[str, str] = Field(
        default_factory=dict,
        description="AI models used (key: engine_name, value: model_id)"
    )
    
    # Timestamp
    snapshot_taken_at: datetime = Field(
        ...,
        description="When this snapshot was captured (UTC)"
    )
    
    created_at: datetime = Field(
        ...,
        description="When this record was created (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable snapshot
