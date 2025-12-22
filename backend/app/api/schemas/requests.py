"""API request schemas for ZimPrep gateway.

All gateway endpoints MUST use these Pydantic schemas for type safety
and automatic validation.
"""

from pydantic import BaseModel, Field


class PipelineExecutionRequest(BaseModel):
    """Request to execute a pipeline.
    
    This is the ONLY way to execute engines in production.
    Direct engine execution is not allowed.
    """
    
    pipeline_name: str = Field(
        ...,
        description="Name of the pipeline to execute",
        examples=["exam_attempt_v1"]
    )
    
    input_data: dict = Field(
        default_factory=dict,
        description="Input data for the pipeline (specific to each pipeline type)"
    )
    
    class Config:
        # Reject unknown fields
        extra = "forbid"
