"""Output schema for Topic Intelligence Engine."""

from typing import Any
from pydantic import BaseModel, Field

from app.engines.ai.topic_intelligence.schemas.topic import (
    TopicCluster,
    TopicSimilarity,
)


class TopicIntelligenceOutput(BaseModel):
    """Output contract for Topic Intelligence Engine.
    
    Fields populated depend on the operation:
    - embed_topic: topic_embedding
    - cluster_topics: topic_clusters
    - find_similar: similar_topics
    - match_question: matched_topics
    """
    
    trace_id: str = Field(
        ...,
        description="Trace identifier from input"
    )
    
    operation: str = Field(
        ...,
        description="Operation that was performed"
    )
    
    # For embed_topic
    topic_embedding: list[float] | None = Field(
        default=None,
        description="384-dimensional topic embedding (embed_topic only)"
    )
    
    topic_id: str | None = Field(
        default=None,
        description="Topic ID that was embedded (embed_topic only)"
    )
    
    # For cluster_topics
    topic_clusters: list[TopicCluster] | None = Field(
        default=None,
        description="Discovered topic clusters (cluster_topics only)"
    )
    
    num_clusters: int | None = Field(
        default=None,
        description="Number of clusters discovered (cluster_topics only)"
    )
    
    # For find_similar
    similar_topics: list[TopicSimilarity] | None = Field(
        default=None,
        description="Similar topics ranked by similarity (find_similar only)"
    )
    
    query_topic_id: str | None = Field(
        default=None,
        description="Query topic ID (find_similar only)"
    )
    
    # For match_question
    matched_topics: list[TopicSimilarity] | None = Field(
        default=None,
        description="Topics matching the question (match_question only)"
    )
    
    question_id: str | None = Field(
        default=None,
        description="Question ID that was matched (match_question only)"
    )
    
    # Common fields
    engine_version: str = Field(
        ...,
        description="Engine version for audit trail"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional operation metadata"
    )
