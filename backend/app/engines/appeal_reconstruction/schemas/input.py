"""Appeal Reconstruction Input Schema.

STRICT CONTRACT: This schema defines the ONLY valid inputs for appeal reconstruction.
"""

from typing import Literal
from pydantic import BaseModel, field_validator


class AppealReconstructionInput(BaseModel):
    """Input contract for Appeal Reconstruction Engine.
    
    CRITICAL RULES:
    - trace_id is MANDATORY (references original exam execution)
    - scope specifies what to reconstruct
    - question_id only allowed when scope == "question"
    - Unknown fields are REJECTED (fail-closed)
    """
    
    trace_id: str
    scope: Literal["full", "question"] = "full"
    question_id: str | None = None
    
    class Config:
        """Pydantic config for strict validation."""
        extra = "forbid"  # Reject unknown fields
    
    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, v: str) -> str:
        """Ensure trace_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("trace_id cannot be empty")
        return v.strip()
    
    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: str | None, info) -> str | None:
        """Ensure question_id is only provided when scope == 'question'."""
        scope = info.data.get("scope", "full")
        
        if scope == "question" and not v:
            raise ValueError("question_id is required when scope is 'question'")
        
        if scope == "full" and v:
            raise ValueError("question_id should not be provided when scope is 'full'")
        
        return v
