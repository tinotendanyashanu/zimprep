"""Output schema for Retrieval Engine."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceChunk(BaseModel):
    """Single piece of evidence retrieved from vector store.
    
    All content is preserved verbatim - no summarization or paraphrasing.
    This ensures legal defensibility and auditability.
    """
    
    source_type: str = Field(
        ...,
        description="Type of evidence source (marking_scheme, examiner_report, etc.)"
    )
    
    content: str = Field(
        ...,
        description="Original text content from source document (unmodified)"
    )
    
    source_reference: str = Field(
        ...,
        description="Document ID or reference for audit trail"
    )
    
    syllabus_ref: Optional[str] = Field(
        default=None,
        description="Syllabus reference if applicable (e.g., '3.2.1 Algebra')"
    )
    
    mark_mapping: Optional[int] = Field(
        default=None,
        ge=0,
        description="Mark allocation if this evidence specifies marks"
    )
    
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Vector similarity score (cosine similarity)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from source document"
    )


class RetrievalOutput(BaseModel):
    """Output contract for Retrieval Engine.
    
    Contains the assembled evidence pack ready for the Reasoning Engine.
    Confidence represents evidence sufficiency, NOT answer correctness.
    """
    
    trace_id: str = Field(
        ...,
        description="Trace identifier from input (for audit trail)"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier"
    )
    
    evidence_pack: Dict[str, List[EvidenceChunk]] = Field(
        ...,
        description="Evidence chunks grouped by source type"
    )
    
    retrieval_metadata: Dict[str, Any] = Field(
        ...,
        description="Retrieval statistics and metadata"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Evidence sufficiency score (NOT answer correctness)"
    )
    
    engine_version: str = Field(
        ...,
        description="Engine version for audit trail and reproducibility"
    )
    
    # Core metadata (for audit trail)
    subject: str = Field(
        ...,
        description="Subject name"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier"
    )
    
    paper_code: str = Field(
        ...,
        description="Paper code"
    )
