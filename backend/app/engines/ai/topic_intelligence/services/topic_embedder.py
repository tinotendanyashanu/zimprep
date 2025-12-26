"""Topic embedding service using sentence-transformers.

Generates consistent 384-dimensional embeddings for topics and questions.
"""

import logging
from typing import Any

from app.engines.ai.topic_intelligence.errors import EmbeddingServiceUnavailableError

logger = logging.getLogger(__name__)


class TopicEmbedder:
    """Service for embedding topics into vector space.
    
    Uses sentence-transformers (all-MiniLM-L6-v2):
    - Free (self-hosted, no API costs)
    - Fast (~5ms per embedding)
    - 384 dimensions
    - Good quality for semantic similarity
    """
    
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    
    def __init__(self):
        """Initialize embedder with sentence-transformers model."""
        self.model = None  # Lazy load
        self.model_loaded = False
    
    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model_loaded:
            return
        
        try:
            # Placeholder: In production, would load sentence-transformers
            # from sentence_transformers import SentenceTransformer
            # self.model = SentenceTransformer(self.EMBEDDING_MODEL)
            
            # For now, simulate model loading
            logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
            self.model = "simulated_model"  # Placeholder
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise EmbeddingServiceUnavailableError(
                service=self.EMBEDDING_MODEL,
                original_error=str(e)
            )
    
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text.
        
        Args:
            text: Text to embed (topic name or question text)
            
        Returns:
            384-dimensional embedding vector
            
        Raises:
            EmbeddingServiceUnavailableError: If embedding fails
        """
        self._load_model()
        
        try:
            # Placeholder: In production, would use sentence-transformers
            # embedding = self.model.encode(text, convert_to_numpy=True)
            # return embedding.tolist()
            
            # For now, return simulated embedding (deterministic for testing)
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            
            # Generate deterministic "embedding" from hash
            # In production, this would be replaced with actual sentence-transformers
            embedding = [(hash_val >> (i % 32)) % 256 / 255.0 - 0.5 
                        for i in range(self.EMBEDDING_DIMENSION)]
            
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise EmbeddingServiceUnavailableError(
                service=self.EMBEDDING_MODEL,
                original_error=str(e)
            )
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (batch processing).
        
        More efficient than calling embed_text multiple times.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of 384-dimensional embedding vectors
        """
        self._load_model()
        
        try:
            # Placeholder: In production, would use batch encoding
            # embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
            # return embeddings.tolist()
            
            # For now, call embed_text for each (inefficient, but works)
            embeddings = [self.embed_text(text) for text in texts]
            
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}")
            raise EmbeddingServiceUnavailableError(
                service=self.EMBEDDING_MODEL,
                original_error=str(e)
            )
    
    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        import math
        
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Compute magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Clamp to [0.0, 1.0] range (cosine can be negative, but we only care about positive similarity)
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0))
