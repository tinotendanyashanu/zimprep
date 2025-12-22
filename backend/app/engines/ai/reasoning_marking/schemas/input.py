"""Input schema for Reasoning & Marking Engine.

Defines the strict contract for inputs received from the Orchestrator.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, validator


class AnswerType(str, Enum):
    """Answer type enumeration."""
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"
    STRUCTURED = "structured"


class RubricPoint(BaseModel):
    """Atomic mark point from official rubric."""
    point_id: str = Field(..., description="Unique identifier for this rubric point")
    description: str = Field(..., description="What the student must demonstrate")
    marks: float = Field(..., gt=0, description="Marks awarded for this point")
    
    class Config:
        frozen = True  # Immutable


class RetrievedEvidence(BaseModel):
    """Evidence item from Retrieval Engine."""
    evidence_id: str = Field(..., description="Unique evidence identifier")
    content: str = Field(..., description="Evidence content/text")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    source_type: str = Field(..., description="Type of source (e.g., marking_scheme, examiner_report)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        frozen = True


class ExamContext(BaseModel):
    """Exam context information."""
    syllabus_version: str = Field(..., description="Syllabus version (e.g., 9184/1)")
    exam_board: str = Field(default="ZIMSEC", description="Exam board")
    exam_year: Optional[int] = Field(None, description="Reference exam year if applicable")
    topic: Optional[str] = Field(None, description="Topic/unit being assessed")
    

class ReasoningMarkingInput(BaseModel):
    """Input contract for Reasoning & Marking Engine.
    
    This schema enforces the mandatory fields required for auditable,
    evidence-based marking.
    
    CRITICAL RULES:
    - If retrieved_evidence is empty, engine MUST fail closed
    - official_rubric must contain at least one point
    - max_marks must match sum of all rubric point marks
    """
    
    # Core identifiers
    trace_id: str = Field(..., description="Orchestrator trace ID for end-to-end tracking")
    question_id: str = Field(..., description="Unique question identifier")
    
    # Exam metadata
    subject: str = Field(..., description="Subject (e.g., Mathematics, English)")
    paper: str = Field(..., description="Paper identifier (e.g., Paper 1, Paper 2)")
    answer_type: AnswerType = Field(..., description="Type of answer expected")
    
    # Student response
    raw_student_answer: str = Field(..., min_length=1, description="Raw student answer text")
    
    # Marking criteria
    max_marks: int = Field(..., gt=0, description="Maximum marks for this question")
    official_rubric: List[RubricPoint] = Field(..., min_items=1, description="Atomic mark points from official rubric")
    
    # Retrieved evidence (CRITICAL)
    retrieved_evidence: List[RetrievedEvidence] = Field(
        ..., 
        description="Evidence from Retrieval Engine - MUST NOT be empty"
    )
    
    # Context
    exam_context: ExamContext = Field(..., description="Exam context and syllabus information")
    
    # Engine versions for traceability
    engine_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Versions of upstream engines (embedding, retrieval)"
    )
    
    # Timestamps
    submission_timestamp: datetime = Field(..., description="When student submitted answer")
    
    @validator("retrieved_evidence")
    def evidence_must_not_be_empty(cls, v):
        """Fail closed if no evidence provided."""
        if not v or len(v) == 0:
            raise ValueError(
                "retrieved_evidence is empty - engine MUST fail closed. "
                "Cannot perform marking without authoritative evidence."
            )
        return v
    
    @validator("official_rubric")
    def rubric_must_be_valid(cls, v, values):
        """Validate rubric structure."""
        if not v or len(v) == 0:
            raise ValueError("official_rubric must contain at least one mark point")
        
        # Check for duplicate point_ids
        point_ids = [p.point_id for p in v]
        if len(point_ids) != len(set(point_ids)):
            raise ValueError("official_rubric contains duplicate point_ids")
        
        # Validate total marks match max_marks
        if "max_marks" in values:
            total_rubric_marks = sum(p.marks for p in v)
            if abs(total_rubric_marks - values["max_marks"]) > 0.01:  # Allow floating point tolerance
                raise ValueError(
                    f"Rubric marks ({total_rubric_marks}) do not match max_marks ({values['max_marks']})"
                )
        
        return v
    
    class Config:
        frozen = True  # Input is immutable
