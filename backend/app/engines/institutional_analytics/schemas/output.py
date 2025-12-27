"""Output schema for Institutional Analytics Engine.

PHASE FOUR: Cohort-level aggregated analytics outputs.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.engines.institutional_analytics.schemas.input import AnalyticsScope


class MasteryLevelCounts(BaseModel):
    """Count of students at each mastery level."""
    
    NOT_INTRODUCED: int = Field(default=0, ge=0)
    EMERGING: int = Field(default=0, ge=0)
    DEVELOPING: int = Field(default=0, ge=0)
    PROFICIENT: int = Field(default=0, ge=0)
    MASTERED: int = Field(default=0, ge=0)
    
    class Config:
        frozen = True


class MasteryLevelPercentages(BaseModel):
    """Percentage of students at each mastery level."""
    
    NOT_INTRODUCED: float = Field(default=0.0, ge=0.0, le=100.0)
    EMERGING: float = Field(default=0.0, ge=0.0, le=100.0)
    DEVELOPING: float = Field(default=0.0, ge=0.0, le=100.0)
    PROFICIENT: float = Field(default=0.0, ge=0.0, le=100.0)
    MASTERED: float = Field(default=0.0, ge=0.0, le=100.0)
    
    class Config:
        frozen = True


class TopicMasteryDistribution(BaseModel):
    """Distribution of mastery levels for a topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    
    mastery_level_counts: MasteryLevelCounts = Field(
        ...,
        description="Count of students at each mastery level"
    )
    
    mastery_level_percentages: MasteryLevelPercentages = Field(
        ...,
        description="Percentage of students at each mastery level"
    )
    
    class Config:
        frozen = True


class CohortAverageScore(BaseModel):
    """Average score statistics for a topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    
    average_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Mean score across cohort"
    )
    
    median_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Median score across cohort"
    )
    
    sample_size: int = Field(
        ...,
        ge=1,
        description="Number of student attempts"
    )
    
    class Config:
        frozen = True


class TrendIndicator(BaseModel):
    """Trend analysis for a topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    
    trend_direction: str = Field(
        ...,
        description="Trend direction: improving/stable/declining/insufficient_data"
    )
    
    cohort_volatility: float = Field(
        ...,
        ge=0.0,
        description="Standard deviation across cohort (consistency measure)"
    )
    
    class Config:
        frozen = True


class CoverageGap(BaseModel):
    """Topic with low practice coverage."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    
    practice_frequency: int = Field(
        ...,
        ge=0,
        description="Number of practice attempts"
    )
    
    last_practiced_at: Optional[datetime] = Field(
        None,
        description="Last practice timestamp (UTC)"
    )
    
    class Config:
        frozen = True


class InstitutionalAnalyticsOutput(BaseModel):
    """Immutable output from Institutional Analytics Engine.
    
    Contains cohort-level aggregated analytics with privacy safeguards.
    This is READ-ONLY and does NOT alter any student data.
    """
    
    # Engine metadata
    trace_id: str = Field(..., description="Request trace ID")
    engine_name: str = Field(default="institutional_analytics", description="Engine identifier")
    engine_version: str = Field(..., description="Engine version")
    
    # Scope metadata
    scope: AnalyticsScope = Field(..., description="Aggregation scope")
    scope_id: str = Field(..., description="Scope identifier")
    subject: Optional[str] = Field(None, description="Subject filter")
    
    # Cohort information
    cohort_size: int = Field(
        ...,
        ge=0,
        description="Number of students in cohort"
    )
    
    # Analytics results
    topic_mastery_distribution: List[TopicMasteryDistribution] = Field(
        default_factory=list,
        description="Mastery level distribution per topic"
    )
    
    cohort_average_scores: List[CohortAverageScore] = Field(
        default_factory=list,
        description="Average scores per topic"
    )
    
    trend_indicators: List[TrendIndicator] = Field(
        default_factory=list,
        description="Trend analysis per topic"
    )
    
    coverage_gaps: List[CoverageGap] = Field(
        default_factory=list,
        description="Topics with low practice coverage"
    )
    
    # Privacy metadata
    privacy_redacted: bool = Field(
        ...,
        description="Whether data was redacted due to small cohort size"
    )
    
    min_cohort_size_enforced: int = Field(
        ...,
        ge=3,
        description="Minimum cohort size threshold enforced"
    )
    
    # Computation metadata
    computed_at: datetime = Field(..., description="Computation timestamp (UTC)")
    time_window_days: int = Field(..., description="Analysis time window")
    
    # Audit trail
    source_snapshot_versions: List[str] = Field(
        default_factory=list,
        description="Source snapshot IDs used in aggregation"
    )
    
    snapshot_id: Optional[str] = Field(
        None,
        description="MongoDB snapshot ID (set after persistence)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable output
