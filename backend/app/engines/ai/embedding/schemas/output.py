"""Output schema for Embedding Engine."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.engines.ai.embedding.schemas.input import AnswerType


class EmbeddingOutput(BaseModel):
    """Output contract for Embedding Engine.
    
    Contains the vector embedding and all legally auditable metadata.
    """
    
    # Core Embedding Data
    embedding_vector: List[float] = Field(
        ...,
        description="Vector embedding of the student answer (384-dimensional)"
    )
    
    vector_dimension: int = Field(
        ...,
        description="Dimensionality of the embedding vector"
    )
    
    embedding_model_id: str = Field(
        ...,
        description="Identifier of the embedding model used"
    )
    
    # Trace Information
    trace_id: str = Field(
        ...,
        description="Trace identifier from input (for audit trail)"
    )
    
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (always 1.0 for mechanical transformation)"
    )
    
    # Legally Auditable Metadata (Mandatory)
    engine_name: str = Field(
        default="embedding",
        description="Engine name for audit trail"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for reproducibility"
    )
    
    subject: str = Field(
        ...,
        description="Subject name"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier"
    )
    
    paper_id: str = Field(
        ...,
        description="Paper identifier"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier"
    )
    
    max_marks: int = Field(
        ...,
        description="Maximum marks for this question"
    )
    
    answer_type: AnswerType = Field(
        ...,
        description="Type of answer"
    )
    
    submission_timestamp: datetime = Field(
        ...,
        description="Original submission timestamp"
    )
