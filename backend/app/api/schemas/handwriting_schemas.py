"""Request/Response schemas for handwriting exam submissions."""

from typing import List, Literal
from pydantic import BaseModel, Field


class HandwritingAnswer(BaseModel):
    """Single handwritten answer with image reference."""
    
    question_id: str = Field(
        ...,
        description="Question identifier"
    )
    
    image_reference: str = Field(
        ...,
        description="Base64-encoded image or URL to uploaded image"
    )
    
    question_type: Literal["calculation", "essay", "structured"] = Field(
        default="calculation",
        description="Type of question for OCR optimization"
    )
    
    expected_format: Literal["step_by_step", "final_answer", "paragraph"] = Field(
        default="step_by_step",
        description="Expected answer format"
    )


class HandwritingExamSubmission(BaseModel):
    """Complete handwriting exam submission."""
    
    student_id: str = Field(
        ...,
        description="Student identifier"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam identifier"
    )
    
    answers: List[HandwritingAnswer] = Field(
        ...,
        min_length=1,
        description="List of handwritten answers with images"
    )
    
    session_id: str | None = Field(
        default=None,
        description="Optional session identifier"
    )


class HandwritingExamResponse(BaseModel):
    """Response after handwriting exam processing."""
    
    success: bool
    trace_id: str
    exam_id: str
    total_questions: int
    ocr_processed: int
    marks_awarded: float
    max_marks: float
    grade: str | None = None
    requires_manual_review: bool = False
    low_confidence_questions: List[str] = []
