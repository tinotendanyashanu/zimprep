"""Appeal Reconstruction Output Schema.

LEGAL-GRADE OUTPUT: These schemas define the immutable, forensic output
for exam appeals. The `re_executed` field MUST always be False.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class MarkingPointExplanation(BaseModel):
    """Explanation of a single marking point decision.
    
    Provides human-readable detail on why marks were/weren't awarded.
    """
    
    point: str = Field(..., description="Description of the marking criterion")
    evidence_source: str = Field(..., description="Where the evidence came from (e.g., 'Marking Scheme 2024')")
    awarded: bool = Field(..., description="Whether this marking point was awarded")
    reason: str | None = Field(None, description="Human-readable explanation for the decision")


class QuestionReconstruction(BaseModel):
    """Reconstruction of a single question's marking.
    
    Contains all details needed to explain how marks were allocated.
    """
    
    question_id: str
    student_answer: str
    marking_points: list[MarkingPointExplanation]
    marks_awarded: int
    marks_available: int
    decided_by_engine: str = Field(..., description="Engine that made the marking decision")
    engine_version: str = Field(..., description="Version of the marking engine")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence at time of marking")


class AppealReconstructionOutput(BaseModel):
    """Complete appeal reconstruction output.
    
    LEGAL INVARIANTS:
    - re_executed MUST always be False (no AI re-execution during appeal)
    - ai_used reflects whether AI was used in ORIGINAL marking only
    - Output is IMMUTABLE once generated
    - audit_reference links back to original audit trail
    """
    
    # Identity
    trace_id: str = Field(..., description="Original exam attempt trace ID")
    candidate_number: str = Field(..., description="Student candidate number")
    subject: str = Field(..., description="Exam subject")
    paper_code: str = Field(..., description="Paper identifier")
    
    # Results (from ORIGINAL marking - NOT recalculated)
    final_score: int = Field(..., description="Original final score")
    grade: str = Field(..., description="Original grade awarded")
    
    # Reconstruction metadata
    reconstruction_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this reconstruction was generated"
    )
    
    # Legal flags (CRITICAL)
    ai_used: bool = Field(..., description="Whether AI was used in original marking")
    re_executed: Literal[False] = Field(
        default=False,
        description="MUST be False - proves no AI re-execution occurred"
    )
    
    # Audit linkage
    audit_reference: str = Field(..., description="Reference to original audit record")
    
    # Question-level reconstructions
    questions: list[QuestionReconstruction] = Field(
        default_factory=list,
        description="Detailed reconstruction for each question"
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "trace_id": "trace_abc123",
                "candidate_number": "ZP-000123",
                "subject": "Mathematics",
                "paper_code": "P2",
                "final_score": 62,
                "grade": "C",
                "reconstruction_timestamp": "2025-12-22T21:17:36Z",
                "ai_used": True,
                "re_executed": False,
                "audit_reference": "AUD-2025-000045",
                "questions": [
                    {
                        "question_id": "Q1",
                        "student_answer": "x = 3",
                        "marking_points": [
                            {
                                "point": "Correct solution for x",
                                "evidence_source": "Marking Scheme 2024",
                                "awarded": True,
                                "reason": "Answer matches expected solution"
                            }
                        ],
                        "marks_awarded": 2,
                        "marks_available": 2,
                        "decided_by_engine": "reasoning_marking",
                        "engine_version": "1.0.0",
                        "confidence": 0.92
                    }
                ]
            }
        }
