"""AI evidence schema structures.

Defines structures for recording AI model invocations and decisions.
NO PII OR SECRETS - only model metadata, hashes, and references.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ModelInvocation(BaseModel):
    """Record of a single AI model invocation.
    
    This captures WHAT model was called, WHEN, and WHAT it decided,
    without storing sensitive prompt/response content.
    """
    
    invocation_id: str = Field(
        ...,
        description="Unique invocation identifier"
    )
    
    trace_id: str = Field(
        ...,
        description="Global trace ID"
    )
    
    engine_name: str = Field(
        ...,
        description="AI engine that made this call"
    )
    
    model_id: str = Field(
        ...,
        description="Model identifier (e.g., 'gpt-4-turbo', 'claude-3-opus')"
    )
    
    model_version: str = Field(
        ...,
        description="Specific model version/snapshot"
    )
    
    prompt_hash: str = Field(
        ...,
        description="SHA-256 hash of the prompt (NOT the prompt itself)"
    )
    
    response_hash: str = Field(
        ...,
        description="SHA-256 hash of the model response"
    )
    
    invoked_at: datetime = Field(
        ...,
        description="Timestamp of invocation (UTC)"
    )
    
    duration_ms: float = Field(
        ...,
        ge=0.0,
        description="How long the invocation took (milliseconds)"
    )
    
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in its output"
    )
    
    temperature: Optional[float] = Field(
        None,
        description="Model temperature parameter (if applicable)"
    )
    
    tokens_used: Optional[int] = Field(
        None,
        ge=0,
        description="Total tokens consumed (if available)"
    )
    
    created_at: datetime = Field(
        ...,
        description="When this record was created (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class AIEvidence(BaseModel):
    """Complete AI evidence record for audit trail.
    
    Links AI decisions to exam outcomes for regulatory compliance.
    """
    
    evidence_id: str = Field(
        ...,
        description="Unique evidence record identifier"
    )
    
    trace_id: str = Field(
        ...,
        description="Global trace ID"
    )
    
    audit_record_id: str = Field(
        ...,
        description="Parent audit record ID"
    )
    
    model_invocation: ModelInvocation = Field(
        ...,
        description="Model invocation details"
    )
    
    validated: bool = Field(
        ...,
        description="Whether this AI output was validated"
    )
    
    validator: Optional[str] = Field(
        None,
        description="Who/what validated (e.g., 'validation_engine')"
    )
    
    validation_decision: Optional[str] = Field(
        None,
        description="Validation outcome (e.g., 'approved', 'vetoed')"
    )
    
    validation_reason: Optional[str] = Field(
        None,
        description="Reason for veto/modification (if applicable)"
    )
    
    validated_at: Optional[datetime] = Field(
        None,
        description="When validation occurred (UTC)"
    )
    
    created_at: datetime = Field(
        ...,
        description="When this evidence was recorded (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True
