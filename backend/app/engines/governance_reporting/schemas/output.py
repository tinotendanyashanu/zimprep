"""Output schema for Governance Reporting Engine.

PHASE FOUR: Regulator-safe governance and compliance reports.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.engines.governance_reporting.schemas.input import ReportType, ReportScope


class EscalationReason(BaseModel):
    """Reason for AI escalation to paid model."""
    
    reason: str = Field(..., description="Escalation reason")
    count: int = Field(..., ge=0, description="Occurrence count")
    
    class Config:
        frozen = True


class AIUsageSummary(BaseModel):
    """AI usage statistics."""
    
    total_ai_calls: int = Field(..., ge=0, description="Total AI API calls")
    oss_model_calls: int = Field(..., ge=0, description="Calls to OSS models")
    paid_model_calls: int = Field(..., ge=0, description="Calls to paid models")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    escalation_reasons: List[EscalationReason] = Field(
        default_factory=list,
        description="Reasons for escalation to paid models"
    )
    
    class Config:
        frozen = True


class VetoReason(BaseModel):
    """Reason for validation veto."""
    
    reason: str = Field(..., description="Veto reason (bounds/consistency/evidence/rubric)")
    count: int = Field(..., ge=0, description="Occurrence count")
    
    class Config:
        frozen = True


class ValidationStatistics(BaseModel):
    """Validation and veto statistics."""
    
    total_validations: int = Field(..., ge=0, description="Total validation checks")
    veto_count: int = Field(..., ge=0, description="Number of AI outputs vetoed")
    veto_rate: float = Field(..., ge=0.0, le=1.0, description="Veto rate (vetoes/total)")
    veto_reasons: List[VetoReason] = Field(
        default_factory=list,
        description="Breakdown by veto reason"
    )
    
    class Config:
        frozen = True


class AppealStatistics(BaseModel):
    """Appeal frequency and outcomes."""
    
    total_appeals: int = Field(..., ge=0, description="Total appeal requests")
    appeals_granted: int = Field(..., ge=0, description="Appeals granted")
    appeals_denied: int = Field(..., ge=0, description="Appeals denied")
    appeals_pending: int = Field(..., ge=0, description="Appeals pending")
    average_resolution_time_hours: float = Field(
        ...,
        ge=0.0,
        description="Average time to resolve appeal"
    )
    
    class Config:
        frozen = True


class ModelCostBreakdown(BaseModel):
    """Cost breakdown by AI model."""
    
    model_name: str = Field(..., description="AI model name")
    usage_count: int = Field(..., ge=0, description="Number of uses")
    total_cost: float = Field(..., ge=0.0, description="Total cost in USD")
    
    class Config:
        frozen = True


class CostTransparency(BaseModel):
    """Cost transparency summaries."""
    
    total_cost_usd: float = Field(..., ge=0.0, description="Total cost in USD")
    cost_per_student: float = Field(..., ge=0.0, description="Average cost per student")
    cost_per_exam: float = Field(..., ge=0.0, description="Average cost per exam")
    model_breakdown: List[ModelCostBreakdown] = Field(
        default_factory=list,
        description="Cost breakdown by model"
    )
    
    class Config:
        frozen = True


class TopicDifficulty(BaseModel):
    """Topic difficulty consistency indicator."""
    
    topic_id: str = Field(..., description="Topic identifier")
    variance_across_cohorts: float = Field(
        ...,
        ge=0.0,
        description="Variance in topic performance across cohorts"
    )
    
    class Config:
        frozen = True


class FairnessIndicators(BaseModel):
    """Fairness and bias indicators (DESCRIPTIVE ONLY).
    
    These are SIGNALS, not judgments. No automated bias conclusions.
    """
    
    mark_distribution_variance: float = Field(
        ...,
        ge=0.0,
        description="Variance in mark distribution across cohorts"
    )
    
    topic_difficulty_consistency: List[TopicDifficulty] = Field(
        default_factory=list,
        description="Topic difficulty variance across cohorts"
    )
    
    class Config:
        frozen = True


class FailureBreakdown(BaseModel):
    """System failure breakdown."""
    
    error_type: str = Field(..., description="Error type")
    count: int = Field(..., ge=0, description="Occurrence count")
    
    class Config:
        frozen = True


class SystemHealth(BaseModel):
    """System health metrics."""
    
    total_requests: int = Field(..., ge=0, description="Total requests processed")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    average_latency_ms: float = Field(..., ge=0.0, description="Average latency in ms")
    failure_breakdown: List[FailureBreakdown] = Field(
        default_factory=list,
        description="Breakdown by error type"
    )
    
    class Config:
        frozen = True


class GovernanceReportingOutput(BaseModel):
    """Immutable output from Governance Reporting Engine.
    
    Contains regulator-safe audit and compliance reports.
    This is READ-ONLY and contains NO student-identifiable data.
    """
    
    # Engine metadata
    trace_id: str = Field(..., description="Request trace ID")
    engine_name: str = Field(default="governance_reporting", description="Engine identifier")
    engine_version: str = Field(..., description="Engine version")
    
    # Report metadata
    report_id: str = Field(..., description="Unique report identifier")
    report_type: ReportType = Field(..., description="Type of report")
    scope: ReportScope = Field(..., description="Report scope")
    scope_id: Optional[str] = Field(None, description="Scope identifier")
    
    time_period_start: datetime = Field(..., description="Report period start (UTC)")
    time_period_end: datetime = Field(..., description="Report period end (UTC)")
    generated_at: datetime = Field(..., description="Report generation timestamp (UTC)")
    
    # Report sections (optional based on report_type)
    ai_usage_summary: Optional[AIUsageSummary] = Field(
        None,
        description="AI usage statistics"
    )
    
    validation_statistics: Optional[ValidationStatistics] = Field(
        None,
        description="Validation and veto statistics"
    )
    
    appeal_statistics: Optional[AppealStatistics] = Field(
        None,
        description="Appeal frequency and outcomes"
    )
    
    cost_transparency: Optional[CostTransparency] = Field(
        None,
        description="Cost transparency summaries"
    )
    
    fairness_indicators: Optional[FairnessIndicators] = Field(
        None,
        description="Fairness and bias indicators (descriptive only)"
    )
    
    system_health: Optional[SystemHealth] = Field(
        None,
        description="System health metrics"
    )
    
    # Persistence
    mongodb_id: Optional[str] = Field(
        None,
        description="MongoDB document ID (set after persistence)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable output
