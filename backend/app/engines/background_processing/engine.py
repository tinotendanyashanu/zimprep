"""Background Processing Engine

Main orchestrator-facing entry point for asynchronous job execution.
Refactored to use queue, workers, policies, jobs, and observability architecture.
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

# New architecture imports
from app.engines.background_processing.jobs import (
    MarkingJob,
    EmbeddingJob,
    AnalyticsJob,
    MaintenanceJob,
)

from app.engines.background_processing.policies import (
    RetryPolicy,
    IdempotencyPolicy,
)

from app.engines.background_processing.observability import MetricsCollector

from app.engines.background_processing.repositories import (
    JobRepository,
    ArtifactRepository,
)

# Artifact manager from services (still needed)
from app.engines.background_processing.services import ArtifactManager

from app.engines.background_processing.errors import (
    BackgroundProcessingError,
    InvalidJobConfigurationError,
    TaskTypeNotSupportedError,
    ErrorCode,
)


logger = logging.getLogger(__name__)

ENGINE_NAME = "background_processing"
ENGINE_VERSION = "2.0.0"  # Updated to reflect new architecture


class BackgroundProcessingEngine:
    """Production-grade asynchronous job execution engine for ZimPrep.
    
    Executes long-running, heavy, or non-interactive workloads asynchronously.
    
    Architecture:
    - Queue-based job distribution
    - Worker pool for concurrency
    - Retry and idempotency policies
    - Comprehensive observability
    
    Strict Rules:
    - Only executes work authorized by orchestrator
    - Never calls other engines
    - Never makes business decisions
    - Never interprets or modifies results
    - Fully idempotent
    - Complete audit trail
    """
    
    def __init__(self):
        """Initialize engine with new architecture components."""
        # Job executors (migrated from services)
        self.marking_job = MarkingJob()
        self.embedding_job = EmbeddingJob()
        self.analytics_job = AnalyticsJob()
        self.maintenance_job = MaintenanceJob()
        
        # Map task types to job executors
        self.job_executors = {
            TaskType.MARKING_JOB: self.marking_job.execute,
            TaskType.EMBEDDING_GENERATION: self.embedding_job.execute,
            TaskType.ANALYTICS_AGGREGATION: self.analytics_job.execute,
            TaskType.INFRASTRUCTURE_MAINTENANCE: self.maintenance_job.execute,
        }
        
        # Policies
        self.retry_policy = RetryPolicy()
        self.idempotency_policy = IdempotencyPolicy()
        
        # Observability
        self.metrics_collector = MetricsCollector()
        
        # Infrastructure services (kept from original)
        self.artifact_manager = ArtifactManager()
        
        # Repositories
        self.job_repo = JobRepository()
        self.artifact_repo = ArtifactRepository()
        
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION} (New Architecture)")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[JobOutput]:
        """Execute background job.
        
        Execution Flow:
        1. Parse and validate JobInput
        2. Check idempotency (duplicate job detection)
        3. Verify orchestrator authorization
        4. Route to task-specific executor via retry policy
        5. Monitor resource metrics
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
            
            # Step 2: Check idempotency (new)
            cached_result = await self.idempotency_policy.check_duplicate(
                job_id=input_data.job_id,
                trace_id=trace_id
            )
            
            if cached_result:
                logger.info(
                    f"Returning cached result for duplicate job: {input_data.job_id}",
                    extra={"trace_id": trace_id, "job_id": input_data.job_id}
                )
                return self._build_response(cached_result, trace_id, start_time)
            
            # Step 3: Create job record
            await self.job_repo.create_job_record(
                job_id=input_data.job_id,
                trace_id=trace_id,
                task_type=input_data.task_type.value,
                origin_engine=input_data.origin_engine,
                payload=input_data.validated_payload,
                priority=input_data.priority.value,
                requested_at=input_data.requested_at
            )
            
            # Step 4-5: Execute job with retry and monitoring (updated)
            async with self.metrics_collector.track_job(trace_id, input_data.job_id):
                result_artifacts, retry_count = await self.retry_policy.execute_with_retry(
                    operation=lambda: self._execute_task(input_data, trace_id),
                    retry_policy=input_data.retry_policy,
                    trace_id=trace_id,
                    job_id=input_data.job_id,
                    operation_name=f"{input_data.task_type.value}_execution"
                )
            
            # Get resource metrics (updated)
            resource_metrics = self.metrics_collector.get_metrics()
            
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
            
            # Record metrics (new)
            self.metrics_collector.record_job_completion(
                task_type=input_data.task_type.value,
                success=True
            )
            
            if retry_count > 0:
                self.metrics_collector.record_retry(input_data.task_type.value)
            
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
            
            # Cache result for idempotency (new)
            await self.idempotency_policy.cache_result(
                job_id=input_data.job_id,
                job_output=output,
                trace_id=trace_id
            )
            
            return self._build_response(output, trace_id, start_time)
        
        except ValidationError as e:
            logger.error(
                "Input validation failed",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            
            # Record failure metrics (new)
            self.metrics_collector.record_job_completion(
                task_type="unknown",
                success=False,
                error_code=ErrorCode.INVALID_JOB_CONFIG.value
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
            
            # Record failure metrics (new)
            if "job_id" in payload:
                task_type = payload.get("task_type", "unknown")
                self.metrics_collector.record_job_completion(
                    task_type=task_type,
                    success=False,
                    error_code=e.error_code.value
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
        
        # Route using job_executors mapping (updated for new architecture)
        executor = self.job_executors.get(task_type)
        
        if not executor:
            raise TaskTypeNotSupportedError(
                task_type=task_type.value,
                trace_id=trace_id
            )
        
        return await executor(payload, trace_id, job_id)
    
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
