"""Custom exceptions for Identity & Subscription Engine.

All exceptions include explicit denial reasons for fail-closed behavior.
"""

from typing import Optional, Dict, Any
from app.engines.identity_subscription.schemas.denial_reasons import DenialReason


class EngineException(Exception):
    """Base exception for all engine errors.
    
    All engine exceptions include:
    - Explicit denial reason
    - Trace ID for debugging
    - Additional metadata
    """
    
    def __init__(
        self,
        message: str,
        denial_reason: DenialReason,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.denial_reason = denial_reason
        self.trace_id = trace_id
        self.metadata = metadata or {}


class IdentityResolutionError(EngineException):
    """Identity lookup failed or returned ambiguous results."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            denial_reason=DenialReason.USER_NOT_FOUND,
            trace_id=trace_id,
            metadata=metadata,
        )


class SubscriptionResolutionError(EngineException):
    """Subscription lookup failed or returned ambiguous results."""
    
    def __init__(
        self,
        message: str,
        denial_reason: DenialReason = DenialReason.NO_ACTIVE_SUBSCRIPTION,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            denial_reason=denial_reason,
            trace_id=trace_id,
            metadata=metadata,
        )


class DatabaseError(EngineException):
    """Database connection or query failed."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            denial_reason=DenialReason.DATABASE_ERROR,
            trace_id=trace_id,
            metadata=metadata,
        )


class CacheInconsistencyError(EngineException):
    """Cache validation failed, data inconsistency detected."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            denial_reason=DenialReason.CACHE_INCONSISTENCY,
            trace_id=trace_id,
            metadata=metadata,
        )


class AmbiguousStateError(EngineException):
    """Multiple conflicting states detected (fail-closed)."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            denial_reason=DenialReason.AMBIGUOUS_STATE,
            trace_id=trace_id,
            metadata=metadata,
        )
