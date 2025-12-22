"""Trace collector service for extracting engine execution traces.

Pure business logic - no I/O, no database access.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from app.engines.audit_compliance.schemas.input import EngineExecutionRecord
from app.engines.audit_compliance.errors import TraceExtractionError

logger = logging.getLogger(__name__)


class TraceCollectorService:
    """Service for extracting and validating engine execution traces.
    
    Processes the engine execution log from orchestrator input and
    prepares it for audit persistence.
    """
    
    def extract_engine_traces(
        self,
        engine_execution_log: List[EngineExecutionRecord],
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Extract engine traces from execution log.
        
        Args:
            engine_execution_log: List of engine execution records
            trace_id: Request trace ID
            
        Returns:
            List of trace dictionaries ready for persistence
            
        Raises:
            TraceExtractionError: Extraction failed
        """
        try:
            if not engine_execution_log:
                logger.warning(
                    f"[{trace_id}] Empty engine execution log - no traces to extract"
                )
                return []
            
            traces = []
            for record in engine_execution_log:
                trace = {
                    "engine_name": record.engine_name,
                    "engine_version": record.engine_version,
                    "execution_order": record.execution_order,
                    "started_at": record.started_at,
                    "completed_at": record.completed_at,
                    "duration_ms": (
                        record.completed_at - record.started_at
                    ).total_seconds() * 1000,
                    "success": record.success,
                    "confidence": record.confidence,
                    "input_hash": record.input_hash,
                    "output_hash": record.output_hash,
                    "error_message": record.error_message,
                }
                traces.append(trace)
            
            logger.info(
                f"[{trace_id}] Extracted {len(traces)} engine traces"
            )
            
            return traces
        
        except Exception as e:
            logger.error(
                f"[{trace_id}] Failed to extract engine traces: {e}",
                exc_info=True
            )
            raise TraceExtractionError(
                message=f"Failed to extract engine traces: {str(e)}",
                trace_id=trace_id,
                extraction_stage="trace_extraction"
            )
    
    def validate_trace_integrity(
        self,
        engine_execution_log: List[EngineExecutionRecord],
        trace_id: str
    ) -> bool:
        """Validate that execution log is complete and ordered.
        
        Args:
            engine_execution_log: List of engine execution records
            trace_id: Request trace ID
            
        Returns:
            True if valid
            
        Raises:
            TraceExtractionError: Validation failed
        """
        try:
            if not engine_execution_log:
                return True  # Empty log is valid (early termination)
            
            # Check execution order is sequential
            expected_order = 1
            for record in engine_execution_log:
                if record.execution_order != expected_order:
                    raise TraceExtractionError(
                        message=f"Engine execution order gap: expected {expected_order}, got {record.execution_order}",
                        trace_id=trace_id,
                        extraction_stage="order_validation"
                    )
                expected_order += 1
            
            # Check timestamps are chronological
            prev_completion: datetime = None
            for record in engine_execution_log:
                if record.started_at > record.completed_at:
                    raise TraceExtractionError(
                        message=f"Engine {record.engine_name}: start time after completion time",
                        trace_id=trace_id,
                        extraction_stage="timestamp_validation"
                    )
                
                if prev_completion and record.started_at < prev_completion:
                    logger.warning(
                        f"[{trace_id}] Overlapping execution detected for {record.engine_name}"
                    )
                
                prev_completion = record.completed_at
            
            logger.info(
                f"[{trace_id}] Trace integrity validated: {len(engine_execution_log)} records"
            )
            
            return True
        
        except TraceExtractionError:
            raise
        except Exception as e:
            logger.error(
                f"[{trace_id}] Trace validation failed: {e}",
                exc_info=True
            )
            raise TraceExtractionError(
                message=f"Trace validation failed: {str(e)}",
                trace_id=trace_id,
                extraction_stage="trace_validation"
            )
    
    def calculate_total_execution_time(
        self,
        engine_execution_log: List[EngineExecutionRecord],
        trace_id: str
    ) -> float:
        """Calculate total execution time across all engines.
        
        Args:
            engine_execution_log: List of engine execution records
            trace_id: Request trace ID
            
        Returns:
            Total execution time in milliseconds
        """
        if not engine_execution_log:
            return 0.0
        
        total_ms = 0.0
        for record in engine_execution_log:
            duration = (record.completed_at - record.started_at).total_seconds() * 1000
            total_ms += duration
        
        logger.debug(
            f"[{trace_id}] Total execution time: {total_ms:.2f}ms across {len(engine_execution_log)} engines"
        )
        
        return total_ms
    
    def get_orchestration_window(
        self,
        engine_execution_log: List[EngineExecutionRecord],
        trace_id: str
    ) -> tuple[datetime, datetime]:
        """Get start and end timestamps of orchestration.
        
        Args:
            engine_execution_log: List of engine execution records
            trace_id: Request trace ID
            
        Returns:
            Tuple of (started_at, completed_at)
            
        Raises:
            TraceExtractionError: No execution records found
        """
        if not engine_execution_log:
            raise TraceExtractionError(
                message="Cannot determine orchestration window: empty execution log",
                trace_id=trace_id,
                extraction_stage="orchestration_window"
            )
        
        started_at = min(record.started_at for record in engine_execution_log)
        completed_at = max(record.completed_at for record in engine_execution_log)
        
        return started_at, completed_at
