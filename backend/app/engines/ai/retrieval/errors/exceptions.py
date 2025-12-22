"""Custom exceptions for Retrieval Engine."""


class RetrievalEngineError(Exception):
    """Base exception for all Retrieval Engine errors.
    
    All retrieval engine errors inherit from this base class for
    consistent error handling and categorization.
    """
    
    def __init__(self, message: str, trace_id: str = None):
        """Initialize retrieval engine error.
        
        Args:
            message: Error message
            trace_id: Optional trace ID for audit trail
        """
        self.message = message
        self.trace_id = trace_id
        super().__init__(self.message)


class VectorStoreUnavailableError(RetrievalEngineError):
    """Vector store is unavailable or unreachable.
    
    This is a HARD FAILURE - the pipeline must fail if we cannot
    access the vector store. AI marking cannot proceed without
    authoritative evidence.
    """
    
    def __init__(self, message: str = "Vector store unavailable", trace_id: str = None):
        super().__init__(message=message, trace_id=trace_id)


class InsufficientEvidenceError(RetrievalEngineError):
    """Insufficient evidence retrieved for marking.
    
    This is a SOFT FAILURE - we degrade confidence but can still
    return partial results. The Reasoning Engine may choose to
    veto based on low confidence.
    """
    
    def __init__(self, message: str = "Insufficient evidence retrieved", trace_id: str = None):
        super().__init__(message=message, trace_id=trace_id)


class InvalidEmbeddingDimensionError(RetrievalEngineError):
    """Embedding vector has invalid dimensionality.
    
    This is a HARD FAILURE - embeddings must be exactly 384 dimensions
    to match the vector store index. This indicates an upstream engine
    failure or data corruption.
    """
    
    def __init__(self, expected: int, actual: int, trace_id: str = None):
        message = f"Invalid embedding dimension: expected {expected}, got {actual}"
        super().__init__(message=message, trace_id=trace_id)
        self.expected = expected
        self.actual = actual


class QueryExecutionError(RetrievalEngineError):
    """Error executing vector search query.
    
    This is a HARD FAILURE - indicates a problem with the query syntax,
    index configuration, or database state. Cannot proceed without fixing.
    """
    
    def __init__(self, message: str, query: dict = None, trace_id: str = None):
        super().__init__(message=message, trace_id=trace_id)
        self.query = query
