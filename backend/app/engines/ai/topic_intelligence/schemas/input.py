"""Input schema for Topic Intelligence Engine."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TopicIntelligenceInput(BaseModel):
    """Input contract for Topic Intelligence Engine.
    
    Supports 4 operations:
    1. embed_topic: Generate embedding for a topic
    2. cluster_topics: Cluster all topics in a subject
    3. find_similar: Find topics similar to a query topic
    4. match_question: Find topics matching a question
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    operation: Literal["embed_topic", "cluster_topics", "find_similar", "match_question"] = Field(
        ...,
        description="Operation to perform"
    )
    
    # For embed_topic
    topic_text: str | None = Field(
        default=None,
        description="Topic text to embed (required for embed_topic)"
    )
    
    topic_id: str | None = Field(
        default=None,
        description="Topic identifier (required for embed_topic, find_similar)"
    )
    
    syllabus_version: str | None = Field(
        default=None,
        description="Syllabus version (required for embed_topic)"
    )
    
    # For cluster_topics
    subject: str | None = Field(
        default=None,
        description="Subject to cluster (required for cluster_topics)"
    )
    
    # For find_similar
    query_topic_id: str | None = Field(
        default=None,
        description="Topic ID to find similar topics for (required for find_similar)"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to return (default: 0.7)"
    )
    
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of similar topics to return"
    )
    
    # For match_question
    question_text: str | None = Field(
        default=None,
        description="Question text to match (required for match_question)"
    )
    
    question_id: str | None = Field(
        default=None,
        description="Question identifier for logging"
    )
    
    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation is one of the allowed types."""
        allowed = {"embed_topic", "cluster_topics", "find_similar", "match_question"}
        if v not in allowed:
            raise ValueError(f"operation must be one of {allowed}, got: {v}")
        return v
