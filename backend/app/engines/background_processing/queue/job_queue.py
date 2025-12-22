"""Abstract job queue interface.

Defines the contract for background job queue implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.engines.background_processing.schemas.input import JobInput


class JobQueue(ABC):
    """Abstract interface for background job queues.
    
    All queue implementations must provide:
    - Thread-safe enqueue/dequeue operations
    - Priority-based ordering
    - Size and emptiness checks
    """
    
    @abstractmethod
    async def enqueue(self, job_input: JobInput) -> None:
        """Add job to queue.
        
        Args:
            job_input: Job to enqueue
            
        Raises:
            Exception: If enqueue fails
        """
        pass
    
    @abstractmethod
    async def dequeue(self) -> Optional[JobInput]:
        """Get next job from queue.
        
        Returns highest priority job, or None if queue is empty.
        
        Returns:
            Next job or None if empty
        """
        pass
    
    @abstractmethod
    async def peek(self) -> Optional[JobInput]:
        """View next job without removing it.
        
        Returns:
            Next job or None if empty
        """
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of jobs in queue
        """
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Returns:
            True if queue has no jobs
        """
        pass
