"""Input schema for Recommendation Engine.

MANDATORY CONTEXT:
All data passed to this engine is validated, final, and immutable.
This engine MUST NOT question or re-interpret results.
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, validator


class TopicBreakdown(BaseModel):
    """Performance breakdown at topic level."""
    
    topic: str = Field(..., description="Syllabus topic identifier")
    topic_name: str = Field(..., description="Human-readable topic name")
    marks_earned: float = Field(..., ge=0, description="Marks earned in this topic")
    marks_possible: float = Field(..., gt=0, description="Total marks possible")
    percentage: float = Field(..., ge=0, le=100, description="Topic score percentage")


class PaperLevelScore(BaseModel):
    """Score breakdown at paper level."""
    
    paper_id: str = Field(..., description="Paper identifier (e.g., 'paper_1')")
    paper_name: str = Field(..., description="Paper name (e.g., 'Paper 1: Multiple Choice')")
    marks_earned: float = Field(..., ge=0)
    marks_possible: float = Field(..., gt=0)
    percentage: float = Field(..., ge=0, le=100)
    topic_breakdowns: List[TopicBreakdown] = Field(default_factory=list)


class FinalResults(BaseModel):
    """Final exam results (immutable, validated)."""
    
    overall_score: float = Field(..., ge=0, le=100, description="Final subject percentage")
    grade: str = Field(..., description="Official grade (A, B, C, D, E, U)")
    total_marks_earned: float = Field(..., ge=0)
    total_marks_possible: float = Field(..., gt=0)
    paper_scores: List[PaperLevelScore] = Field(..., min_items=1)
    

class MarkedQuestion(BaseModel):
    """Summary of a marked question."""
    
    question_id: str
    marks_earned: float = Field(..., ge=0)
    marks_possible: float = Field(..., gt=0)
    topics: List[str] = Field(default_factory=list)
    error_categories: List[str] = Field(
        default_factory=list,
        description="Common error types (e.g., 'incomplete_explanation', 'missing_definition')"
    )
    partially_achieved_points: List[str] = Field(
        default_factory=list,
        description="Rubric points that were partially met"
    )


class ValidatedMarkingSummary(BaseModel):
    """Summary of validated marking data."""
    
    weak_topics: List[str] = Field(
        default_factory=list,
        description="Topics where performance was below threshold"
    )
    common_error_categories: List[str] = Field(
        default_factory=list,
        description="Most frequent error types across all questions"
    )
    marked_questions: List[MarkedQuestion] = Field(default_factory=list)


class PastAttempt(BaseModel):
    """Historical exam attempt."""
    
    attempt_id: str
    exam_date: datetime
    subject: str
    overall_score: float = Field(..., ge=0, le=100)
    grade: str


class HistoricalPerformanceSummary(BaseModel):
    """Optional historical performance data."""
    
    past_attempts: List[PastAttempt] = Field(default_factory=list)
    improvement_trend: Optional[str] = Field(
        None,
        description="'improving', 'stable', 'declining', or None"
    )
    persistently_weak_topics: List[str] = Field(
        default_factory=list,
        description="Topics consistently weak across attempts"
    )


class Constraints(BaseModel):
    """Student-specific constraints."""
    
    available_study_hours_per_week: Optional[float] = Field(
        None,
        ge=0,
        description="Student's available study time"
    )
    next_exam_date: Optional[datetime] = Field(
        None,
        description="Date of next exam (if scheduled)"
    )
    subscription_tier: str = Field(
        ...,
        description="Student's subscription level (affects recommendation depth)"
    )
    max_recommendations: int = Field(
        5,
        ge=1,
        le=10,
        description="Maximum number of recommendations to generate"
    )


class RecommendationInput(BaseModel):
    """
    Complete input contract for Recommendation Engine.
    
    GUARANTEES FROM ORCHESTRATOR:
    - All scores are final and immutable
    - All AI marking has passed validation
    - All data is authoritative
    - Student identity is verified
    - Subscription entitlements are valid
    """
    
    trace_id: str = Field(..., description="Orchestrator trace identifier")
    student_id: str = Field(..., description="Verified student identifier")
    subject: str = Field(..., description="Subject code (e.g., 'biology_6030')")
    syllabus_version: str = Field(..., description="Syllabus version (e.g., '2025_v1')")
    
    final_results: FinalResults = Field(
        ...,
        description="Validated final results from Results Engine"
    )
    
    validated_marking_summary: ValidatedMarkingSummary = Field(
        ...,
        description="Summary of validated marking data from Validation Engine"
    )
    
    historical_performance_summary: Optional[HistoricalPerformanceSummary] = Field(
        None,
        description="Optional historical performance data"
    )
    
    constraints: Constraints = Field(..., description="Student-specific constraints")
    
    @validator("final_results")
    def validate_final_results(cls, v):
        """Ensure final results are structurally sound."""
        if v.overall_score < 0 or v.overall_score > 100:
            raise ValueError("Overall score must be between 0 and 100")
        
        if v.grade not in ["A", "B", "C", "D", "E", "U"]:
            raise ValueError(f"Invalid grade: {v.grade}")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "trace_20250101_123456",
                "student_id": "student_001",
                "subject": "biology_6030",
                "syllabus_version": "2025_v1",
                "final_results": {
                    "overall_score": 68.5,
                    "grade": "B",
                    "total_marks_earned": 137,
                    "total_marks_possible": 200,
                    "paper_scores": [
                        {
                            "paper_id": "paper_1",
                            "paper_name": "Paper 1: Multiple Choice",
                            "marks_earned": 35,
                            "marks_possible": 50,
                            "percentage": 70.0,
                            "topic_breakdowns": []
                        }
                    ]
                },
                "validated_marking_summary": {
                    "weak_topics": ["photosynthesis", "enzymes"],
                    "common_error_categories": ["incomplete_explanation", "missing_diagram"],
                    "marked_questions": []
                },
                "constraints": {
                    "subscription_tier": "premium",
                    "max_recommendations": 5
                }
            }
        }
