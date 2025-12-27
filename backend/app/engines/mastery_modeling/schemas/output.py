"""Output schema for Mastery Modeling Engine.

PHASE THREE: Mastery states with full justification traces.
"""

from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MasteryLevel(str, Enum):
    """Locked mastery level classifications."""
    NOT_INTRODUCED = "NOT_INTRODUCED"
    EMERGING = "EMERGING"
    DEVELOPING = "DEVELOPING"
    PROFICIENT = "PROFICIENT"
    MASTERED = "MASTERED"


class ClassificationMethod(str, Enum):
    """Method used for mastery classification."""
    AI_ASSISTED = "ai_assisted"
    RULE_BASED = "rule_based"
    INSUFFICIENT_DATA = "insufficient_data"


class TrendDirection(str, Enum):
    """Performance trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class ScoreSummary(BaseModel):
    """Aggregated performance metrics."""
    
    average_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average percentage score across attempts"
    )
    
    latest_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Most recent attempt score"
    )
    
    best_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Best score achieved"
    )
    
    attempt_count: int = Field(
        ...,
        ge=0,
        description="Number of attempts"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class MasteryJustification(BaseModel):
    """Full trace of how mastery was determined.
    
    CRITICAL: This provides complete explainability for regulatory review.
    """
    
    attempts_used: List[str] = Field(
        ...,
        description="List of exam attempt trace IDs used"
    )
    
    score_summary: ScoreSummary = Field(
        ...,
        description="Aggregated performance metrics"
    )
    
    trend_direction: TrendDirection = Field(
        ...,
        description="Performance trend over time"
    )
    
    confidence_weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Reliability score for this classification"
    )
    
    classification_method: ClassificationMethod = Field(
        ...,
        description="Method used (AI or rule-based)"
    )
    
    threshold_used: Optional[float] = Field(
        None,
        description="Threshold used for rule-based classification"
    )
    
    rationale: str = Field(
        ...,
        description="Human-readable explanation of classification"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class TopicMasteryState(BaseModel):
    """Mastery state for a single topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    
    mastery_level: MasteryLevel = Field(
        ...,
        description="Mastery classification"
    )
    
    justification: MasteryJustification = Field(
        ...,
        description="Full trace of how mastery was determined"
    )
    
    computed_at: datetime = Field(
        ...,
        description="When this state was computed"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class WeaknessSummary(BaseModel):
    """Summary of a weak topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    mastery_level: MasteryLevel = Field(..., description="Current mastery")
    priority_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Priority for remediation (0-1, higher = more urgent)"
    )
    trend: TrendDirection = Field(..., description="Trend direction")
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class StrengthSummary(BaseModel):
    """Summary of a strong topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    mastery_level: MasteryLevel = Field(..., description="Current mastery")
    stability_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Consistency of performance (0-1)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class MasteryModelingOutput(BaseModel):
    """Immutable output from Mastery Modeling Engine.
    
    Contains AI-assisted (OSS only) mastery classifications with
    full explainability and justification traces.
    """
    
    # Engine metadata
    trace_id: str = Field(..., description="Request trace ID")
    engine_name: str = Field(default="mastery_modeling", description="Engine identifier")
    engine_version: str = Field(..., description="Engine version")
    
    # Analysis scope
    user_id: str = Field(..., description="Student identifier")
    subject: str = Field(..., description="Subject code")
    computed_at: datetime = Field(..., description="Computation timestamp (UTC)")
    
    # Mastery states
    topic_mastery_states: List[TopicMasteryState] = Field(
        default_factory=list,
        description="Per-topic mastery classifications"
    )
    
    # Weakness & strength detection
    weaknesses: List[WeaknessSummary] = Field(
        default_factory=list,
        description="Topics needing attention (ranked by priority)"
    )
    
    strengths: List[StrengthSummary] = Field(
        default_factory=list,
        description="Topics with strong performance (ranked by stability)"
    )
    
    # Overall status
    total_topics_analyzed: int = Field(
        ...,
        ge=0,
        description="Number of topics with mastery classification"
    )
    
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in analysis"
    )
    
    # Audit trail
    source_analytics_snapshot_id: Optional[str] = Field(
        None,
        description="Analytics snapshot ID used as input"
    )
    
    mastery_snapshot_id: Optional[str] = Field(
        None,
        description="MongoDB mastery snapshot ID (set after persistence)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen =True  # Immutable output
