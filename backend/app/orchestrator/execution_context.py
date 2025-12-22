from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class ExecutionContext:
    """Context for a single request execution.
    
    Contains all metadata required for full observability and traceability.
    This context is created by the gateway and propagated to all engines.
    """
    
    # Core identification
    trace_id: str
    request_id: str
    
    # Timing
    request_timestamp: datetime
    
    # Source tracking
    request_source: str  # e.g., "web", "mobile", "api"
    
    # User context
    user_id: str | None = None
    
    # Feature flags snapshot (immutable at request time)
    feature_flags_snapshot: dict[str, bool] = field(default_factory=dict)

    @staticmethod
    def create(
        user_id: str | None = None,
        request_source: str = "api",
        feature_flags: dict[str, bool] | None = None
    ) -> "ExecutionContext":
        """Create a new execution context with generated IDs.
        
        Args:
            user_id: Optional user identifier
            request_source: Source of the request (web, mobile, api, etc.)
            feature_flags: Optional feature flags snapshot
            
        Returns:
            ExecutionContext with all fields populated
        """
        return ExecutionContext(
            trace_id=str(uuid4()),
            request_id=str(uuid4()),
            request_timestamp=datetime.utcnow(),
            request_source=request_source,
            user_id=user_id,
            feature_flags_snapshot=feature_flags or {}
        )
