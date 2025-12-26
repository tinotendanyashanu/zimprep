"""Error handling for Topic Intelligence Engine."""

from app.engines.ai.topic_intelligence.errors.exceptions import (
    TopicIntelligenceError,
    EmbeddingServiceUnavailableError,
    ClusteringFailedError,
    TopicNotFoundError,
    InvalidOperationError,
)

__all__ = [
    "TopicIntelligenceError",
    "EmbeddingServiceUnavailableError",
    "ClusteringFailedError",
    "TopicNotFoundError",
    "InvalidOperationError",
]
