"""Input schema for Learning Analytics Engine.

PHASE THREE: Read-only statistical analysis of historical performance.
"""

from typing import Optional
from pydantic import BaseModel, Field


class LearningAnalyticsInput(BaseModel):
    """Input contract for Learning Analytics Engine.
    
    This engine analyzes historical exam performance to compute
    longitudinal learning metrics.
    """
    
    user_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    subject: str = Field(
        ...,
        description="Subject code (e.g., MATHEMATICS_4024)"
    )
    
    topic_id: Optional[str] = Field(
        None,
        description="Optional topic identifier for filtered analysis"
    )
    
    time_window_days: int = Field(
        default=365,
        ge=1,
        le=1825,  # Max 5 years
        description="Analysis time window in days (default: 365)"
    )
    
    min_attempts: int = Field(
        default=2,
        ge=1,
        description="Minimum attempts required for analysis (default: 2)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable input
