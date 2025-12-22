"""Reporting Engine Adapter for Orchestrator Integration.

This adapter wraps the ReportingAnalyticsEngine to conform to the
orchestrator's Engine contract and EngineResponse pattern.
"""

from typing import Any
import logging
from datetime import datetime

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.reporting_analytics.engine import ReportingAnalyticsEngine
from app.engines.reporting_analytics.schemas.input import (
    ReportingInput,
    UserRole,
    ReportingScope,
    ExportFormat
)
from app.engines.reporting_analytics.schemas.output import ReportingOutput
from app.engines.reporting_analytics.errors.exceptions import ReportingEngineError


logger = logging.getLogger(__name__)

ENGINE_NAME = "reporting"
ENGINE_VERSION = "1.0.0"


class ReportingEngineAdapter:
    """Adapter to integrate ReportingAnalyticsEngine with the orchestrator.
    
    This adapter:
    - Accepts orchestrator payload (dict) and ExecutionContext
    - Transforms payload into ReportingInput schema
    - Calls the underlying ReportingAnalyticsEngine
    - Returns EngineResponse[dict] for orchestrator compatibility
    """
    
    def __init__(self):
        """Initialize the adapter with the reporting engine."""
        self.engine = ReportingAnalyticsEngine()
        logger.info(f"{ENGINE_NAME} adapter initialized (version: {ENGINE_VERSION})")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[dict]:
        """Execute the reporting engine via orchestrator contract.
        
        Args:
            payload: Request payload containing reporting parameters
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with reporting output as dict
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(f"[{trace_id}] Reporting engine adapter started")
        
        try:
            # Transform orchestrator payload → ReportingInput
            reporting_input = self._build_reporting_input(payload, context)
            
            # Extract results data from payload (passed from results engine)
            results_data = payload.get("results_data")
            historical_data = payload.get("historical_data")
            
            # Execute reporting engine
            output: ReportingOutput = await self.engine.execute(
                input_data=reporting_input,
                results_data=results_data,
                historical_data=historical_data
            )
            
            # Build success response
            return self._build_success_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
            
        except ReportingEngineError as e:
            # Known reporting errors
            logger.error(
                f"[{trace_id}] Reporting engine error: {e.message}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=e.message,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            # Unexpected errors
            logger.exception(
                f"[{trace_id}] Unexpected error in reporting adapter",
                extra={"trace_id": trace_id}
            )
            return self._build_error_response(
                error_message=f"Unexpected reporting error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _build_reporting_input(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> ReportingInput:
        """Build ReportingInput from orchestrator payload.
        
        Args:
            payload: Request payload
            context: Execution context
            
        Returns:
            Validated ReportingInput
        """
        # Map report_type string to UserRole enum
        report_type = payload.get("report_type", "student")
        role_mapping = {
            "student": UserRole.STUDENT,
            "parent": UserRole.PARENT,
            "school": UserRole.SCHOOL_ADMIN
        }
        role = role_mapping.get(report_type, UserRole.STUDENT)
        
        # Map export_format string to ExportFormat enum
        export_format_str = payload.get("export_format", "json")
        format_mapping = {
            "json": ExportFormat.JSON,
            "csv": ExportFormat.CSV,
            "pdf": ExportFormat.PDF
        }
        export_format = format_mapping.get(export_format_str, ExportFormat.JSON)
        
        # Build ReportingInput
        return ReportingInput(
            trace_id=context.trace_id,
            user_id=context.user_id,
            role=role,
            exam_session_id=payload.get("exam_session_id", context.trace_id),
            subject_code=payload.get("subject_code", "MATH"),
            reporting_scope=ReportingScope.SINGLE_EXAM,  # Default scope
            export_format=export_format,
            feature_flags_snapshot=context.feature_flags_snapshot
        )
    
    def _build_success_response(
        self,
        output: ReportingOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[dict]:
        """Build successful EngineResponse.
        
        Args:
            output: Reporting output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with success
        """
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=output.confidence
        )
        
        # Convert ReportingOutput to dict for orchestrator
        output_dict = output.model_dump()
        
        logger.info(
            f"[{trace_id}] Reporting engine completed successfully",
            extra={
                "trace_id": trace_id,
                "execution_time": execution_time,
                "report_type": output.report_type.value
            }
        )
        
        return EngineResponse[dict](
            success=True,
            data=output_dict,
            error=None,
            trace=trace
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[dict]:
        """Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with error
        """
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0
        )
        
        logger.error(
            f"[{trace_id}] Reporting engine failed",
            extra={
                "trace_id": trace_id,
                "execution_time": execution_time,
                "error": error_message
            }
        )
        
        return EngineResponse[dict](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
