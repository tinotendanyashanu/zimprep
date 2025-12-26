"""Reasoning & Marking Engine

Main orchestrator-facing entry point for AI-powered exam marking.
"""

import logging
from datetime import datetime
from typing import List

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.reasoning_marking.schemas import (
    ReasoningMarkingInput,
    ReasoningMarkingOutput,
    AwardedPoint,
    MissingPoint,
)
from app.engines.ai.reasoning_marking.services import (
    RubricMapperService,
    ReasoningService,
    FeedbackGenerator,
    ConfidenceCalculator,
)
from app.engines.ai.reasoning_marking.rules.marking_constraints import MarkingConstraints
from app.engines.ai.reasoning_marking.errors import (
    ReasoningMarkingException,
    EvidenceMissingError,
    EvidenceQualityError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "reasoning_marking"
ENGINE_VERSION = "1.0.0"


class ReasoningMarkingEngine:
    """Production-grade reasoning and marking engine for ZimPrep.
    
    Compares student answers to retrieved marking evidence and allocates marks
    strictly per official rubric. This engine produces SUGGESTIONS, not final marks.
    
    STRICT PROHIBITIONS:
    ✗ Retrieve data (that's Retrieval Engine's job)
    ✗ Invent rubric criteria
    ✗ Guess marks without evidence
    ✗ Exceed rubric limits
    ✗ Apply final grades (that's Validation Engine's job)
    ✗ Bypass validation
    ✗ Call other engines
    """
    
    def __init__(self):
        """Initialize engine (lazy initialization for AI service)."""
        self.reasoning_service = None  # Lazy init - created on first run()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    def _ensure_service(self):
        """Ensure reasoning service is initialized (lazy initialization).
        
        This defers OPENAI_API_KEY validation until the engine is actually used.
        """
        if self.reasoning_service is None:
            self.reasoning_service = ReasoningService()
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[ReasoningMarkingOutput]:
        """Execute reasoning and marking engine.
        
        Implements the mandatory 6-step execution flow:
        1. Evidence Validation
        2. Rubric Decomposition (non-AI)
        3. Constrained LLM Reasoning
        4. Deterministic Mark Allocation
        5. Examiner-Style Feedback
        6. Confidence Calculation
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ReasoningMarkingOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Reasoning & Marking Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            # STEP 1: Evidence Validation
            try:
                input_data = ReasoningMarkingInput(**payload)
            except ValidationError as e:
                logger.error(
                    "Input validation failed",
                    extra={"trace_id": trace_id, "errors": e.errors()}
                )
                return self._build_error_response(
                    error_message=f"Input validation failed: {str(e)}",
                    trace_id=trace_id,
                    start_time=start_time
                )
            
            # Validate evidence quality (warning, not failure)
            evidence_quality_warning = self._check_evidence_quality(
                input_data.retrieved_evidence,
                trace_id
            )
            
            # PHASE ZERO: Ensure service is initialized (lazy init)
            self._ensure_service()
            
            # STEP 2: Rubric Decomposition (NON-AI)
            rubric_map = RubricMapperService.decompose_rubric(
                input_data.official_rubric,
                trace_id
            )
            
            # Validate rubric integrity
            RubricMapperService.validate_rubric_integrity(
                input_data.official_rubric,
                input_data.max_marks,
                trace_id
            )
            
            # STEP 3: Constrained LLM Reasoning
            reasoning_result = self.reasoning_service.perform_reasoning(
                student_answer=input_data.raw_student_answer,
                rubric_points=input_data.official_rubric,
                retrieved_evidence=input_data.retrieved_evidence,
                answer_type=input_data.answer_type,
                subject=input_data.subject,
                question_id=input_data.question_id,
                trace_id=trace_id
            )
            
            awarded_points: List[AwardedPoint] = reasoning_result["awarded_points"]
            missing_points: List[MissingPoint] = reasoning_result["missing_points"]
            
            # STEP 4: Deterministic Mark Allocation (CODE-BASED)
            awarded_marks = self._calculate_total_marks(awarded_points)
            
            # STEP 5: Examiner-Style Feedback
            feedback = FeedbackGenerator.generate_feedback(
                awarded_points=awarded_points,
                missing_points=missing_points,
                awarded_marks=awarded_marks,
                max_marks=input_data.max_marks,
                answer_type=input_data.answer_type,
                subject=input_data.subject,
                trace_id=trace_id
            )
            
            # STEP 6: Confidence Calculation
            confidence = ConfidenceCalculator.calculate_confidence(
                rubric_points=input_data.official_rubric,
                awarded_points=awarded_points,
                retrieved_evidence=input_data.retrieved_evidence,
                answer_length=len(input_data.raw_student_answer),
                trace_id=trace_id
            )
            
            # Reduce confidence if evidence quality warning
            if evidence_quality_warning:
                confidence = min(confidence, 0.6)
                logger.warning(
                    "Confidence reduced due to evidence quality issues",
                    extra={"trace_id": trace_id, "adjusted_confidence": confidence}
                )
            
            # Build output
            output = ReasoningMarkingOutput(
                question_id=input_data.question_id,
                trace_id=trace_id,
                awarded_marks=awarded_marks,
                max_marks=input_data.max_marks,
                mark_breakdown=awarded_points,
                missing_points=missing_points,
                feedback=feedback,
                confidence=confidence,
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                answer_type=input_data.answer_type.value,
                evidence_count=len(input_data.retrieved_evidence)
            )
            
            # Validate output against constraints
            MarkingConstraints.validate_output(
                output,
                input_data.official_rubric,
                trace_id
            )
            
            # Return success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except ReasoningMarkingException as e:
            # Known engine errors
            logger.error(
                f"Engine error: {type(e).__name__}",
                extra={
                    "trace_id": trace_id,
                    "error_message": e.message,
                    "metadata": e.metadata
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=e.message,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            # Unexpected errors - fail explicitly
            logger.error(
                "Unexpected engine error",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _check_evidence_quality(
        self,
        evidence_items,
        trace_id: str
    ) -> bool:
        """Check evidence quality and log warnings.
        
        Returns:
            True if quality issues detected (warning only)
        """
        if not evidence_items:
            raise EvidenceMissingError(
                trace_id=trace_id,
                question_id="unknown"
            )
        
        # Check for low relevance scores
        avg_relevance = sum(e.relevance_score for e in evidence_items) / len(evidence_items)
        
        if avg_relevance < 0.5:
            logger.warning(
                "Low average evidence relevance",
                extra={
                    "trace_id": trace_id,
                    "avg_relevance": avg_relevance,
                    "evidence_count": len(evidence_items)
                }
            )
            return True
        
        # Check for insufficient diversity (all evidence too similar)
        if len(evidence_items) < 2:
            logger.warning(
                "Insufficient evidence diversity",
                extra={"trace_id": trace_id, "evidence_count": len(evidence_items)}
            )
            return True
        
        return False
    
    def _calculate_total_marks(self, awarded_points: List[AwardedPoint]) -> float:
        """Calculate total marks (deterministic, code-based).
        
        Args:
            awarded_points: List of awarded points
            
        Returns:
            Total marks
        """
        return sum(point.marks for point in awarded_points)
    
    def _build_response(
        self,
        output: ReasoningMarkingOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[ReasoningMarkingOutput]:
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
            confidence=output.confidence
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "Engine execution completed",
            extra={
                "trace_id": trace_id,
                "question_id": output.question_id,
                "awarded_marks": output.awarded_marks,
                "max_marks": output.max_marks,
                "confidence": output.confidence,
                "duration_ms": duration_ms
            }
        )
        
        return EngineResponse[ReasoningMarkingOutput](
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
    ) -> EngineResponse[ReasoningMarkingOutput]:
        """Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with error
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.warning(
            "Engine execution failed",
            extra={
                "trace_id": trace_id,
                "error": error_message,
                "duration_ms": duration_ms
            }
        )
        
        return EngineResponse[ReasoningMarkingOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
