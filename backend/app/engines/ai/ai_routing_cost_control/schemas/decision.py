"""Decision schemas for AI routing."""

from typing import Literal
from pydantic import BaseModel, Field


class RoutingDecision(BaseModel):
    """Routing decision type."""
    
    decision: Literal["cache_hit", "oss_model", "paid_model", "queued"] = Field(
        ...,
        description="Type of routing decision made"
    )
    
    reason: str = Field(
        ...,
        description="Human-readable reason for the decision"
    )


class CostPolicy(BaseModel):
    """Cost policy configuration for a request."""
    
    daily_limit_usd: float = Field(
        default=5.0,
        ge=0.0,
        description="Maximum USD spend per user per day"
    )
    
    monthly_limit_usd: float = Field(
        default=150.0,
        ge=0.0,
        description="Maximum USD spend per user per month"
    )
    
    school_monthly_limit_usd: float = Field(
        default=10000.0,
        ge=0.0,
        description="Maximum USD spend per school per month"
    )
    
    emergency_kill_switch: bool = Field(
        default=False,
        description="If True, all AI requests are queued (emergency cost control)"
    )
    
    allow_oss_models: bool = Field(
        default=True,
        description="If True, cheaper OSS models can be used"
    )
    
    auto_escalate_on_low_confidence: bool = Field(
        default=True,
        description="If True, low confidence OSS results escalate to paid models"
    )
    
    escalation_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold below which escalation occurs"
    )


class CacheDecision(BaseModel):
    """Cache lookup decision."""
    
    cache_hit: bool = Field(
        ...,
        description="True if cache contains valid result"
    )
    
    cache_key: str | None = Field(
        default=None,
        description="Cache key used for lookup"
    )
    
    cached_at: str | None = Field(
        default=None,
        description="ISO timestamp when result was cached"
    )
    
    cache_source: Literal["redis", "mongodb", "none"] | None = Field(
        default=None,
        description="Where the cached result was found"
    )


class ModelSelection(BaseModel):
    """Model selection decision."""
    
    selected_model: str = Field(
        ...,
        description="Model identifier (e.g., 'gpt-4o', 'sentence-transformers')"
    )
    
    model_tier: Literal["oss", "paid"] = Field(
        ...,
        description="Model tier (OSS = free/cheap, paid = premium)"
    )
    
    selection_reason: str = Field(
        ...,
        description="Reason for selecting this model"
    )
    
    estimated_cost_usd: float = Field(
        ...,
        ge=0.0,
        description="Estimated cost for this request in USD"
    )
