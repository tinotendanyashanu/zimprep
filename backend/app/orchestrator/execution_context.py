from dataclasses import dataclass
from uuid import uuid4


@dataclass
class ExecutionContext:
    """Context for a single request execution."""
    
    trace_id: str
    user_id: str | None = None

    @staticmethod
    def create(user_id: str | None = None):
        """Create a new execution context with generated trace_id."""
        return ExecutionContext(trace_id=str(uuid4()), user_id=user_id)
