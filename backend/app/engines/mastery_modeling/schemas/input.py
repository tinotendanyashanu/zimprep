"""Input schema for Mastery Modeling Engine.

PHASE THREE: AI-assisted mastery classification from analytics data.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.engines.learning_analytics.schemas.output import TopicAnalytics


class MasteryModelingInput(BaseModel):
    """Input contract for Mastery Modeling Engine.
    
    This engine classifies mastery levels from analytics data
    using OSS AI with deterministic fallback.
    """
    
    user_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    subject: str = Field(
        ...,
        description="Subject code"
    )
    
    topic_analytics: list[TopicAnalytics] = Field(
        ...,
        description="Topic analytics from Learning Analytics Engine"
    )
    
    time_decay_factor: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="How much to discount old attempts (0.0-1.0)"
    )
    
    use_ai_classification: bool = Field(
        default=True,
        description="Whether to use AI-assisted classification (OSS only)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable input
