"""Cost metadata schema for audit trail integration.

PHASE TWO: Schema for tracking AI costs in audit records.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AICostMetadata(BaseModel):
    """AI cost metadata for a single AI call.
    
    This captures the financial cost of AI model invocations
    for observability and cost attribution.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace ID linking this cost to the execution"
    )
    
    engine_name: str = Field(
        ...,
        description="Engine that made the AI call (e.g., 'reasoning_marking')"
    )
    
    pipeline_name: str = Field(
        ...,
        description="Pipeline that triggered this AI call"
    )
    
    model: str = Field(
        ...,
        description="AI model used (e.g., 'gpt-4o-2024-08-06')"
    )
    
    request_type: str = Field(
        ...,
        description="Type of AI request (e.g., 'marking', 'retrieval', 'embedding')"
    )
    
    tokens_input: int = Field(
        ...,
        ge=0,
        description="Number of input tokens"
    )
    
    tokens_output: int = Field(
        ...,
        ge=0,
        description="Number of output tokens"
    )
    
    cost_usd: float = Field(
        ...,
        ge=0.0,
        description="Estimated cost in USD"
    )
    
    cache_hit: bool = Field(
        ...,
        description="Whether this was a cache hit (cost=$0)"
    )
    
    cache_source: Optional[str] = Field(
        None,
        description="Cache source if cache hit ('redis', 'mongodb', or None)"
    )
    
    escalation_reason: Optional[str] = Field(
        None,
        description="Reason for escalating to paid model (if applicable)"
    )
    
    invoked_at: datetime = Field(
        ...,
        description="When the AI call was made (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable
