"""Output contracts for Background Processing Engine.

Provides machine-readable job execution results.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""
    
    SUCCESS = "success"
    FAILED = "failed"
    RETRIED = "retried"


class ResourceMetrics(BaseModel):
    """Resource consumption metrics for job execution."""
    
    cpu_usage_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average CPU usage during execution"
    )
    memory_usage_mb: float = Field(
        ...,
        ge=0.0,
        description="Peak memory usage in megabytes"
    )
    execution_time_ms: int = Field(
        ...,
        ge=0,
        description="Total execution time in milliseconds"
    )
    disk_io_operations: int = Field(
        default=0,
        ge=0,
        description="Number of disk I/O operations"
    )
    network_io_mb: float = Field(
        default=0.0,
        ge=0.0,
        description="Network I/O in megabytes"
    )


class ArtifactReference(BaseModel):
    """Reference to a persisted job artifact."""
    
    artifact_id: str = Field(
        ...,
        description="Unique artifact identifier"
    )
    artifact_type: str = Field(
        ...,
        description="Type of artifact (embeddings, aggregation, etc.)"
    )
    storage_location: str = Field(
        ...,
        description="Storage path or reference"
    )
    size_bytes: int = Field(
        ...,
        ge=0,
        description="Artifact size in bytes"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of artifact creation"
    )


class JobOutput(BaseModel):
    """Output contract for background job execution.
    
    Returns machine-readable job status and metadata.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace ID propagated from input"
    )
    job_id: str = Field(
        ...,
        description="Job ID propagated from input"
    )
    status: JobStatus = Field(
        ...,
        description="Final job execution status"
    )
    execution_time_ms: int = Field(
        ...,
        ge=0,
        description="Total job execution duration in milliseconds"
    )
    resource_metrics: ResourceMetrics = Field(
        ...,
        description="Resource consumption during execution"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Typed error code if job failed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Human-readable error message if job failed"
    )
    artifact_references: List[ArtifactReference] = Field(
        default_factory=list,
        description="References to artifacts created by this job"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts made"
    )
    completed_at: str = Field(
        ...,
        description="ISO timestamp of job completion"
    )
