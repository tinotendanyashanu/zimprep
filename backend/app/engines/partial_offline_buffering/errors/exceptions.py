"""Custom exceptions for Partial Offline Buffering Engine."""

from typing import Optional, Dict, Any


class BufferingException(Exception):
    """Base exception for buffering operations."""
    
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


class BufferLimitExceededError(BufferingException):
    """Raised when buffer size limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        current_buffer_count: Optional[int] = None
    ):
        metadata = {
            "session_id": session_id,
            "current_buffer_count": current_buffer_count
        }
        super().__init__(message, trace_id, metadata)


class BufferExpiredError(BufferingException):
    """Raised when attempting to sync expired buffers."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        buffer_id: Optional[str] = None
    ):
        metadata = {"buffer_id": buffer_id}
        super().__init__(message, trace_id, metadata)


class DuplicateBufferError(BufferingException):
    """Raised when duplicate buffer is detected."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        buffered_payload_hash: Optional[str] = None
    ):
        metadata = {"buffered_payload_hash": buffered_payload_hash}
        super().__init__(message, trace_id, metadata)


class SyncFailedError(BufferingException):
    """Raised when sync operation fails."""
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        failed_count: Optional[int] = None
    ):
        metadata = {"failed_count": failed_count}
        super().__init__(message, trace_id, metadata)
