"""Timeout wrapper for AI API calls.

PHASE 6: Operational robustness - prevent pipeline hangs from slow AI responses.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

from app.config.settings import settings


logger = logging.getLogger(__name__)

T = TypeVar('T')


class AITimeoutError(Exception):
    """Raised when AI API call exceeds timeout."""
    
    def __init__(self, engine_name: str, timeout_seconds: int):
        self.engine_name = engine_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"AI engine '{engine_name}' timed out after {timeout_seconds} seconds"
        )


def with_timeout(engine_name: str):
    """Decorator to add timeout to AI API calls.
    
    Usage:
        @with_timeout("reasoning_marking")
        async def call_openai_api(...):
            ...
    
    Args:
        engine_name: Name of the engine making the call (for logging)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            timeout = settings.AI_TIMEOUT_SECONDS
            
            try:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError:
                logger.error(
                    f"AI timeout in {engine_name}: exceeded {timeout}s",
                    extra={
                        "engine_name": engine_name,
                        "timeout_seconds": timeout
                    }
                )
                raise AITimeoutError(engine_name, timeout)
        
        return wrapper
    return decorator


async def with_timeout_sync(
    func: Callable[..., T],
    engine_name: str,
    *args,
    **kwargs
) -> T:
    """Apply timeout to synchronous function in async context.
    
    For synchronous AI API calls that need timeout protection.
    
    Args:
        func: Synchronous function to call
        engine_name: Name of the engine (for logging)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
    
    Returns:
        Function result
        
    Raises:
        AITimeoutError: If function exceeds timeout
    """
    timeout = settings.AI_TIMEOUT_SECONDS
    
    try:
        # Run synchronous function in executor with timeout
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, lambda: func(*args, **kwargs)
            ),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error(
            f"AI timeout in {engine_name}: exceeded {timeout}s",
            extra={
                "engine_name": engine_name,
                "timeout_seconds": timeout
            }
        )
        raise AITimeoutError(engine_name, timeout)
