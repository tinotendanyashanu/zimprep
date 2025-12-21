"""Audit logger for authorization decisions.

Provides structured logging for compliance and debugging.
"""

import logging
from typing import Optional
from datetime import datetime

from app.engines.identity_subscription.schemas.denial_reasons import DenialReason
from app.engines.identity_subscription.schemas.input import ActionType

logger = logging.getLogger(__name__)


class AuditLogger:
    """Structured audit logging for authorization decisions."""
    
    @staticmethod
    def log_decision(
        trace_id: str,
        user_id: Optional[str],
        action_type: ActionType,
        allowed: bool,
        denial_reason: Optional[DenialReason] = None,
        confidence: float = 1.0,
        metadata: Optional[dict] = None
    ) -> None:
        """Log authorization decision.
        
        Args:
            trace_id: Request trace identifier
            user_id: User identifier (may be None for unauthenticated)
            action_type: Action being requested
            allowed: Whether request was allowed
            denial_reason: Denial reason if denied
            confidence: Confidence score
            metadata: Additional metadata
        """
        log_data = {
            "trace_id": trace_id,
            "user_id": user_id,
            "action": action_type.value,
            "allowed": allowed,
            "denial_reason": denial_reason.value if denial_reason else None,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        if allowed:
            logger.info(
                f"Authorization: ALLOWED {action_type.value}",
                extra=log_data
            )
        else:
            logger.warning(
                f"Authorization: DENIED {action_type.value} ({denial_reason.value if denial_reason else 'unknown'})",
                extra=log_data
            )
    
    @staticmethod
    def log_error(
        trace_id: str,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """Log engine error.
        
        Args:
            trace_id: Request trace identifier
            error_type: Type of error
            error_message: Error message
            user_id: User identifier (may be None)
            metadata: Additional metadata
        """
        log_data = {
            "trace_id": trace_id,
            "user_id": user_id,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        logger.error(
            f"Engine error: {error_type} - {error_message}",
            extra=log_data
        )
    
    @staticmethod
    def log_cache_operation(
        trace_id: str,
        operation: str,
        cache_hit: bool,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """Log cache operation.
        
        Args:
            trace_id: Request trace identifier
            operation: Operation type (get, set, invalidate)
            cache_hit: Whether cache hit occurred
            user_id: User identifier
            metadata: Additional metadata
        """
        log_data = {
            "trace_id": trace_id,
            "user_id": user_id,
            "operation": operation,
            "cache_hit": cache_hit,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        logger.debug(
            f"Cache operation: {operation} ({'HIT' if cache_hit else 'MISS'})",
            extra=log_data
        )
