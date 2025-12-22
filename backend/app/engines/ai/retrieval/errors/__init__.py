"""Error handling for Retrieval Engine."""

from app.engines.ai.retrieval.errors.exceptions import (
    RetrievalEngineError,
    VectorStoreUnavailableError,
    InsufficientEvidenceError,
    InvalidEmbeddingDimensionError,
    QueryExecutionError,
)

__all__ = [
    "RetrievalEngineError",
    "VectorStoreUnavailableError",
    "InsufficientEvidenceError",
    "InvalidEmbeddingDimensionError",
    "QueryExecutionError",
]
