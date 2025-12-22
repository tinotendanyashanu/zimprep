"""Stateless worker for job execution.

Executes jobs from queue with full traceability and error handling.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable

from app.engines.background_processing.schemas.input import JobInput, TaskType
from app.engines.background_processing.schemas.output import ArtifactReference
from app.engines.background_processing.errors import TaskTypeNotSupportedError

logger = logging.getLogger(__name__)


class Worker:
    """Stateless job executor.
    
    Constraints:
    - No shared state between executions
    - Restart-safe (can be killed and restarted)
    - Routes jobs to appropriate executors
    - Tracks execution metrics
    - Full trace-aware logging
    """
    
    def __init__(
        self,
        worker_id: str,
        job_executors: Dict[TaskType, Callable[[Dict[str, Any], str, str], Awaitable[list[ArtifactReference]]]]
    ):
        """Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            job_executors: Map of task types to executor functions
        """
        self.worker_id = worker_id
        self.job_executors = job_executors
        self._current_job_id: str | None = None
        
        logger.info(f"Worker initialized: {worker_id}")
    
    async def execute_job(self, job_input: JobInput) -> tuple[list[ArtifactReference], datetime, datetime]:
        """Execute a single job.
        
        Args:
            job_input: Job to execute
            
        Returns:
            Tuple of (artifacts, start_time, end_time)
            
        Raises:
            TaskTypeNotSupportedError: If task type has no executor
            Exception: If job execution fails
        """
        start_time = datetime.utcnow()
        self._current_job_id = job_input.job_id
        
        logger.info(
            f"Worker {self.worker_id} starting job {job_input.job_id}",
            extra={
                "worker_id": self.worker_id,
                "job_id": job_input.job_id,
                "trace_id": job_input.trace_id,
                "task_type": job_input.task_type.value
            }
        )
        
        try:
            # Route to appropriate executor
            executor = self.job_executors.get(job_input.task_type)
            
            if not executor:
                raise TaskTypeNotSupportedError(
                    task_type=job_input.task_type.value,
                    trace_id=job_input.trace_id
                )
            
            # Execute job
            artifacts = await executor(
                job_input.validated_payload,
                job_input.trace_id,
                job_input.job_id
            )
            
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(
                f"Worker {self.worker_id} completed job {job_input.job_id}",
                extra={
                    "worker_id": self.worker_id,
                    "job_id": job_input.job_id,
                    "trace_id": job_input.trace_id,
                    "execution_time_ms": execution_time_ms,
                    "artifacts": len(artifacts)
                }
            )
            
            return artifacts, start_time, end_time
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(
                f"Worker {self.worker_id} job {job_input.job_id} failed: {e}",
                extra={
                    "worker_id": self.worker_id,
                    "job_id": job_input.job_id,
                    "trace_id": job_input.trace_id,
                    "execution_time_ms": execution_time_ms,
                    "error": str(e)
                }
            )
            
            raise
        
        finally:
            self._current_job_id = None
    
    @property
    def is_busy(self) -> bool:
        """Check if worker is currently executing a job.
        
        Returns:
            True if worker is executing a job
        """
        return self._current_job_id is not None
    
    @property
    def current_job_id(self) -> str | None:
        """Get ID of currently executing job.
        
        Returns:
            Job ID or None if idle
        """
        return self._current_job_id
