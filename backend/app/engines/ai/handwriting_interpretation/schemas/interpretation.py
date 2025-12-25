"""Interpretation schemas for structured answer representation."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class MathExpression(BaseModel):
    """Mathematical expression extracted from handwriting.
    
    Represents a single mathematical expression (equation, formula, calculation).
    """
    
    latex: str = Field(
        ...,
        description="LaTeX representation of the mathematical expression"
    )
    
    plain_text: str = Field(
        ...,
        description="Plain text representation (fallback if LaTeX rendering fails)"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="OCR confidence for this specific expression"
    )
    
    position_index: int = Field(
        ...,
        ge=0,
        description="Position index in the answer (0-based, sequential order)"
    )


class ExtractedStep(BaseModel):
    """Single step extracted from a step-by-step answer.
    
    Used for structured answers like math problems where working is shown.
    """
    
    step_number: int = Field(
        ...,
        ge=1,
        description="Step number (1-based, as shown in student answer)"
    )
    
    content: str = Field(
        ...,
        description="Text content of the step"
    )
    
    math_expressions: list[MathExpression] = Field(
        default_factory=list,
        description="Mathematical expressions found in this step"
    )
    
    is_final_answer: bool = Field(
        default=False,
        description="True if this step contains the final answer"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., detected labels, underlines)"
    )


class StructuredAnswer(BaseModel):
    """Canonical structured representation of a handwritten answer.
    
    This is the PRIMARY output of the Handwriting Interpretation Engine.
    It provides a clean, structured representation suitable for embedding
    and AI marking.
    """
    
    answer_type: Literal["calculation", "essay", "short_answer", "structured"] = Field(
        ...,
        description="Type of answer (influences structure)"
    )
    
    full_text: str = Field(
        ...,
        description="Complete answer as continuous text (primary representation)"
    )
    
    steps: list[ExtractedStep] = Field(
        default_factory=list,
        description="Step-by-step breakdown (empty for essay/short_answer)"
    )
    
    math_expressions: list[MathExpression] = Field(
        default_factory=list,
        description="All mathematical expressions found (for calculation/structured)"
    )
    
    detected_language: str = Field(
        default="en",
        description="Detected language code (ISO 639-1)"
    )
    
    word_count: int = Field(
        ...,
        ge=0,
        description="Total word count"
    )
    
    has_diagrams: bool = Field(
        default=False,
        description="True if diagrams/drawings were detected (not OCR'd)"
    )
    
    interpretation_notes: list[str] = Field(
        default_factory=list,
        description="Notes about interpretation quality/issues (e.g., 'illegible word at line 3')"
    )
