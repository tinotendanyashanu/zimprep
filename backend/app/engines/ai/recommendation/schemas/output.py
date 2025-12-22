"""Output schema for Recommendation Engine.

MANDATORY OUTPUT CONTRACT:
All recommendations must be evidence-based, syllabus-aligned, and explainable.
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator


class PerformanceDiagnosis(BaseModel):
    """Diagnosis of weak area with evidence."""
    
    syllabus_area: str = Field(..., description="Exact syllabus topic/objective")
    weakness_description: str = Field(
        ...,
        description="Learning-focused description of weakness (not grading language)"
    )
    evidence: str = Field(
        ...,
        description="Specific marking evidence (e.g., 'missing definitions', 'incomplete explanations')"
    )
    impact_level: str = Field(
        ...,
        description="'high', 'medium', or 'low' - impact on overall scoring"
    )


class StudyRecommendation(BaseModel):
    """Prioritized study recommendation."""
    
    rank: int = Field(..., ge=1, description="Priority rank (1 = highest)")
    syllabus_reference: str = Field(..., description="Exact syllabus topic/objective reference")
    what_to_revise: str = Field(..., description="Specific content to study")
    why_it_matters: str = Field(..., description="Why this impacts scoring")
    estimated_time_hours: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated time to address this area"
    )


class PracticeSuggestion(BaseModel):
    """Targeted practice suggestion."""
    
    question_type: str = Field(
        ...,
        description="Type of question to practice (e.g., 'essay', 'structured', 'calculation')"
    )
    paper_section: str = Field(
        ...,
        description="Which paper/section to focus on (e.g., 'Paper 2 Section B')"
    )
    skills_to_focus: List[str] = Field(
        ...,
        description="Specific skills to practice (e.g., 'definitions', 'diagrams', 'explanations')"
    )
    example_topics: List[str] = Field(
        default_factory=list,
        description="Example topics to practice"
    )


class StudySession(BaseModel):
    """Single study session in a plan."""
    
    session_number: int = Field(..., ge=1)
    duration_hours: float = Field(..., gt=0)
    topics: List[str] = Field(..., min_items=1)
    goal: str = Field(..., description="Clear goal for this session")
    activities: List[str] = Field(
        ...,
        min_items=1,
        description="Specific activities to do"
    )


class StudyPlan(BaseModel):
    """Time-based study plan."""
    
    total_duration_weeks: int = Field(..., ge=1, description="Plan duration in weeks")
    sessions_per_week: int = Field(..., ge=1, le=7, description="Study sessions per week")
    sessions: List[StudySession] = Field(..., min_items=1)
    notes: Optional[str] = Field(
        None,
        description="Additional notes or adaptability guidance"
    )


class RecommendationOutput(BaseModel):
    """
    Complete output contract for Recommendation Engine.
    
    GUARANTEES TO ORCHESTRATOR:
    - All recommendations are evidence-based
    - All references are syllabus-aligned
    - All content is explainable
    - No scores or grades are modified
    - Output is advisory only
    """
    
    # Mandatory trace info
    trace_id: str = Field(..., description="Original orchestrator trace ID")
    engine_name: str = Field(default="recommendation", description="Engine identifier")
    engine_version: str = Field(default="1.0.0", description="Engine version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Core recommendations
    performance_diagnosis: List[PerformanceDiagnosis] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Top 3-5 weakest areas with evidence"
    )
    
    study_recommendations: List[StudyRecommendation] = Field(
        ...,
        min_items=1,
        description="Prioritized study recommendations"
    )
    
    practice_suggestions: List[PracticeSuggestion] = Field(
        ...,
        min_items=1,
        description="Targeted practice suggestions"
    )
    
    study_plan: Optional[StudyPlan] = Field(
        None,
        description="Personalized study plan (if data allows)"
    )
    
    motivation: str = Field(
        ...,
        description="Supportive, professional message emphasizing progress"
    )
    
    # Confidence and observability
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in recommendation quality (not student ability)"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Any limitations, assumptions, or caveats"
    )
    
    @validator("confidence_score")
    def validate_confidence(cls, v):
        """Ensure confidence score is reasonable."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
    
    @validator("performance_diagnosis")
    def validate_diagnosis_count(cls, v):
        """Ensure diagnosis is not overwhelming."""
        if len(v) > 5:
            raise ValueError("Performance diagnosis should have at most 5 items")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "trace_20250101_123456",
                "engine_name": "recommendation",
                "engine_version": "1.0.0",
                "timestamp": "2025-01-01T12:34:56Z",
                "performance_diagnosis": [
                    {
                        "syllabus_area": "3.2 Photosynthesis",
                        "weakness_description": "Incomplete understanding of light-dependent reactions",
                        "evidence": "Missing definitions of key terms, incomplete explanations of electron transport chain",
                        "impact_level": "high"
                    }
                ],
                "study_recommendations": [
                    {
                        "rank": 1,
                        "syllabus_reference": "3.2.1 Light-dependent reactions",
                        "what_to_revise": "Structure and function of photosystems I and II, electron transport chain, chemiosmosis",
                        "why_it_matters": "This topic accounts for 15% of Paper 2 marks and requires detailed explanations",
                        "estimated_time_hours": 3.0
                    }
                ],
                "practice_suggestions": [
                    {
                        "question_type": "structured",
                        "paper_section": "Paper 2 Section B",
                        "skills_to_focus": ["definitions", "explanations", "diagrams"],
                        "example_topics": ["photosynthesis", "respiration"]
                    }
                ],
                "study_plan": None,
                "motivation": "You have shown solid understanding in several areas. Focusing on photosynthesis and enzyme function will help you improve your grade.",
                "confidence_score": 0.85,
                "notes": None
            }
        }
