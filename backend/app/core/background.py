"""Background Job Management for Async Traceability.

PHASE 3: TRACEABILITY & ASYNC SAFETY

This module implements the core infrastructure for safe asynchronous processing:
1. Job Enqueueing with Trace Propagation
2. Status Persistence (MongoDB)
3. Traceability (linking jobs to original requests)

Architecture:
- Singleton `job_manager` handles all async operations
- Uses FastAPI `BackgroundTasks` for execution
- Uses MongoDB for status tracking logic
"""

import logging
import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from fastapi import BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient

from app.config.settings import settings
from app.orchestrator.execution_context import ExecutionContext
# Import orchestrator inside function to avoid circular import if needed
# but orchestrator imports this file? No, orchestrator will import this.

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Execution status of a background job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundJobManager:
    """Manages asynchronous background jobs with traceability."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Any = None
        self._orchestrator_ref = None  # Lazy reference to break circular dependency

    def initialize(self):
        """Initialize MongoDB connection.
        
        Must be called during application startup.
        """
        if not self.client:
            logger.info("Initializing BackgroundJobManager MongoDB client...")
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DB]  # Explicit database name
            logger.info("BackgroundJobManager initialized")

    def shutdown(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("BackgroundJobManager shutdown")

    def _get_orchestrator(self):
        """Lazy load orchestrator to avoid circular imports."""
        if not self._orchestrator_ref:
            from app.orchestrator.orchestrator import orchestrator
            self._orchestrator_ref = orchestrator
        return self._orchestrator_ref

    async def enqueue_job(
        self,
        background_tasks: BackgroundTasks,
        pipeline_name: str,
        payload: dict,
        context: ExecutionContext
    ) -> str:
        """Enqueue a pipeline for background execution.
        
        Args:
            background_tasks: FastAPI background tasks handler
            pipeline_name: Name of pipeline to run
            payload: Input payload
            context: Request context (must contain trace_id)
            
        Returns:
            job_id: Unique identifier for the background job
        """
        job_id = f"job_{uuid4()}"
        
        # 1. Persist initial status (PENDING)
        job_record = {
            "job_id": job_id,
            "trace_id": context.trace_id,
            "pipeline_name": pipeline_name,
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "user_id": context.user_id,
            "request_source": context.request_source
        }
        
        if self.db is not None:
             await self.db.background_jobs.insert_one(job_record)
        else:
            logger.warning("BackgroundJobManager DB not initialized! Job status will not be persisted.")

        logger.info(
            f"Enqueuing background job {job_id}",
            extra={
                "trace_id": context.trace_id,
                "pipeline_name": pipeline_name,
                "job_id": job_id
            }
        )

        # 2. Add to background tasks
        background_tasks.add_task(
            self._run_job_wrapper,
            job_id=job_id,
            pipeline_name=pipeline_name,
            payload=payload,
            context=context
        )
        
        return job_id

    async def _run_job_wrapper(
        self,
        job_id: str,
        pipeline_name: str,
        payload: dict,
        context: ExecutionContext
    ) -> None:
        """Internal wrapper to run the job and update status.
        
        This runs IN THE BACKGROUND after response is sent.
        """
        logger.info(
            f"Starting background job {job_id}", 
            extra={"trace_id": context.trace_id, "job_id": job_id}
        )
        
        # Update status to RUNNING
        await self._update_status(job_id, JobStatus.RUNNING)
        
        try:
            orchestrator = self._get_orchestrator()
            
            # Execute pipeline
            # Note: We re-use the context, preserving trace_id
            result = await orchestrator.execute_pipeline(
                pipeline_name=pipeline_name,
                payload=payload,
                context=context
            )
            
            # Update status to COMPLETED
            await self._update_status(
                job_id, 
                JobStatus.COMPLETED,
                result_summary={
                    "success": result.get("success", False),
                    "total_duration_ms": result.get("total_duration_ms")
                }
            )
            
        except Exception as e:
            logger.exception(
                f"Background job {job_id} failed",
                extra={"trace_id": context.trace_id, "job_id": job_id}
            )
            
            # Update status to FAILED
            await self._update_status(
                job_id, 
                JobStatus.FAILED,
                error=str(e)
            )

    async def _update_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        result_summary: dict = None,
        error: str = None
    ):
        """Update job status in MongoDB."""
        if self.db is None:
            return

        update_doc = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result_summary:
            update_doc["result_summary"] = result_summary
        
        if error:
            update_doc["error"] = error
            
        await self.db.background_jobs.update_one(
            {"job_id": job_id},
            {"$set": update_doc}
        )

    async def get_job(self, job_id: str) -> Optional[dict]:
        """Retrieve job details by ID."""
        if self.db is None:
            return None
            
        return await self.db.background_jobs.find_one(
            {"job_id": job_id},
            {"_id": 0}  # Exclude MongoDB ID
        )


# Singleton instance
job_manager = BackgroundJobManager()
