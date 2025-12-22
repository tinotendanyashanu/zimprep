"""
Reporting & Analytics Engine - Parent/Guardian Report Schema

Defines the data structure for parent/guardian-facing reports.
Parents see a simplified, redacted view focusing on high-level trends.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SimplifiedTopicPerformance(BaseModel):
    """Simplified topic performance for parents"""
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    performance_level: str = Field(
        ...,
        description="Performance level (strong, satisfactory, needs_attention)"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage performance in this topic"
    )
    
    trend: Optional[str] = Field(
        default=None,
        description="Trend indicator (improving, stable, declining)"
    )


class ParentExamSummary(BaseModel):
    """High-level exam summary for parents"""
    
    exam_title: str = Field(
        ...,
        description="Title of the exam"
    )
    
    subject_name: str = Field(
        ...,
        description="Subject name"
    )
    
    completion_date: datetime = Field(
        ...,
        description="When the exam was completed"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall percentage (no raw marks shown)"
    )
    
    grade: str = Field(
        ...,
        description="Final grade achieved"
    )
    
    performance_summary: str = Field(
        ...,
        description="Written summary of overall performance"
    )


class ProgressIndicator(BaseModel):
    """Progress indicator over time"""
    
    period: str = Field(
        ...,
        description="Time period (e.g., 'Last 30 days', 'Last 3 months')"
    )
    
    trend: str = Field(
        ...,
        description="Overall trend (improving, stable, declining)"
    )
    
    average_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average percentage score in this period"
    )


class ParentReportData(BaseModel):
    """
    Complete data structure for a parent/guardian report.
    
    Parents receive:
    - Simplified exam summary (no raw marks)
    - Topic-level performance (categorized as strong/satisfactory/needs_attention)
    - High-level trends
    - Strengths and areas for improvement
    
    This view is intentionally redacted to avoid overwhelming parents
    with excessive detail while still providing actionable insights.
    """
    
    exam_summary: ParentExamSummary = Field(
        ...,
        description="Simplified exam summary"
    )
    
    topic_performance: List[SimplifiedTopicPerformance] = Field(
        default_factory=list,
        description="Simplified topic performance"
    )
    
    progress_indicators: List[ProgressIndicator] = Field(
        default_factory=list,
        description="High-level progress indicators"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="List of identified strengths (topics)"
    )
    
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="List of areas needing improvement (topics)"
    )
    
    guardian_notes: Optional[str] = Field(
        default=None,
        description="Optional notes for guardians about interpreting the report"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (excluding sensitive data)"
    )
    
    model_config = {
        "frozen": True,
    }
