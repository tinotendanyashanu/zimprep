"""Orchestrator for managing pipeline and engine execution.

This is the ONLY component that coordinates engine execution.
"""

import inspect
import logging
from datetime import datetime
from typing import Any

from app.contracts.engine_response import EngineResponse
from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.engine_registry import engine_registry
from app.orchestrator.pipelines import (
    get_pipeline,
    validate_pipeline_name,
    BLOCKED_ENGINES_DURING_APPEAL,
    BLOCKED_ENGINES_DURING_REPORTING
)


logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails."""
    
    def __init__(
        self,
        message: str,
        pipeline_name: str,
        failed_engine: str | None = None,
        trace_id: str | None = None
    ):
        super().__init__(message)
        self.pipeline_name = pipeline_name
        self.failed_engine = failed_engine
        self.trace_id = trace_id


class AppealIntegrityError(Exception):
    """Raised when appeal reconstruction integrity is violated.
    
    CRITICAL: This error is thrown when AI engines attempt to execute
    during an appeal reconstruction pipeline. This is a HARD FAIL
    to ensure legal defensibility.
    """
    
    def __init__(
        self,
        message: str,
        pipeline_name: str,
        blocked_engine: str,
        trace_id: str | None = None
    ):
        super().__init__(message)
        self.pipeline_name = pipeline_name
        self.blocked_engine = blocked_engine
        self.trace_id = trace_id


class ReportingIntegrityError(Exception):
    """Raised when reporting pipeline integrity is violated.
    
    CRITICAL: This error is thrown when AI engines or recalculation engines
    attempt to execute during a reporting pipeline. Reporting is READ-ONLY.
    """
    
    def __init__(
        self,
        message: str,
        pipeline_name: str,
        blocked_engine: str,
        trace_id: str | None = None
    ):
        super().__init__(message)
        self.pipeline_name = pipeline_name
        self.blocked_engine = blocked_engine
        self.trace_id = trace_id


class Orchestrator:
    """Central orchestrator for managing engine execution.
    
    CRITICAL RULES:
    1. Engines MUST be executed via pipelines (not directly)
    2. Pipeline order is immutable and defined in pipelines.py
    3. All engines MUST return EngineResponse
    4. Full observability is mandatory (logging, timing, etc.)
    5. Fail-fast on any engine failure
    6. Appeal pipelines MUST NOT execute AI engines (HARD FAIL)
    7. Reporting pipelines MUST be read-only (HARD FAIL on AI/recalc)
    """
    
    def __init__(self, registry):
        self.registry = registry
    
    async def execute_pipeline(
        self,
        pipeline_name: str,
        payload: dict,
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Execute a full pipeline with all engines in canonical order.
        
        This is the PRIMARY execution method for production.
        Supports both synchronous and asynchronous engines via polymorphic execution.
        
        CRITICAL: Appeal pipelines enforce AI engine blocking.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            payload: Input data for the pipeline
            context: Execution context with trace_id and metadata
            
        Returns:
            Dictionary containing:
            - trace_id: Request trace ID
            - request_id: Request ID
            - pipeline_name: Name of executed pipeline
            - success: Whether pipeline completed successfully
            - engine_outputs: Results from each engine
            - started_at: Pipeline start time
            - completed_at: Pipeline completion time
            - total_duration_ms: Total execution time
            - error: Error message if failed (optional)
            - failed_engine: Name of failed engine (optional)
            
        Raises:
            PipelineExecutionError: If pipeline execution fails
            AppealIntegrityError: If AI engine attempts to execute during appeal
            ReportingIntegrityError: If AI engine attempts to execute during reporting
        """
        trace_id = context.trace_id
        request_id = context.request_id
        pipeline_start = datetime.utcnow()
        
        logger.info(
            "Pipeline execution started",
            extra={
                "pipeline_name": pipeline_name,
                "trace_id": trace_id,
                "request_id": request_id,
                "user_id": context.user_id,
                "request_source": context.request_source
            }
        )
        
        # Validate pipeline exists
        if not validate_pipeline_name(pipeline_name):
            error_msg = f"Pipeline '{pipeline_name}' not found"
            logger.error(error_msg, extra={"trace_id": trace_id})
            raise PipelineExecutionError(
                message=error_msg,
                pipeline_name=pipeline_name,
                trace_id=trace_id
            )
        
        # Get pipeline definition
        engine_sequence = get_pipeline(pipeline_name)
        if not engine_sequence:
            error_msg = f"Pipeline '{pipeline_name}' has no engines"
            logger.error(error_msg, extra={"trace_id": trace_id})
            raise PipelineExecutionError(
                message=error_msg,
                pipeline_name=pipeline_name,
                trace_id=trace_id
            )
        
        # CRITICAL: Enforce AI engine blocking for appeal pipelines
        is_appeal_pipeline = "appeal" in pipeline_name.lower()
        is_reporting_pipeline = "reporting" in pipeline_name.lower()
        
        if is_appeal_pipeline:
            self._validate_appeal_pipeline_integrity(
                pipeline_name, engine_sequence, trace_id
            )
            logger.info(
                f"[{trace_id}] FORENSIC MODE: Appeal pipeline validated - "
                f"no AI engines will execute"
            )
        
        if is_reporting_pipeline:
            self._validate_reporting_pipeline_integrity(
                pipeline_name, engine_sequence, trace_id
            )
            # Set read_only flag in payload for engines
            payload["read_only"] = True
            logger.info(
                f"[{trace_id}] READ-ONLY MODE: Reporting pipeline validated - "
                f"no AI engines or recalculation will execute"
            )
        
        # Execute engines in order
        engine_outputs: dict[str, dict[str, Any]] = {}
        

        
        for engine_name in engine_sequence:
            engine_start = datetime.utcnow()
            
            try:
                logger.info(
                    "Engine execution started",
                    extra={
                        "engine_name": engine_name,
                        "trace_id": trace_id,
                        "pipeline_name": pipeline_name
                    }
                )
                
                # Get engine from registry
                engine = self.registry.get(engine_name)
                if not engine:
                    raise RuntimeError(
                        f"Engine '{engine_name}' not registered in orchestrator"
                    )
                
                # Execute engine (polymorphic: async or sync)
                # This is the critical pattern that makes the orchestrator production-grade
                if inspect.iscoroutinefunction(engine.run):
                    # Engine is async - await it
                    result = await engine.run(payload, context)
                else:
                    # Engine is sync - call directly
                    result = engine.run(payload, context)
                
                # Validate output contract
                if not isinstance(result, EngineResponse):
                    raise RuntimeError(
                        f"Engine '{engine_name}' violated contract: "
                        f"returned {type(result).__name__} instead of EngineResponse"
                    )
                
                engine_end = datetime.utcnow()
                duration_ms = (engine_end - engine_start).total_seconds() * 1000
                
                # Store engine output (immutable aggregation)
                engine_outputs[engine_name] = {
                    "engine_name": engine_name,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                    "started_at": engine_start,
                    "completed_at": engine_end,
                    "duration_ms": duration_ms,
                    "engine_version": result.trace.engine_version,
                    "confidence": result.trace.confidence
                }
                
                logger.info(
                    "Engine execution completed",
                    extra={
                        "engine_name": engine_name,
                        "trace_id": trace_id,
                        "duration_ms": duration_ms,
                        "success": result.success,
                        "confidence": result.trace.confidence
                    }
                )
                
                # FAIL-FAST: Abort on engine failure
                if not result.success:
                    error_msg = (
                        f"Engine '{engine_name}' failed: {result.error}"
                    )
                    logger.error(
                        "Pipeline aborted due to engine failure",
                        extra={
                            "engine_name": engine_name,
                            "trace_id": trace_id,
                            "error": result.error
                        }
                    )
                    raise PipelineExecutionError(
                        message=error_msg,
                        pipeline_name=pipeline_name,
                        failed_engine=engine_name,
                        trace_id=trace_id
                    )
                
            except PipelineExecutionError:
                # Re-raise pipeline errors
                raise
                
            except Exception as e:
                engine_end = datetime.utcnow()
                duration_ms = (engine_end - engine_start).total_seconds() * 1000
                
                error_msg = f"Engine '{engine_name}' crashed: {str(e)}"
                logger.exception(
                    "Engine execution crashed",
                    extra={
                        "engine_name": engine_name,
                        "trace_id": trace_id,
                        "duration_ms": duration_ms
                    }
                )
                
                raise PipelineExecutionError(
                    message=error_msg,
                    pipeline_name=pipeline_name,
                    failed_engine=engine_name,
                    trace_id=trace_id
                ) from e
        
        # Pipeline completed successfully
        pipeline_end = datetime.utcnow()
        total_duration_ms = (pipeline_end - pipeline_start).total_seconds() * 1000
        
        logger.info(
            "Pipeline execution completed",
            extra={
                "pipeline_name": pipeline_name,
                "trace_id": trace_id,
                "total_duration_ms": total_duration_ms,
                "engines_executed": len(engine_outputs),
                "success": True
            }
        )
        
        # Return immutable aggregated output
        return {
            "trace_id": trace_id,
            "request_id": request_id,
            "pipeline_name": pipeline_name,
            "success": True,
            "engine_outputs": engine_outputs,
            "started_at": pipeline_start,
            "completed_at": pipeline_end,
            "total_duration_ms": total_duration_ms
        }
    
    def execute(
        self,
        engine_name: str,
        payload: dict,
        context: ExecutionContext
    ) -> Any:
        """Execute a single engine directly.
        
        ⚠️ DEPRECATED: This method exists for backward compatibility only.
        Production code MUST use execute_pipeline() instead.
        
        Args:
            engine_name: Name of engine to execute
            payload: Input data
            context: Execution context
            
        Returns:
            Engine result
            
        Raises:
            RuntimeError: If engine not registered
        """
        logger.warning(
            "Direct engine execution used (deprecated)",
            extra={
                "engine_name": engine_name,
                "trace_id": context.trace_id
            }
        )
        
        engine = self.registry.get(engine_name)
        if not engine:
            raise RuntimeError(f"Engine {engine_name} not registered")
        
        return engine.run(payload, context)
    
    def _validate_appeal_pipeline_integrity(
        self,
        pipeline_name: str,
        engine_sequence: list[str],
        trace_id: str
    ) -> None:
        """Validate that appeal pipeline contains no AI engines.
        
        CRITICAL: This is a HARD FAIL check. If any AI engine is found
        in an appeal pipeline, the entire pipeline is rejected.
        
        This ensures legal defensibility - appeals NEVER re-execute AI.
        
        Args:
            pipeline_name: Name of the pipeline being executed
            engine_sequence: List of engine names in the pipeline
            trace_id: Request trace ID for logging
            
        Raises:
            AppealIntegrityError: If AI engine is found in pipeline
        """
        for engine_name in engine_sequence:
            if engine_name in BLOCKED_ENGINES_DURING_APPEAL:
                error_msg = (
                    f"APPEAL INTEGRITY VIOLATION: AI engine '{engine_name}' "
                    f"cannot execute during appeal reconstruction. "
                    f"Appeals are forensic only - no AI re-execution allowed."
                )
                logger.error(
                    error_msg,
                    extra={
                        "trace_id": trace_id,
                        "pipeline_name": pipeline_name,
                        "blocked_engine": engine_name
                    }
                )
                raise AppealIntegrityError(
                    message=error_msg,
                    pipeline_name=pipeline_name,
                    blocked_engine=engine_name,
                    trace_id=trace_id
                )
    
    def _validate_reporting_pipeline_integrity(
        self,
        pipeline_name: str,
        engine_sequence: list[str],
        trace_id: str
    ) -> None:
        """Validate that reporting pipeline contains no AI engines.
        
        CRITICAL: This is a HARD FAIL check. If any AI engine is found
        in a reporting pipeline, the entire pipeline is rejected.
        
        Reporting pipelines are READ-ONLY and must not trigger any
        AI processing or result recalculation.
        
        Args:
            pipeline_name: Name of the pipeline being executed
            engine_sequence: List of engine names in the pipeline
            trace_id: Request trace ID for logging
            
        Raises:
            ReportingIntegrityError: If AI engine is found in pipeline
        """
        for engine_name in engine_sequence:
            if engine_name in BLOCKED_ENGINES_DURING_REPORTING:
                error_msg = (
                    f"REPORTING INTEGRITY VIOLATION: Engine '{engine_name}' "
                    f"cannot execute during reporting pipeline. "
                    f"Reporting is READ-ONLY - no AI re-execution or recalculation allowed."
                )
                logger.error(
                    error_msg,
                    extra={
                        "trace_id": trace_id,
                        "pipeline_name": pipeline_name,
                        "blocked_engine": engine_name
                    }
                )
                raise ReportingIntegrityError(
                    message=error_msg,
                    pipeline_name=pipeline_name,
                    blocked_engine=engine_name,
                    trace_id=trace_id
                )


# Global orchestrator instance
orchestrator = Orchestrator(engine_registry)

