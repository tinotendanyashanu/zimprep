"""
Reporting & Analytics Engine - Student Report Schema

Defines the data structure for student-facing reports.
Students see full detail including question-level breakdown.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionBreakdown(BaseModel):
    """Breakdown of a single question"""
    
    question_number: int = Field(
        ...,
        ge=1,
        description="Question number within the paper"
    )
    
    question_text: str = Field(
        ...,
        description="The question text (may be truncated)"
    )
    
    marks_awarded: float = Field(
        ...,
        ge=0,
        description="Marks awarded for this question"
    )
    
    marks_available: float = Field(
        ...,
        ge=0,
        description="Total marks available for this question"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage score for this question"
    )
    
    topic: str = Field(
        ...,
        description="Topic/subtopic this question belongs to"
    )
    
    feedback_summary: Optional[str] = Field(
        default=None,
        description="Brief feedback from marking engine"
    )


class TopicPerformance(BaseModel):
    """Aggregated performance for a topic"""
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    questions_attempted: int = Field(
        ...,
        ge=0,
        description="Number of questions attempted in this topic"
    )
    
    marks_earned: float = Field(
        ...,
        ge=0,
        description="Total marks earned in this topic"
    )
    
    marks_available: float = Field(
        ...,
        ge=0,
        description="Total marks available in this topic"
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


class HistoricalDataPoint(BaseModel):
    """A single data point in historical performance"""
    
    exam_session_id: UUID = Field(
        ...,
        description="ID of the exam session"
    )
    
    exam_date: datetime = Field(
        ...,
        description="When the exam was taken"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage score achieved"
    )
    
    grade: str = Field(
        ...,
        description="Grade achieved"
    )


class ExamSummary(BaseModel):
    """High-level summary of the exam"""
    
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
    
    total_marks: float = Field(
        ...,
        ge=0,
        description="Total marks awarded"
    )
    
    total_available: float = Field(
        ...,
        ge=0,
        description="Total marks available"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall percentage"
    )
    
    grade: str = Field(
        ...,
        description="Final grade achieved"
    )


class StudentReportData(BaseModel):
    """
    Complete data structure for a student report.
    
    Students receive:
    - Full exam summary
    - Question-by-question breakdown
    - Topic-level performance analysis
    - Historical trends (if available)
    """
    
    exam_summary: ExamSummary = Field(
        ...,
        description="High-level exam summary"
    )
    
    question_breakdown: List[QuestionBreakdown] = Field(
        default_factory=list,
        description="Detailed breakdown of each question"
    )
    
    topic_performance: List[TopicPerformance] = Field(
        default_factory=list,
        description="Performance aggregated by topic"
    )
    
    historical_performance: List[HistoricalDataPoint] = Field(
        default_factory=list,
        description="Historical performance data for trend analysis"
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="List of identified strengths (topics)"
    )
    
    areas_for_improvement: List[str] = Field(
        default_factory=list,
        description="List of areas needing improvement (topics)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    model_config = {
        "frozen": True,
    }
