"""AI timeout enforcement utilities.

Ensures all AI engine calls respect the configured timeout to prevent
pipeline hangs from slow AI API responses.
"""

import asyncio
import functools
from typing import TypeVar, Callable, Any, Coroutine
from app.config.settings import settings
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


def with_timeout(
    timeout_seconds: int | None = None,
    operation_name: str = "AI operation"
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator to enforce timeout on async AI operations.
    
    Usage:
        @with_timeout(timeout_seconds=30, operation_name="OpenAI completion")
        async def call_openai_api(...):
            ...
    
    Args:
        timeout_seconds: Timeout in seconds (default: from settings.AI_TIMEOUT_SECONDS)
        operation_name: Human-readable operation name for logging
        
    Returns:
        Decorated async function with timeout enforcement
    """
    if timeout_seconds is None:
        timeout_seconds = settings.AI_TIMEOUT_SECONDS
    
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"{operation_name} timed out",
                    timeout_seconds=timeout_seconds,
                    function=func.__name__
                )
                raise TimeoutError(
                    f"{operation_name} exceeded timeout of {timeout_seconds}s"
                )
        
        return wrapper
    
    return decorator


class AITimeoutError(Exception):
    """Raised when an AI operation times out."""
    pass


async def with_timeout_async(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: int | None = None,
    operation_name: str = "AI operation"
) -> T:
    """Execute coroutine with timeout (functional approach).
    
    Usage:
        result = await with_timeout_async(
            openai_api_call(),
            timeout_seconds=30,
            operation_name="OpenAI embedding"
        )
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        operation_name: Human-readable operation name for logging
        
    Returns:
        Result from coroutine
        
    Raises:
        AITimeoutError: If operation times out
    """
    if timeout_seconds is None:
        timeout_seconds = settings.AI_TIMEOUT_SECONDS
    
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(
            f"{operation_name} timed out",
            timeout_seconds=timeout_seconds
        )
        raise AITimeoutError(
            f"{operation_name} exceeded timeout of {timeout_seconds}s"
        )
