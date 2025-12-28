"""Custom exceptions for Device Connectivity Awareness Engine."""

from typing import Optional, Dict, Any


class ConnectivityException(Exception):
    """Base exception for connectivity operations."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}
        super().__init__(self.message)


class SessionPausedError(ConnectivityException):
    """Raised when session is paused due to long disconnect."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        disconnect_duration: Optional[int] = None
    ):
        metadata = {
            "session_id": session_id,
            "disconnect_duration_seconds": disconnect_duration
        }
        super().__init__(message, trace_id, metadata)


class InvalidHeartbeatError(ConnectivityException):
    """Raised when heartbeat validation fails."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        metadata = {"session_id": session_id}
        super().__init__(message, trace_id, metadata)
