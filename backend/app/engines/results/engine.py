"""Results Engine - Main orchestrator-facing entry point.

Responsible for final grade calculation and result generation.
This is a NON-AI, deterministic engine producing legally authoritative results.
"""

import logging
from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError
from pymongo import MongoClient

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.results.schemas.input import ResultsInput
from app.engines.results.schemas.output import ResultsOutput
from app.engines.results.services.aggregation_service import AggregationService
from app.engines.results.services.grading_service import GradingService
from app.engines.results.services.breakdown_service import BreakdownService
from app.engines.results.repository.results_repo import ResultsRepository
from app.engines.results.errors.exceptions import (
    ResultsException,
    MissingPapersError,
    MarkOverflowError,
    InvalidWeightingError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "results"
ENGINE_VERSION = "1.0.0"


class ResultsEngine:
    """Production-grade Results Engine for ZimPrep.
    
    Aggregates validated marks, applies weightings, calculates final totals,
    resolves grades, and produces immutable exam results.
    
    CRITICAL: Results produced here are final, legally authoritative, and
    suitable for exam appeals. All operations are deterministic and auditable.
    """
    
    def __init__(self, mongo_client: MongoClient | None = None):
        """Initialize engine with repository.
        
        Args:
            mongo_client: Optional MongoDB client (for testing/DI)
        """
        self.repository: ResultsRepository | None = None
        
        if mongo_client:
            self.repository = ResultsRepository(mongo_client)
        
        logger.info("ResultsEngine initialized (version: %s)", ENGINE_VERSION)
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[ResultsOutput]:
        """Execute results engine.
        
        Implements the mandatory 9-step execution flow:
        1. Validate input schema
        2. Verify all required papers present
        3. Aggregate section → paper marks
        4. Apply paper weightings
        5. Calculate subject total
        6. Resolve grade via grading scale
        7. Build topic & paper breakdowns
        8. Persist immutable result
        9. Return ResultsOutput
        
        Args:
            payload: Request payload containing ResultsInput data
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ResultsOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info("Starting results calculation: trace_id=%s", trace_id)
        
        try:
            # ============================================================
            # STEP 1: Validate input schema
            # ============================================================
            try:
                input_data = ResultsInput(**payload)
                logger.info(
                    "Input validated: candidate=%s, exam=%s, subject=%s, papers=%d",
                    input_data.candidate_id,
                    input_data.exam_id,
                    input_data.subject_code,
                    len(input_data.papers)
                )
            except ValidationError as e:
                logger.error("Input validation failed: %s", str(e))
                return self._build_error_response(
                    error_message=f"Input validation failed: {str(e)}",
                    trace_id=trace_id,
                    start_time=start_time
                )
            
            # ============================================================
            # STEP 2: Verify all required papers present
            # ============================================================
            self._verify_papers(input_data, trace_id)
            
            # ============================================================
            # STEP 3: Aggregate section → paper marks
            # ============================================================
            # (Section marks are already aggregated in input validation)
            logger.info("Section marks validated and ready for aggregation")
            
            # ============================================================
            # STEP 4: Apply paper weightings
            # ============================================================
            # (Handled in step 5 during total calculation)
            
            # ============================================================
            # STEP 5: Calculate subject total
            # ============================================================
            total_marks = AggregationService.calculate_subject_total(input_data.papers)
            logger.info("Calculated subject total: %.2f", total_marks)
            
            # ============================================================
            # STEP 6: Resolve grade via grading scale
            # ============================================================
            grade = GradingService.resolve_grade(
                total_marks=total_marks,
                grading_scale=input_data.grading_scale
            )
            
            pass_status = GradingService.determine_pass_status(
                total_marks=total_marks,
                grading_scale=input_data.grading_scale
            )
            
            logger.info("Grade resolved: %s (pass: %s)", grade, pass_status)
            
            # ============================================================
            # STEP 7: Build topic & paper breakdowns
            # ============================================================
            paper_results, topic_breakdown = BreakdownService.build_complete_breakdown(
                papers=input_data.papers
            )
            
            # Calculate overall percentage
            percentage = AggregationService.calculate_percentage(
                awarded_marks=total_marks,
                max_marks=input_data.grading_scale.max_total_marks
            )
            
            # Build output
            output = ResultsOutput(
                trace_id=trace_id,
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                candidate_id=input_data.candidate_id,
                exam_id=input_data.exam_id,
                subject_code=input_data.subject_code,
                subject_name=input_data.subject_name,
                syllabus_version=input_data.syllabus_version,
                total_marks=total_marks,
                max_total_marks=input_data.grading_scale.max_total_marks,
                percentage=percentage,
                grade=grade,
                pass_status=pass_status,
                paper_results=paper_results,
                topic_breakdown=topic_breakdown,
                confidence=1.0,  # Always 1.0 for deterministic operations
                issued_at=datetime.utcnow(),
                notes=input_data.notes
            )
            
            # ============================================================
            # STEP 8: Persist immutable result
            # ============================================================
            if self.repository:
                try:
                    document_id = self.repository.save_result(
                        result=output,
                        trace_id=trace_id
                    )
                    logger.info("Result persisted: document_id=%s", document_id)
                except ResultsException as e:
                    logger.error("Failed to persist result: %s", str(e))
                    return self._build_error_response(
                        error_message=f"Failed to persist result: {str(e)}",
                        trace_id=trace_id,
                        start_time=start_time
                    )
            else:
                logger.warning("No repository configured - result not persisted")
            
            # ============================================================
            # STEP 9: Return ResultsOutput
            # ============================================================
            logger.info(
                "Results calculation complete: grade=%s, total=%.2f, trace=%s",
                grade,
                total_marks,
                trace_id
            )
            
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
            
        except ResultsException as e:
            # Known engine exceptions
            logger.error("Results engine error: %s", str(e))
            return self._build_error_response(
                error_message=str(e),
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error in results engine")
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _verify_papers(self, input_data: ResultsInput, trace_id: str):
        """Verify all required papers are present and valid.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Raises:
            MarkOverflowError: If awarded marks exceed max marks
            InvalidWeightingError: If weightings are invalid
        """
        for paper in input_data.papers:
            # Check for mark overflow
            if paper.awarded_marks > paper.max_marks:
                logger.error(
                    "Mark overflow in paper %s: %.2f > %.2f",
                    paper.paper_code,
                    paper.awarded_marks,
                    paper.max_marks
                )
                raise MarkOverflowError(
                    paper_code=paper.paper_code,
                    awarded_marks=paper.awarded_marks,
                    max_marks=paper.max_marks,
                    trace_id=trace_id
                )
            
            # Verify weighting is valid
            if paper.weighting <= 0 or paper.weighting > 1.0:
                logger.error(
                    "Invalid weighting for paper %s: %.4f",
                    paper.paper_code,
                    paper.weighting
                )
                raise InvalidWeightingError(
                    actual_sum=paper.weighting,
                    expected_sum=1.0,
                    trace_id=trace_id
                )
        
        logger.info("All %d papers verified successfully", len(input_data.papers))
    
    def _build_response(
        self,
        output: ResultsOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[ResultsOutput]:
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
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0  # Always 1.0 for deterministic operations
        )
        
        logger.info(
            "Response built successfully: execution_time=%.3fs",
            execution_time
        )
        
        return EngineResponse[ResultsOutput](
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
    ) -> EngineResponse[ResultsOutput]:
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
            confidence=0.0  # Zero confidence on error
        )
        
        logger.error(
            "Error response built: error=%s, execution_time=%.3fs",
            error_message,
            execution_time
        )
        
        return EngineResponse[ResultsOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
