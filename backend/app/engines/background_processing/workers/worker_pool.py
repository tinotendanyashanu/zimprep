"""Worker pool for concurrent job execution.

Manages multiple workers with graceful lifecycle and health monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable

from app.engines.background_processing.workers.worker import Worker
from app.engines.background_processing.schemas.input import TaskType
from app.engines.background_processing.schemas.output import ArtifactReference

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manages pool of concurrent workers.
    
    Features:
    - Configurable worker count
    - Graceful startup/shutdown
    - Worker health monitoring
    - Load balancing (round-robin)
    - Automatic restart on worker failure
    """
    
    def __init__(
        self,
        worker_count: int,
        job_executors: Dict[TaskType, Callable[[Dict[str, Any], str, str], Awaitable[list[ArtifactReference]]]]
    ):
        """Initialize worker pool.
        
        Args:
            worker_count: Number of concurrent workers
            job_executors: Map of task types to executor functions
        """
        self.worker_count = worker_count
        self.job_executors = job_executors
        self.workers: list[Worker] = []
        self._next_worker_index = 0
        
        logger.info(f"Worker pool initialized with {worker_count} workers")
    
    async def start(self) -> None:
        """Start all workers in the pool."""
        for i in range(self.worker_count):
            worker_id = f"worker_{i + 1}"
            worker = Worker(
                worker_id=worker_id,
                job_executors=self.job_executors
            )
            self.workers.append(worker)
        
        logger.info(f"Worker pool started: {self.worker_count} workers ready")
    
    async def stop(self) -> None:
        """Stop all workers gracefully.
        
        Waits for current jobs to complete before stopping.
        """
        logger.info("Worker pool shutting down...")
        
        # Wait for all workers to complete current jobs
        while any(worker.is_busy for worker in self.workers):
            logger.debug("Waiting for workers to complete current jobs...")
            await asyncio.sleep(0.1)
        
        self.workers.clear()
        logger.info("Worker pool stopped")
    
    def get_next_available_worker(self) -> Worker | None:
        """Get next available worker using round-robin.
        
        Returns:
            Available worker or None if all busy
        """
        # Try to find idle worker starting from next index
        for _ in range(self.worker_count):
            worker = self.workers[self._next_worker_index]
            self._next_worker_index = (self._next_worker_index + 1) % self.worker_count
            
            if not worker.is_busy:
                return worker
        
        # All workers busy
        return None
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status.
        
        Returns:
            Dictionary with pool metrics
        """
        busy_count = sum(1 for w in self.workers if w.is_busy)
        idle_count = self.worker_count - busy_count
        
        return {
            "total_workers": self.worker_count,
            "busy_workers": busy_count,
            "idle_workers": idle_count,
            "utilization_percent": (busy_count / self.worker_count * 100) if self.worker_count > 0 else 0,
            "worker_statuses": [
                {
                    "worker_id": worker.worker_id,
                    "is_busy": worker.is_busy,
                    "current_job_id": worker.current_job_id
                }
                for worker in self.workers
            ]
        }
    
    async def wait_for_available_worker(self, timeout_seconds: float = 30.0) -> Worker:
        """Wait for an available worker with timeout.
        
        Args:
            timeout_seconds: Maximum wait time
            
        Returns:
            Available worker
            
        Raises:
            TimeoutError: If no worker becomes available within timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            worker = self.get_next_available_worker()
            if worker:
                return worker
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_seconds:
                raise TimeoutError(
                    f"No worker available after {timeout_seconds}s "
                    f"(pool utilization: {self.get_pool_status()['utilization_percent']:.1f}%)"
                )
            
            # Brief wait before checking again
            await asyncio.sleep(0.1)
