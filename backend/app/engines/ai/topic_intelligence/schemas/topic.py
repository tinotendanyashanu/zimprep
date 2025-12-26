"""Topic data schemas."""

from typing import Literal
from pydantic import BaseModel, Field


class Topic(BaseModel):
    """Topic representation with embedding."""
    
    topic_id: str = Field(
        ...,
        description="Unique topic identifier"
    )
    
    topic_name: str = Field(
        ...,
        description="Human-readable topic name"
    )
    
    subject: str = Field(
        ...,
        description="Subject this topic belongs to (e.g., 'Mathematics')"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier"
    )
    
    embedding: list[float] | None = Field(
        default=None,
        description="384-dimensional vector embedding (None if not yet embedded)"
    )
    
    cluster_id: int | None = Field(
        default=None,
        description="Cluster assignment (None if not yet clustered)"
    )
    
    parent_topic_id: str | None = Field(
        default=None,
        description="Parent topic ID for hierarchical topics"
    )


class TopicCluster(BaseModel):
    """Cluster of related topics."""
    
    cluster_id: int = Field(
        ...,
        description="Unique cluster identifier"
    )
    
    cluster_name: str = Field(
        ...,
        description="Human-readable cluster name (auto-generated from centroid)"
    )
    
    topic_ids: list[str] = Field(
        ...,
        description="List of topic IDs in this cluster"
    )
    
    centroid_embedding: list[float] = Field(
        ...,
        description="384-dimensional centroid vector"
    )
    
    cluster_size: int = Field(
        ...,
        ge=1,
        description="Number of topics in cluster"
    )


class TopicSimilarity(BaseModel):
    """Topic similarity result."""
    
    topic_id: str = Field(
        ...,
        description="Topic identifier"
    )
    
    topic_name: str = Field(
        ...,
        description="Topic name"
    )
    
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0.0-1.0)"
    )
    
    relationship_type: Literal["same_cluster", "cross_cluster", "unrelated"] = Field(
        ...,
        description="Type of relationship between topics"
    )
