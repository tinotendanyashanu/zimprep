"""Output schema for Learning Analytics Engine.

PHASE THREE: Statistical learning metrics derived from historical performance.
"""

from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TrendDirection(str, Enum):
    """Direction of performance trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class TopicPerformanceTimeline(BaseModel):
    """Performance timeline for a single topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Human-readable topic name")
    
    attempt_timestamps: List[datetime] = Field(
        ...,
        description="Timestamps of all attempts for this topic"
    )
    
    attempt_scores: List[float] = Field(
        ...,
        description="Percentage scores for each attempt"
    )
    
    attempt_ids: List[str] = Field(
        ...,
        description="Trace IDs of attempts used in analysis"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class TrendAnalysis(BaseModel):
    """Trend analysis metrics."""
    
    slope: float = Field(
        ...,
        description="Linear regression slope (positive = improving)"
    )
    
    direction: TrendDirection = Field(
        ...,
        description="Trend direction classification"
    )
    
    volatility: float = Field(
        ...,
        ge=0.0,
        description="Standard deviation of scores (consistency measure)"
    )
    
    r_squared: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="R-squared value for trend fit quality"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class ConfidenceAdjustedScore(BaseModel):
    """Confidence-weighted performance metric."""
    
    raw_average: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Simple average of all attempts"
    )
    
    weighted_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence-weighted average"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this metric"
    )
    
    sample_size: int = Field(
        ...,
        ge=1,
        description="Number of attempts used"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class TopicAnalytics(BaseModel):
    """Complete analytics for a single topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    
    timeline: TopicPerformanceTimeline = Field(
        ...,
        description="Historical performance timeline"
    )
    
    rolling_average: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Rolling average performance (last 5 attempts or all if <5)"
    )
    
    trend: TrendAnalysis = Field(
        ...,
        description="Trend analysis metrics"
    )
    
    confidence_adjusted: ConfidenceAdjustedScore = Field(
        ...,
        description="Confidence-weighted performance"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class LearningAnalyticsOutput(BaseModel):
    """Immutable output from Learning Analytics Engine.
    
    Contains statistical analysis of historical performance.
    This is READ-ONLY and does NOT alter any exam marks.
    """
    
    # Engine metadata
    trace_id: str = Field(..., description="Request trace ID")
    engine_name: str = Field(default="learning_analytics", description="Engine identifier")
    engine_version: str = Field(..., description="Engine version for reproducibility")
    
    # Analysis scope
    user_id: str = Field(..., description="Student identifier")
    subject: str = Field(..., description="Subject code")
    analyzed_at: datetime = Field(..., description="Analysis timestamp (UTC)")
    
    # Analytics results
    topic_analytics: List[TopicAnalytics] = Field(
        default_factory=list,
        description="Per-topic analytics (empty if no data)"
    )
    
    total_attempts_analyzed: int = Field(
        ...,
        ge=0,
        description="Total number of exam attempts analyzed"
    )
    
    time_window_days: int = Field(
        ...,
        description="Analysis window in days"
    )
    
    # Status
    has_sufficient_data: bool = Field(
        ...,
        description="Whether sufficient data exists for reliable analysis"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Optional notes (e.g., why insufficient data)"
    )
    
    # Audit trail
    source_attempt_ids: List[str] = Field(
        default_factory=list,
        description="All attempt trace IDs used in this analysis"
    )
    
    snapshot_id: Optional[str] = Field(
        None,
        description="MongoDB snapshot ID (set after persistence)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable output
