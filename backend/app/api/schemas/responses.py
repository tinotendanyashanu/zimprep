"""API response schemas for ZimPrep gateway.

All gateway endpoints MUST return these typed responses.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.contracts.engine_response import EngineResponse


class EngineExecutionResult(BaseModel):
    """Result of a single engine execution within a pipeline."""
    
    engine_name: str = Field(..., description="Name of the engine that was executed")
    success: bool = Field(..., description="Whether the engine executed successfully")
    data: Any | None = Field(None, description="Engine output data")
    error: str | None = Field(None, description="Error message if execution failed")
    
    # Execution metadata
    started_at: datetime = Field(..., description="When engine execution started")
    completed_at: datetime = Field(..., description="When engine execution completed")
    duration_ms: float = Field(..., description="Execution duration in milliseconds")
    
    # Trace information
    engine_version: str = Field(..., description="Version of the engine")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")


class PipelineExecutionResponse(BaseModel):
    """Response from a pipeline execution.
    
    This response contains:
    - Aggregated outputs from all engines
    - Full trace information
    - Immutable execution history
    """
    
    # Trace identification
    trace_id: str = Field(..., description="Unique trace ID for this request")
    request_id: str = Field(..., description="Unique request ID")
    
    # Pipeline information
    pipeline_name: str = Field(..., description="Name of the executed pipeline")
    success: bool = Field(..., description="Whether the entire pipeline succeeded")
    
    # Engine outputs (immutable aggregation)
    engine_outputs: dict[str, EngineExecutionResult] = Field(
        ...,
        description="Results from each engine in execution order"
    )
    
    # Timing
    started_at: datetime = Field(..., description="Pipeline start time")
    completed_at: datetime = Field(..., description="Pipeline completion time")
    total_duration_ms: float = Field(..., description="Total pipeline duration in milliseconds")
    
    # Error handling
    error: str | None = Field(None, description="Error message if pipeline failed")
    failed_engine: str | None = Field(None, description="Name of engine that caused failure")
    
    class Config:
        # Allow arbitrary types for EngineResponse
        arbitrary_types_allowed = True
