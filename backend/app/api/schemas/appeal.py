"""Appeal Reconstruction Request Schema."""

from typing import Literal
from pydantic import BaseModel, Field


class AppealReconstructRequest(BaseModel):
    """Request schema for appeal reconstruction endpoint.
    
    FORENSIC REQUEST: This endpoint reconstructs exam decisions
    without re-executing AI engines.
    """
    
    trace_id: str = Field(
        ...,
        description="Original exam attempt trace ID to reconstruct"
    )
    scope: Literal["full", "question"] = Field(
        default="full",
        description="Reconstruction scope: 'full' for entire paper, 'question' for single question"
    )
    question_id: str | None = Field(
        default=None,
        description="Question ID (required when scope is 'question')"
    )
    
    class Config:
        extra = "forbid"
