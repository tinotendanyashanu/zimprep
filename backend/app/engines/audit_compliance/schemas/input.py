"""Input schema for Audit & Compliance Engine.

Defines the aggregated payload contract from the Orchestrator.
This payload contains complete execution context for forensic logging.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EngineExecutionRecord(BaseModel):
    """Record of a single engine execution in the orchestrator flow.
    
    This captures what engine ran, when, and what it produced.
    """
    
    engine_name: str = Field(
        ...,
        description="Engine identifier (e.g., 'identity_subscription', 'submission')"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version that executed"
    )
    
    execution_order: int = Field(
        ...,
        ge=1,
        description="Order in orchestration sequence (1-indexed)"
    )
    
    started_at: datetime = Field(
        ...,
        description="Engine execution start timestamp (UTC)"
    )
    
    completed_at: datetime = Field(
        ...,
        description="Engine execution completion timestamp (UTC)"
    )
    
    success: bool = Field(
        ...,
        description="Whether engine execution succeeded"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Engine confidence score"
    )
    
    input_hash: str = Field(
        ...,
        description="SHA-256 hash of engine input (for replay verification)"
    )
    
    output_hash: str = Field(
        ...,
        description="SHA-256 hash of engine output (for integrity verification)"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if execution failed"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class AIEvidenceReference(BaseModel):
    """Reference to AI model invocation and decision.
    
    NO PII OR SECRETS - only model metadata and hashes.
    """
    
    engine_name: str = Field(
        ...,
        description="AI engine that made the call (e.g., 'reasoning_marking')"
    )
    
    model_id: str = Field(
        ...,
        description="Model identifier (e.g., 'gpt-4-turbo')"
    )
    
    model_version: str = Field(
        ...,
        description="Model version used"
    )
    
    prompt_hash: str = Field(
        ...,
        description="SHA-256 hash of the prompt (not the prompt itself)"
    )
    
    response_hash: str = Field(
        ...,
        description="SHA-256 hash of the model response"
    )
    
    invoked_at: datetime = Field(
        ...,
        description="Timestamp of model invocation (UTC)"
    )
    
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in decision"
    )
    
    validated: bool = Field(
        ...,
        description="Whether AI output was validated/vetoed"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class ValidationDecision(BaseModel):
    """Record of a validation or veto decision.
    
    Captures when AI output was reviewed and whether it was accepted.
    """
    
    validated_engine: str = Field(
        ...,
        description="Engine whose output was validated"
    )
    
    validator: str = Field(
        ...,
        description="Who/what validated (e.g., 'validation_engine', 'human')"
    )
    
    decision: str = Field(
        ...,
        description="Validation decision (e.g., 'approved', 'vetoed', 'modified')"
    )
    
    validated_at: datetime = Field(
        ...,
        description="Timestamp of validation (UTC)"
    )
    
    reason: Optional[str] = Field(
        None,
        description="Reason for veto or modification"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class PolicyMetadata(BaseModel):
    """Policy and configuration metadata.
    
    Captures the exact policy versions and configurations active
    at the time of exam execution.
    """
    
    marking_scheme_version: str = Field(
        ...,
        description="Version of marking scheme applied"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version for this exam"
    )
    
    exam_regulations_version: str = Field(
        ...,
        description="Version of exam regulations in effect"
    )
    
    platform_version: str = Field(
        ...,
        description="ZimPrep platform version"
    )
    
    policy_effective_date: datetime = Field(
        ...,
        description="When these policies became effective"
    )
    
    additional_policies: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional policy versions (key: policy_name, value: version)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class AuditComplianceInput(BaseModel):
    """Input contract for Audit & Compliance Engine.
    
    This is the aggregated payload from the Orchestrator containing
    complete execution context for forensic and regulatory logging.
    
    CRITICAL: This is a WRITE-ONLY engine. It never returns actionable
    data to the orchestrator - only confirmation of persistence.
    """
    
    trace_id: str = Field(
        ...,
        description="Global trace identifier for this exam execution"
    )
    
    student_id: str = Field(
        ...,
        description="Student identifier (should be pseudonymized for audit)"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam identifier"
    )
    
    session_id: str = Field(
        ...,
        description="Session identifier from Session & Timing Engine"
    )
    
    submission_id: str = Field(
        ...,
        description="Submission identifier from Submission Engine"
    )
    
    engine_execution_log: List[EngineExecutionRecord] = Field(
        ...,
        description="Ordered list of all engine executions in this flow"
    )
    
    ai_evidence_refs: List[AIEvidenceReference] = Field(
        default_factory=list,
        description="AI model invocation evidence (may be empty for non-AI flows)"
    )
    
    validation_decisions: List[ValidationDecision] = Field(
        default_factory=list,
        description="Validation/veto decisions (may be empty)"
    )
    
    feature_flags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of active feature flags at execution time"
    )
    
    policy_metadata: PolicyMetadata = Field(
        ...,
        description="Policy versions and configurations"
    )
    
    final_grade: Optional[str] = Field(
        None,
        description="Final grade assigned (if applicable)"
    )
    
    final_score: Optional[float] = Field(
        None,
        description="Final score achieved (if applicable)"
    )
    
    request_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request context (e.g., IP, user agent - logged only)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable inputs
