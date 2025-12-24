"""Retry logic for orchestrator to handle transient failures.

PHASE 6: Operational robustness - retry transient failures with exponential backoff.
"""

import logging
import asyncio
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""
    pass


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, operation: str, attempts: int, last_error: Exception):
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Retry exhausted for '{operation}' after {attempts} attempts. "
            f"Last error: {str(last_error)}"
        )


async def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    operation_name: str = "operation",
    trace_id: str = None,
    *args,
    **kwargs
) -> T:
    """Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay on each retry (default: 2.0)
        operation_name: Name of operation for logging
        trace_id: Optional trace ID for logging
        *args: Arguments for func
        **kwargs: Keyword arguments for func
    
    Returns:
        Result from func
        
    Raises:
        RetryExhaustedError: If all attempts fail
    """
    last_error = None
    delay = initial_delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                f"Attempting {operation_name} (attempt {attempt}/{max_attempts})",
                extra={"trace_id": trace_id, "attempt": attempt}
            )
            
            result = await func(*args, **kwargs)
            
            if attempt > 1:
                logger.info(
                    f"Retry successful for {operation_name} on attempt {attempt}",
                    extra={"trace_id": trace_id, "attempt": attempt}
                )
            
            return result
            
        except Exception as e:
            last_error = e
            
            # Check if this is the last attempt
            if attempt == max_attempts:
                logger.error(
                    f"All retry attempts exhausted for {operation_name}",
                    extra={
                        "trace_id": trace_id,
                        "attempts": max_attempts,
                        "last_error": str(e)
                    },
                    exc_info=True
                )
                raise RetryExhaustedError(operation_name, max_attempts, e)
            
            # Log retry attempt
            logger.warning(
                f"Attempt {attempt} failed for {operation_name}, retrying in {delay}s",
                extra={
                    "trace_id": trace_id,
                    "attempt": attempt,
                    "delay_seconds": delay,
                    "error": str(e)
                }
            )
            
            # Wait before retry
            await asyncio.sleep(delay)
            
            # Increase delay for next attempt
            delay *= backoff_factor


def retryable(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    operation_name: str = None
):
    """Decorator to add retry logic to async functions.
    
    Usage:
        @retryable(max_attempts=3, operation_name="database_write")
        async def save_to_db(data):
            ...
    
    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Delay multiplier for each retry
        operation_name: Name for logging (defaults to function name)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation_name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Try to extract trace_id from kwargs or args
            trace_id = kwargs.get('trace_id')
            if not trace_id and args:
                # Check if first arg has trace_id attribute
                if hasattr(args[0], 'trace_id'):
                    trace_id = args[0].trace_id
            
            return await retry_with_backoff(
                func,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                operation_name=op_name,
                trace_id=trace_id,
                *args,
                **kwargs
            )
        
        return wrapper
    return decorator
