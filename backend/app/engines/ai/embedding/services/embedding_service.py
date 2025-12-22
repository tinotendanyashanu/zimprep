"""Embedding generation service using sentence-transformers.

Provides deterministic, reproducible vector embeddings for student answers.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding generation service.
    
    Uses sentence-transformers (all-MiniLM-L6-v2) for generating
    384-dimensional vector embeddings.
    
    The model is cached in memory for performance across multiple requests.
    """
    
    # Class-level model cache
    _model = None
    _model_id = "sentence-transformers/all-MiniLM-L6-v2"
    _vector_dimension = 384
    
    @classmethod
    def get_model_id(cls) -> str:
        """Get the embedding model identifier.
        
        Returns:
            Model identifier string
        """
        return cls._model_id
    
    @classmethod
    def get_vector_dimension(cls) -> int:
        """Get the embedding vector dimension.
        
        Returns:
            Vector dimension (384)
        """
        return cls._vector_dimension
    
    @classmethod
    def _load_model(cls):
        """Load the embedding model into memory.
        
        Model is cached at the class level to avoid repeated loading.
        
        Raises:
            ImportError: If sentence-transformers is not installed
            Exception: If model loading fails
        """
        if cls._model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {cls._model_id}")
            cls._model = SentenceTransformer(cls._model_id)
            logger.info("Embedding model loaded successfully")
            
        except ImportError as e:
            logger.error("sentence-transformers not installed")
            raise ImportError(
                "sentence-transformers package is required for embedding generation. "
                "Install with: pip install sentence-transformers"
            ) from e
        
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    @classmethod
    def generate_embedding(
        cls,
        normalized_text: str,
        trace_id: Optional[str] = None
    ) -> List[float]:
        """Generate embedding vector for normalized text.
        
        Args:
            normalized_text: Preprocessed student answer text
            trace_id: Optional trace ID for logging
            
        Returns:
            Embedding vector as list of floats (384-dimensional)
            
        Raises:
            Exception: If embedding generation fails
        """
        # Ensure model is loaded
        cls._load_model()
        
        try:
            # Generate embedding
            # encode() returns numpy array
            embedding_array = cls._model.encode(
                normalized_text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Convert numpy array to Python list
            embedding_vector = embedding_array.tolist()
            
            # Validate dimensionality
            if len(embedding_vector) != cls._vector_dimension:
                raise ValueError(
                    f"Unexpected embedding dimension: {len(embedding_vector)} "
                    f"(expected {cls._vector_dimension})"
                )
            
            logger.info(
                "Embedding generated successfully",
                extra={
                    "trace_id": trace_id,
                    "vector_dimension": len(embedding_vector),
                    "model_id": cls._model_id
                }
            )
            
            return embedding_vector
        
        except Exception as e:
            logger.error(
                f"Embedding generation failed: {str(e)}",
                extra={"trace_id": trace_id},
                exc_info=True
            )
            raise
