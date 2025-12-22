"""Background Processing Engine

Main orchestrator-facing entry point for asynchronous job execution.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.background_processing.schemas.input import JobInput, TaskType
from app.engines.background_processing.schemas.output import JobOutput, JobStatus

from app.engines.background_processing.services import (
    MarkingJobExecutor,
    EmbeddingJobExecutor,
    AnalyticsJobExecutor,
    MaintenanceJobExecutor,
    RetryManager,
    ResourceMonitor,
    ArtifactManager,
)

from app.engines.background_processing.repositories import (
    JobRepository,
    ArtifactRepository,
)

from app.engines.background_processing.errors import (
    BackgroundProcessingError,
    InvalidJobConfigurationError,
    TaskTypeNotSupportedError,
    ErrorCode,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "background_processing"
ENGINE_VERSION = "1.0.0"


class BackgroundProcessingEngine:
    """Production-grade asynchronous job execution engine for ZimPrep.
    
    Executes long-running, heavy, or non-interactive workloads asynchronously.
    
    Strict Rules:
    - Only executes work authorized by orchestrator
    - Never calls other engines
    - Never makes business decisions
    - Never interprets or modifies results
    - Fully idempotent
    - Complete audit trail
    """
    
    def __init__(self):
        """Initialize engine with all services and repositories."""
        # Task executors
        self.marking_executor = MarkingJobExecutor()
        self.embedding_executor = EmbeddingJobExecutor()
        self.analytics_executor = AnalyticsJobExecutor()
        self.maintenance_executor = MaintenanceJobExecutor()
        
        # Infrastructure services
        self.retry_manager = RetryManager()
        self.resource_monitor = ResourceMonitor()
        self.artifact_manager = ArtifactManager()
        
        # Repositories
        self.job_repo = JobRepository()
        self.artifact_repo = ArtifactRepository()
        
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[JobOutput]:
        """Execute background job.
        
        Execution Flow:
        1. Parse and validate JobInput
        2. Verify orchestrator authorization
        3. Route to task-specific executor
        4. Monitor resource metrics
        5. Apply retry logic on failures
        6. Persist job artifacts
        7. Emit audit trail
        8. Return JobOutput
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with JobOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        retry_count = 0
        
        try:
            # Step 1: Parse and validate input
            input_data = JobInput(**payload)
            
            logger.info(
                "Background job execution started",
                extra={
                    "trace_id": trace_id,
                    "job_id": input_data.job_id,
                    "task_type": input_data.task_type.value,
                    "origin_engine": input_data.origin_engine,
                    "priority": input_data.priority.value
                }
            )
            
            # Step 2: Create job record (idempotency check)
            await self.job_repo.create_job_record(
                job_id=input_data.job_id,
                trace_id=trace_id,
                task_type=input_data.task_type.value,
                origin_engine=input_data.origin_engine,
                payload=input_data.validated_payload,
                priority=input_data.priority.value,
                requested_at=input_data.requested_at
            )
            
            # Step 3-5: Execute job with retry and monitoring
            async with self.resource_monitor.track_job(trace_id, input_data.job_id):
                result_artifacts, retry_count = await self.retry_manager.execute_with_retry(
                    operation=lambda: self._execute_task(input_data, trace_id),
                    retry_policy=input_data.retry_policy,
                    trace_id=trace_id,
                    job_id=input_data.job_id,
                    operation_name=f"{input_data.task_type.value}_execution"
                )
            
            # Get resource metrics
            resource_metrics = self.resource_monitor.get_metrics()
            
            # Step 6: Persist artifacts
            persisted_artifacts = await self.artifact_manager.persist_artifacts(
                job_id=input_data.job_id,
                artifacts=result_artifacts,
                trace_id=trace_id
            )
            
            # Step 7: Update job status
            await self.job_repo.update_job_status(
                job_id=input_data.job_id,
                trace_id=trace_id,
                status=JobStatus.SUCCESS.value,
                execution_time_ms=resource_metrics.execution_time_ms,
                retry_count=retry_count
            )
            
            # Step 8: Build success response
            output = JobOutput(
                trace_id=trace_id,
                job_id=input_data.job_id,
                status=JobStatus.SUCCESS,
                execution_time_ms=resource_metrics.execution_time_ms,
                resource_metrics=resource_metrics,
                artifact_references=persisted_artifacts,
                retry_count=retry_count,
                completed_at=datetime.utcnow().isoformat()
            )
            
            return self._build_response(output, trace_id, start_time)
            
        except ValidationError as e:
            logger.error(
                "Input validation failed",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Invalid input: {str(e)}",
                error_code=ErrorCode.INVALID_JOB_CONFIG,
                trace_id=trace_id,
                start_time=start_time,
                job_id=payload.get("job_id", "unknown")
            )
        
        except BackgroundProcessingError as e:
            logger.error(
                f"Job execution failed: {e.error_code.value}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            
            # Update job status to failed
            if "job_id" in payload:
                await self.job_repo.update_job_status(
                    job_id=payload["job_id"],
                    trace_id=trace_id,
                    status=JobStatus.FAILED.value,
                    error_code=e.error_code.value,
                    error_message=str(e),
                    retry_count=retry_count
                )
            
            return self._build_error_response(
                error_message=str(e),
                error_code=e.error_code,
                trace_id=trace_id,
                start_time=start_time,
                job_id=payload.get("job_id", "unknown")
            )
        
        except Exception as e:
            logger.exception(
                "Unexpected error in engine",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                error_code=ErrorCode.EXECUTION_FAILED,
                trace_id=trace_id,
                start_time=start_time,
                job_id=payload.get("job_id", "unknown")
            )
    
    async def _execute_task(
        self,
        input_data: JobInput,
        trace_id: str
    ):
        """Route to appropriate task executor.
        
        Args:
            input_data: Validated job input
            trace_id: Trace ID
            
        Returns:
            List of artifact references
            
        Raises:
            TaskTypeNotSupportedError: If task type not supported
        """
        task_type = input_data.task_type
        payload = input_data.validated_payload
        job_id = input_data.job_id
        
        # Route based on task type
        if task_type == TaskType.MARKING_JOB:
            return await self.marking_executor.execute(payload, trace_id, job_id)
        
        elif task_type == TaskType.EMBEDDING_GENERATION:
            return await self.embedding_executor.execute(payload, trace_id, job_id)
        
        elif task_type == TaskType.ANALYTICS_AGGREGATION:
            return await self.analytics_executor.execute(payload, trace_id, job_id)
        
        elif task_type == TaskType.INFRASTRUCTURE_MAINTENANCE:
            return await self.maintenance_executor.execute(payload, trace_id, job_id)
        
        else:
            raise TaskTypeNotSupportedError(
                task_type=task_type.value,
                trace_id=trace_id
            )
    
    def _build_response(
        self,
        output: JobOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[JobOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0,  # Execution either succeeds or fails
        )
        
        logger.info(
            f"Job execution completed: {output.status.value}",
            extra={
                "trace_id": trace_id,
                "job_id": output.job_id,
                "execution_time_ms": output.execution_time_ms,
                "artifacts": len(output.artifact_references),
                "retry_count": output.retry_count
            }
        )
        
        return EngineResponse(
            success=True,
            data=output,
            error=None,
            trace=trace
        )
    
    def _build_error_response(
        self,
        error_message: str,
        error_code: ErrorCode,
        trace_id: str,
        start_time: datetime,
        job_id: str
    ) -> EngineResponse[JobOutput]:
        """Build error EngineResponse with failed output.
        
        Args:
            error_message: Error message
            error_code: Typed error code
            trace_id: Trace ID
            start_time: Execution start time
            job_id: Job ID
            
        Returns:
            EngineResponse with failed output
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0,
        )
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Build minimal resource metrics for failed job
        from app.engines.background_processing.schemas.output import ResourceMetrics
        resource_metrics = ResourceMetrics(
            cpu_usage_percent=0.0,
            memory_usage_mb=0.0,
            execution_time_ms=execution_time_ms
        )
        
        output = JobOutput(
            trace_id=trace_id,
            job_id=job_id,
            status=JobStatus.FAILED,
            execution_time_ms=execution_time_ms,
            resource_metrics=resource_metrics,
            error_code=error_code.value,
            error_message=error_message,
            artifact_references=[],
            retry_count=0,
            completed_at=datetime.utcnow().isoformat()
        )
        
        logger.warning(
            f"Job execution failed: {error_code.value}",
            extra={
                "trace_id": trace_id,
                "job_id": job_id,
                "error": error_message
            }
        )
        
        return EngineResponse(
            success=False,
            data=output,
            error=error_message,
            trace=trace
        )
