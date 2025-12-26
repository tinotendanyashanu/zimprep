"""Custom exceptions for Topic Intelligence Engine."""


class TopicIntelligenceError(Exception):
    """Base exception for Topic Intelligence Engine errors."""
    pass


class EmbeddingServiceUnavailableError(TopicIntelligenceError):
    """Raised when embedding service is unavailable."""
    
    def __init__(self, service: str, original_error: str | None = None):
        self.service = service
        self.original_error = original_error
        message = f"Embedding service unavailable: {service}"
        if original_error:
            message += f" (error: {original_error})"
        super().__init__(message)


class ClusteringFailedError(TopicIntelligenceError):
    """Raised when clustering fails."""
    
    def __init__(self, reason: str, num_topics: int | None = None):
        self.reason = reason
        self.num_topics = num_topics
        message = f"Clustering failed: {reason}"
        if num_topics:
            message += f" (topics: {num_topics})"
        super().__init__(message)


class TopicNotFoundError(TopicIntelligenceError):
    """Raised when topic is not found."""
    
    def __init__(self, topic_id: str):
        self.topic_id = topic_id
        super().__init__(f"Topic not found: {topic_id}")


class InvalidOperationError(TopicIntelligenceError):
    """Raised when operation is invalid or missing required fields."""
    
    def __init__(self, operation: str, missing_fields: list[str]):
        self.operation = operation
        self.missing_fields = missing_fields
        super().__init__(
            f"Invalid operation '{operation}': missing required fields {missing_fields}"
        )
