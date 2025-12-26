"""Output schema for AI Routing & Cost Control Engine."""

from typing import Any
from pydantic import BaseModel, Field

from app.engines.ai.ai_routing_cost_control.schemas.decision import (
    RoutingDecision,
    CacheDecision,
    ModelSelection,
)


class RoutingDecisionOutput(BaseModel):
    """Output contract for AI Routing & Cost Control Engine.
    
    Contains the routing decision and all metadata needed to execute
    or skip the AI request.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace identifier from input (for audit trail)"
    )
    
    routing_decision: RoutingDecision = Field(
        ...,
        description="Primary routing decision (cache/oss/paid/queued)"
    )
    
    cache_decision: CacheDecision = Field(
        ...,
        description="Cache lookup result"
    )
    
    model_selection: ModelSelection | None = Field(
        default=None,
        description="Model selection (None if cache hit)"
    )
    
    should_execute: bool = Field(
        ...,
        description="True if AI engine should execute now"
    )
    
    queue_for_later: bool = Field(
        ...,
        description="True if request should be queued due to cost limits"
    )
    
    cached_result: dict[str, Any] | None = Field(
        default=None,
        description="Cached AI result if cache hit (None otherwise)"
    )
    
    # Cost tracking
    cost_estimate_usd: float = Field(
        ...,
        ge=0.0,
        description="Estimated cost for this request in USD"
    )
    
    cumulative_cost_today_usd: float = Field(
        ...,
        ge=0.0,
        description="User's cumulative spend today in USD"
    )
    
    cumulative_cost_month_usd: float = Field(
        ...,
        ge=0.0,
        description="User's cumulative spend this month in USD"
    )
    
    cost_limit_remaining_usd: float = Field(
        ...,
        description="Remaining cost budget in USD (negative if exceeded)"
    )
    
    school_cost_remaining_usd: float = Field(
        ...,
        description="School's remaining monthly budget in USD"
    )
    
    # Metadata
    cache_key: str | None = Field(
        default=None,
        description="Cache key used (for storage if executing)"
    )
    
    escalation_triggered: bool = Field(
        default=False,
        description="True if this is an escalation from OSS to paid model"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for audit trail"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional routing metadata"
    )
