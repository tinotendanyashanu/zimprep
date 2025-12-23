"""Validation & Consistency Engine.

Main orchestrator-facing entry point for AI governance.

CRITICAL RULES:
- This engine does NOT reason
- This engine does NOT score
- This engine does NOT infer
- This engine does NOT generate feedback
- This engine does NOT call other engines
- This engine does NOT access databases

It ONLY validates AI outputs and enforces hard constraints.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.validation_consistency.schemas.input import ValidationInput
from app.engines.ai.validation_consistency.schemas.output import ValidationOutput
from app.engines.ai.validation_consistency.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

ENGINE_NAME = "validation_consistency"
ENGINE_VERSION = "1.0.0"


class ValidationConsistencyEngine:
    """Production-grade Validation & Consistency Engine for ZimPrep.
    
    This engine has LEGAL VETO POWER. If it returns is_valid = false,
    the orchestrator MUST halt the pipeline.
    
    This engine ensures AI marking is:
    - Within legal bounds
    - Rubric-compliant
    - Internally consistent
    - Evidence-backed
    
    AUTHORITY: This engine can BLOCK invalid AI outputs from reaching Results Engine.
    """
    
    def __init__(self):
        """Initialize engine."""
        # Store engine metadata as instance attributes for explicit output preservation
        self.engine_name = ENGINE_NAME
        self.engine_version = ENGINE_VERSION
        logger.info("ValidationConsistencyEngine initialized (version: %s)", ENGINE_VERSION)
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[ValidationOutput]:
        """Execute validation & consistency engine.
        
        Implements the mandatory 8-step execution flow:
        1. Validate input schema
        2. Execute mark bounds validation
        3. Execute rubric compliance validation
        4. Execute internal consistency validation
        5. Execute evidence presence validation
        6. Aggregate violations and determine validity
        7. Set is_valid flag based on FATAL violations
        8. Return immutable output
        
        Args:
            payload: Request payload containing ValidationInput data
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ValidationOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info("Starting validation: trace_id=%s", trace_id)
        
        try:
            # ============================================================
            # STEP 1: Validate input schema
            # ============================================================
            try:
                input_data = ValidationInput(**payload)
                logger.info(
                    "Input validated: subject=%s, paper=%s, awarded=%.2f, max=%d",
                    input_data.subject,
                    input_data.paper,
                    input_data.awarded_marks,
                    input_data.max_marks
                )
            except ValidationError as e:
                logger.error("Input validation failed: %s", str(e))
                return self._build_error_response(
                    error_message=f"Input validation failed: {str(e)}",
                    trace_id=trace_id,
                    start_time=start_time
                )
            
            # ============================================================
            # STEPS 2-5: Execute all validation rules
            # ============================================================
            violations, is_valid = ValidationService.validate_marking_output(input_data)
            
            # ============================================================
            # STEP 6-7: Aggregate violations and determine validity
            # ============================================================
            # (Already done by ValidationService)
            
            if not is_valid:
                logger.error(
                    "[%s] VALIDATION FAILED: %d violations, marking is INVALID",
                    trace_id,
                    len(violations)
                )
            else:
                logger.info(
                    "[%s] Validation passed: %d violations (all non-fatal)",
                    trace_id,
                    len(violations)
                )
            
            # ============================================================
            # STEP 8: Return immutable output
            # ============================================================
            output = ValidationOutput(
                trace_id=trace_id,
                final_awarded_marks=input_data.awarded_marks,  # Pass through if valid
                validated_feedback=input_data.feedback,  # Pass through
                confidence=input_data.confidence,  # Pass through
                violations=violations,
                is_valid=is_valid,
                engine_name=self.engine_name,  # Explicitly preserved for audit reconstruction
                engine_version=self.engine_version  # Explicit version for appeals
            )
            
            logger.info(
                "Validation complete: is_valid=%s, violations=%d, trace=%s",
                is_valid,
                len(violations),
                trace_id
            )
            
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
            
        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error in validation engine")
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _build_response(
        self,
        output: ValidationOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[ValidationOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse
        """
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            timestamp=datetime.utcnow(),
            confidence=1.0  # Always 1.0 for deterministic operations
        )
        
        logger.info(
            "Response built successfully: execution_time=%.3fs",
            execution_time
        )
        
        return EngineResponse[ValidationOutput](
            success=True,
            data=output,
            error=None,
            trace=trace
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[ValidationOutput]:
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
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            timestamp=datetime.utcnow(),
            confidence=0.0  # Zero confidence on error
        )
        
        logger.error(
            "Error response built: error=%s, execution_time=%.3fs",
            error_message,
            execution_time
        )
        
        return EngineResponse[ValidationOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
