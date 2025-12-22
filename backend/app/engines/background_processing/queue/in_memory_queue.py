"""In-memory job queue implementation.

Reference implementation using asyncio.Queue with priority support.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.engines.background_processing.queue.job_queue import JobQueue
from app.engines.background_processing.schemas.input import JobInput, JobPriority

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrioritizedJob:
    """Job wrapper for priority queue ordering.
    
    Orders by:
    1. Priority (CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3)
    2. Request timestamp (earlier first)
    """
    
    priority_value: int
    requested_at: datetime = field(compare=True)
    job_input: JobInput = field(compare=False)
    
    @staticmethod
    def from_job_input(job_input: JobInput) -> "PrioritizedJob":
        """Create prioritized job from input.
        
        Args:
            job_input: Job input to wrap
            
        Returns:
            PrioritizedJob with priority ordering
        """
        # Map priority to numeric value (lower = higher priority)
        priority_map = {
            JobPriority.CRITICAL: 0,
            JobPriority.HIGH: 1,
            JobPriority.MEDIUM: 2,
            JobPriority.LOW: 3,
        }
        
        return PrioritizedJob(
            priority_value=priority_map[job_input.priority],
            requested_at=job_input.requested_at,
            job_input=job_input
        )


class InMemoryQueue(JobQueue):
    """In-memory priority queue for background jobs.
    
    Features:
    - Priority-based ordering (CRITICAL > HIGH > MEDIUM > LOW)
    - FIFO within same priority level
    - Thread-safe async operations
    - No persistence (reference implementation only)
    
    Note:
        This is a reference implementation. Production systems should use
        persistent queues (Redis, RabbitMQ, AWS SQS, etc.).
    """
    
    def __init__(self, maxsize: int = 0):
        """Initialize in-memory queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self._queue: asyncio.PriorityQueue[PrioritizedJob] = asyncio.PriorityQueue(maxsize=maxsize)
        self._lock = asyncio.Lock()
        
        logger.info(f"Initialized in-memory queue (maxsize={maxsize})")
    
    async def enqueue(self, job_input: JobInput) -> None:
        """Add job to queue with priority ordering.
        
        Args:
            job_input: Job to enqueue
            
        Raises:
            asyncio.QueueFull: If queue is at capacity
        """
        async with self._lock:
            prioritized_job = PrioritizedJob.from_job_input(job_input)
            await self._queue.put(prioritized_job)
            
            logger.debug(
                f"Job enqueued: {job_input.job_id}",
                extra={
                    "job_id": job_input.job_id,
                    "priority": job_input.priority.value,
                    "queue_size": self._queue.qsize()
                }
            )
    
    async def dequeue(self) -> Optional[JobInput]:
        """Get next highest priority job.
        
        Returns:
            Next job or None if queue is empty
        """
        try:
            prioritized_job = self._queue.get_nowait()
            
            logger.debug(
                f"Job dequeued: {prioritized_job.job_input.job_id}",
                extra={
                    "job_id": prioritized_job.job_input.job_id,
                    "priority": prioritized_job.job_input.priority.value,
                    "queue_size": self._queue.qsize()
                }
            )
            
            return prioritized_job.job_input
            
        except asyncio.QueueEmpty:
            return None
    
    async def peek(self) -> Optional[JobInput]:
        """View next job without removing.
        
        Returns:
            Next job or None if empty
        """
        if self._queue.empty():
            return None
        
        # Get and immediately put back
        prioritized_job = await self._queue.get()
        await self._queue.put(prioritized_job)
        
        return prioritized_job.job_input
    
    def size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of jobs in queue
        """
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Returns:
            True if no jobs in queue
        """
        return self._queue.empty()
    
    async def clear(self) -> None:
        """Clear all jobs from queue (for testing).
        
        Warning:
            This operation is destructive and should only be used
            in test environments.
        """
        async with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            logger.warning("Queue cleared (all jobs removed)")
