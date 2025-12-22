"""Embedding Engine

Transforms validated student responses into high-quality vector embeddings
for downstream retrieval-based marking.
"""

from app.engines.ai.embedding.engine import EmbeddingEngine
from app.engines.ai.embedding.schemas import EmbeddingInput, EmbeddingOutput

__all__ = ["EmbeddingEngine", "EmbeddingInput", "EmbeddingOutput"]
