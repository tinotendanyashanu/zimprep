"""
Reporting & Analytics Engine - School/Institution Report Schema

Defines the data structure for school administrator reports.
School admins see aggregated cohort statistics and class-level trends.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StudentPerformanceSummary(BaseModel):
    """Summary of a single student's performance (anonymized if needed)"""
    
    student_id: UUID = Field(
        ...,
        description="Student ID"
    )
    
    student_name: Optional[str] = Field(
        default=None,
        description="Student name (may be anonymized)"
    )
    
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage score"
    )
    
    grade: str = Field(
        ...,
        description="Grade achieved"
    )
    
    topics_strong: List[str] = Field(
        default_factory=list,
        description="Topics where student is strong"
    )
    
    topics_weak: List[str] = Field(
        default_factory=list,
        description="Topics needing improvement"
    )


class CohortStatistics(BaseModel):
    """Statistical analysis of cohort performance"""
    
    total_students: int = Field(
        ...,
        ge=0,
        description="Total number of students in cohort"
    )
    
    average_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Mean percentage score"
    )
    
    median_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Median percentage score"
    )
    
    std_deviation: float = Field(
        ...,
        ge=0,
        description="Standard deviation of scores"
    )
    
    highest_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Highest score achieved"
    )
    
    lowest_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Lowest score achieved"
    )
    
    grade_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of students per grade (e.g., {'A': 15, 'B': 20})"
    )


class TopicAnalysis(BaseModel):
    """Analysis of performance on a specific topic across the cohort"""
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    average_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average score for this topic"
    )
    
    students_above_threshold: int = Field(
        ...,
        ge=0,
        description="Number of students scoring above pass threshold"
    )
    
    students_below_threshold: int = Field(
        ...,
        ge=0,
        description="Number of students scoring below pass threshold"
    )
    
    difficulty_level: str = Field(
        ...,
        description="Perceived difficulty (easy, moderate, challenging)"
    )


class ClassTrend(BaseModel):
    """Trend data for a class over time"""
    
    period: str = Field(
        ...,
        description="Time period (e.g., 'Term 1', 'Quarter 2')"
    )
    
    average_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average class score in this period"
    )
    
    trend_direction: str = Field(
        ...,
        description="Trend direction (improving, stable, declining)"
    )
    
    student_count: int = Field(
        ...,
        ge=0,
        description="Number of students in this period"
    )


class SchoolReportData(BaseModel):
    """
    Complete data structure for a school/institution report.
    
    School administrators receive:
    - Cohort-level statistics
    - Individual student summaries
    - Topic analysis across the cohort
    - Class trends over time
    - Actionable insights for curriculum planning
    
    This view supports institutional decision-making and
    identifies systemic strengths/weaknesses.
    """
    
    exam_title: str = Field(
        ...,
        description="Title of the exam"
    )
    
    subject_name: str = Field(
        ...,
        description="Subject name"
    )
    
    cohort_statistics: CohortStatistics = Field(
        ...,
        description="Statistical summary of cohort performance"
    )
    
    student_summaries: List[StudentPerformanceSummary] = Field(
        default_factory=list,
        description="Individual student performance summaries"
    )
    
    topic_analysis: List[TopicAnalysis] = Field(
        default_factory=list,
        description="Analysis by topic across cohort"
    )
    
    class_trends: List[ClassTrend] = Field(
        default_factory=list,
        description="Historical trends for the class/cohort"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Data-driven recommendations for intervention"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    model_config = {
        "frozen": True,
    }
