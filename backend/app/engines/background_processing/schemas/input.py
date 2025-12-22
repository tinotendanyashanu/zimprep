"""Input contracts for Background Processing Engine.

Enforces strict job configuration from orchestrator.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class TaskType(str, Enum):
    """Supported background task types."""
    
    MARKING_JOB = "marking_job"
    EMBEDDING_GENERATION = "embedding_generation"
    ANALYTICS_AGGREGATION = "analytics_aggregation"
    INFRASTRUCTURE_MAINTENANCE = "infrastructure_maintenance"


class JobPriority(str, Enum):
    """Job execution priority levels."""
    
    CRITICAL = "critical"  # System-critical operations
    HIGH = "high"  # User-blocking operations
    MEDIUM = "medium"  # Standard async work
    LOW = "low"  # Maintenance and cleanup


class RetryPolicy(BaseModel):
    """Retry configuration for job execution."""
    
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts"
    )
    backoff_strategy: str = Field(
        default="exponential",
        description="Backoff strategy: exponential or linear"
    )
    backoff_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Multiplier for exponential backoff"
    )
    initial_delay_ms: int = Field(
        default=1000,
        ge=100,
        le=60000,
        description="Initial retry delay in milliseconds"
    )
    
    @field_validator("backoff_strategy")
    @classmethod
    def validate_backoff_strategy(cls, v: str) -> str:
        """Validate backoff strategy."""
        valid_strategies = {"exponential", "linear"}
        if v not in valid_strategies:
            raise ValueError(f"backoff_strategy must be one of {valid_strategies}")
        return v


class JobInput(BaseModel):
    """Input contract for background job execution.
    
    All fields are mandatory and provided by the orchestrator.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace ID from orchestrator for full request traceability"
    )
    job_id: str = Field(
        ...,
        description="Unique job identifier for idempotency and tracking"
    )
    task_type: TaskType = Field(
        ...,
        description="Type of background task to execute"
    )
    origin_engine: str = Field(
        ...,
        description="Engine that requested this background job"
    )
    validated_payload: Dict[str, Any] = Field(
        ...,
        description="Pre-validated payload for task execution"
    )
    priority: JobPriority = Field(
        default=JobPriority.MEDIUM,
        description="Job execution priority"
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry configuration for this job"
    )
    requested_at: datetime = Field(
        ...,
        description="UTC timestamp when job was requested"
    )
    
    @field_validator("trace_id", "job_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate UUID format."""
        try:
            UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
        return v
    
    @field_validator("validated_payload")
    @classmethod
    def validate_payload_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure payload is not empty."""
        if not v:
            raise ValueError("validated_payload cannot be empty")
        return v
    
    @field_validator("origin_engine")
    @classmethod
    def validate_origin_engine(cls, v: str) -> str:
        """Validate origin engine name."""
        if not v or not v.strip():
            raise ValueError("origin_engine cannot be empty")
        return v.strip()
