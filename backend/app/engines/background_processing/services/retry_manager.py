"""Retry manager for transient failure recovery.

Implements exponential backoff with jitter and retry policies.
"""

import logging
import asyncio
import random
from typing import Callable, Any, TypeVar, Optional

from app.engines.background_processing.schemas.input import RetryPolicy
from app.engines.background_processing.errors import (
    BackgroundProcessingError,
    RetryLimitExceededError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryManager:
    """Manages retry logic for transient failures.
    
    Features:
    - Exponential backoff with jitter
    - Configurable max retry attempts
    - Transient vs permanent error classification
    - Retry telemetry logging
    """
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Any],
        retry_policy: RetryPolicy,
        trace_id: str,
        job_id: str,
        operation_name: str = "operation"
    ) -> tuple[Any, int]:
        """Execute operation with retry logic.
        
        Args:
            operation: Async callable to execute
            retry_policy: Retry configuration
            trace_id: Trace ID for logging
            job_id: Job ID for logging
            operation_name: Name of operation for logging
            
        Returns:
            Tuple of (result, retry_count)
            
        Raises:
            RetryLimitExceededError: If max retries exceeded
            BackgroundProcessingError: If non-retryable error occurs
        """
        attempt = 0
        last_error: Optional[Exception] = None
        
        while attempt < retry_policy.max_attempts:
            try:
                logger.info(
                    f"Executing {operation_name} (attempt {attempt + 1}/{retry_policy.max_attempts})",
                    extra={"trace_id": trace_id, "job_id": job_id}
                )
                
                result = await operation()
                
                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded after {attempt} retries",
                        extra={"trace_id": trace_id, "job_id": job_id}
                    )
                
                return result, attempt
                
            except BackgroundProcessingError as e:
                last_error = e
                
                # If error is not retryable, fail immediately
                if not e.is_retryable:
                    logger.error(
                        f"{operation_name} failed with non-retryable error: {e.error_code.value}",
                        extra={"trace_id": trace_id, "job_id": job_id}
                    )
                    raise
                
                # Check if we can retry
                attempt += 1
                if attempt >= retry_policy.max_attempts:
                    logger.error(
                        f"{operation_name} failed after {attempt} attempts",
                        extra={
                            "trace_id": trace_id,
                            "job_id": job_id,
                            "last_error": str(e)
                        }
                    )
                    raise RetryLimitExceededError(
                        max_attempts=retry_policy.max_attempts,
                        trace_id=trace_id
                    ) from e
                
                # Calculate backoff delay
                delay_ms = self._calculate_backoff(
                    attempt=attempt,
                    retry_policy=retry_policy
                )
                
                logger.warning(
                    f"{operation_name} failed (attempt {attempt}), retrying in {delay_ms}ms: {e.error_code.value}",
                    extra={
                        "trace_id": trace_id,
                        "job_id": job_id,
                        "error": str(e)
                    }
                )
                
                # Wait before retry
                await asyncio.sleep(delay_ms / 1000.0)
                
            except Exception as e:
                # Unexpected error - treat as non-retryable
                logger.exception(
                    f"{operation_name} failed with unexpected error",
                    extra={"trace_id": trace_id, "job_id": job_id}
                )
                raise
        
        # Should not reach here, but if we do, raise retry limit exceeded
        raise RetryLimitExceededError(
            max_attempts=retry_policy.max_attempts,
            trace_id=trace_id
        ) from last_error
    
    def _calculate_backoff(
        self,
        attempt: int,
        retry_policy: RetryPolicy
    ) -> int:
        """Calculate backoff delay in milliseconds.
        
        Args:
            attempt: Current attempt number (1-indexed)
            retry_policy: Retry configuration
            
        Returns:
            Delay in milliseconds
        """
        if retry_policy.backoff_strategy == "exponential":
            # Exponential backoff: initial_delay * multiplier^(attempt-1)
            delay = retry_policy.initial_delay_ms * (
                retry_policy.backoff_multiplier ** (attempt - 1)
            )
        else:
            # Linear backoff: initial_delay * attempt
            delay = retry_policy.initial_delay_ms * attempt
        
        # Add jitter (±25% randomness)
        jitter = random.uniform(-0.25, 0.25)
        delay = delay * (1 + jitter)
        
        # Cap at 60 seconds
        delay = min(delay, 60000)
        
        return int(delay)
