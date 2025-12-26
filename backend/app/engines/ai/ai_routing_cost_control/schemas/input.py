"""Input schema for AI Routing & Cost Control Engine."""

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from app.engines.ai.ai_routing_cost_control.schemas.decision import CostPolicy


class RoutingDecisionInput(BaseModel):
    """Input contract for AI Routing & Cost Control Engine.
    
    This engine decides how AI requests should be routed:
    - Cache hit vs fresh execution
    - OSS model vs paid model
    - Execute now vs queue for later (cost limits)
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    request_type: Literal["marking", "embedding", "ocr", "recommendation"] = Field(
        ...,
        description="Type of AI request being routed"
    )
    
    prompt_hash: str = Field(
        ...,
        description="SHA-256 hash of the AI prompt (for cache key)"
    )
    
    evidence_hash: str = Field(
        ...,
        description="SHA-256 hash of evidence/context (for cache key)"
    )
    
    user_id: str = Field(
        ...,
        description="User identifier for per-user cost tracking"
    )
    
    school_id: str = Field(
        ...,
        description="School identifier for per-school cost tracking"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version (for cache invalidation on syllabus updates)"
    )
    
    cost_policy: CostPolicy = Field(
        default_factory=CostPolicy,
        description="Cost policy configuration for this request"
    )
    
    allow_cache: bool = Field(
        default=True,
        description="If False, bypass cache (useful for testing/debugging)"
    )
    
    user_tier: Literal["free", "premium", "enterprise"] = Field(
        default="free",
        description="User subscription tier (influences model selection)"
    )
    
    previous_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="If this is an escalation, the previous model's confidence score"
    )
    
    @field_validator("prompt_hash", "evidence_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        """Validate hash is non-empty and looks like SHA-256."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Hash cannot be empty")
        
        # SHA-256 should be 64 hex characters
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError(
                f"Hash must be 64-character SHA-256 hex string, got: {v[:20]}..."
            )
        
        return v.lower()
