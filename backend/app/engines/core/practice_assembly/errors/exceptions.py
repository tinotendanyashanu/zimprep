"""Custom exceptions for Practice Assembly Engine."""


class PracticeAssemblyError(Exception):
    """Base exception for Practice Assembly Engine errors."""
    pass


class InsufficientQuestionsError(PracticeAssemblyError):
    """Raised when not enough questions match criteria."""
    
    def __init__(self, requested: int, available: int, topics: list[str]):
        self.requested = requested
        self.available = available
        self.topics = topics
        super().__init__(
            f"Insufficient questions: requested {requested}, found {available} "
            f"for topics {topics}"
        )


class InvalidDifficultyDistributionError(PracticeAssemblyError):
    """Raised when difficulty distribution is invalid."""
    
    def __init__(self, distribution: dict[str, float], reason: str):
        self.distribution = distribution
        self.reason = reason
        super().__init__(
            f"Invalid difficulty distribution {distribution}: {reason}"
        )


class TopicExpansionFailedError(PracticeAssemblyError):
    """Raised when topic expansion via Topic Intelligence fails."""
    
    def __init__(self, topic_id: str, original_error: str | None = None):
        self.topic_id = topic_id
        self.original_error = original_error
        message = f"Topic expansion failed for {topic_id}"
        if original_error:
            message += f": {original_error}"
        super().__init__(message)
