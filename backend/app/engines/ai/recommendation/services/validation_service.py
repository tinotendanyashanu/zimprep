"""Validation service for Recommendation Engine.

Validates input data and ensures recommendations meet quality standards.
"""

import logging
from typing import List, Optional

from ..schemas.input import RecommendationInput
from ..schemas.output import RecommendationOutput
from ..schemas.errors import RecommendationError, RecommendationErrorCode

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for validating input data and recommendation quality.
    
    This service ensures:
    - Input data is complete and structurally valid
    - Sufficient evidence exists for recommendations
    - Recommendations meet minimum confidence threshold
    """
    
    def __init__(
        self,
        min_confidence_threshold: float = 0.6,
        require_weak_topics: bool = True,
    ):
        """
        Initialize validation service.
        
        Args:
            min_confidence_threshold: Minimum acceptable confidence score
            require_weak_topics: Whether to require weak topics for recommendations
        """
        self.min_confidence_threshold = min_confidence_threshold
        self.require_weak_topics = require_weak_topics
    
    def validate_input(self, input_data: RecommendationInput) -> None:
        """
        Validate input data.
        
        Args:
            input_data: Input to validate
            
        Raises:
            RecommendationError: If input is invalid or insufficient
        """
        
        trace_id = input_data.trace_id
        
        logger.info(f"[{trace_id}] Validating input data")
        
        # Check final results exist
        if not input_data.final_results:
            raise RecommendationError(
                error_code=RecommendationErrorCode.MISSING_RESULTS,
                message="Final results are required",
                trace_id=trace_id,
                recoverable=False,
                details="Cannot generate recommendations without final results"
            )
        
        # Check marking summary exists
        if not input_data.validated_marking_summary:
            raise RecommendationError(
                error_code=RecommendationErrorCode.MISSING_MARKING_SUMMARY,
                message="Validated marking summary is required",
                trace_id=trace_id,
                recoverable=False,
                details="Cannot generate recommendations without marking evidence"
            )
        
        # Check for sufficient evidence
        marking_summary = input_data.validated_marking_summary
        
        has_weak_topics = len(marking_summary.weak_topics) > 0
        has_error_categories = len(marking_summary.common_error_categories) > 0
        has_marked_questions = len(marking_summary.marked_questions) > 0
        
        if self.require_weak_topics and not has_weak_topics:
            # This might happen if student scored very high
            logger.warning(
                f"[{trace_id}] No weak topics identified. "
                f"Student may have performed very well."
            )
        
        if not (has_weak_topics or has_error_categories or has_marked_questions):
            raise RecommendationError(
                error_code=RecommendationErrorCode.INSUFFICIENT_EVIDENCE,
                message="Insufficient marking evidence for recommendations",
                trace_id=trace_id,
                recoverable=False,
                details="Need at least weak topics, error categories, or marked questions"
            )
        
        logger.info(f"[{trace_id}] Input validation passed")
    
    def validate_output(self, output: RecommendationOutput) -> None:
        """
        Validate recommendation output quality.
        
        Args:
            output: Output to validate
            
        Raises:
            RecommendationError: If output quality is insufficient
        """
        
        trace_id = output.trace_id
        
        logger.info(f"[{trace_id}] Validating output quality")
        
        # Check confidence threshold
        if output.confidence_score < self.min_confidence_threshold:
            logger.warning(
                f"[{trace_id}] Confidence too low: {output.confidence_score:.2f} "
                f"< {self.min_confidence_threshold:.2f}"
            )
            raise RecommendationError(
                error_code=RecommendationErrorCode.CONFIDENCE_TOO_LOW,
                message="Recommendation confidence below acceptable threshold",
                trace_id=trace_id,
                recoverable=False,
                details=f"Confidence: {output.confidence_score:.2f}, Threshold: {self.min_confidence_threshold:.2f}"
            )
        
        # Check minimum recommendations
        if len(output.performance_diagnosis) == 0:
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_INVALID_RESPONSE,
                message="No performance diagnosis provided",
                trace_id=trace_id,
                recoverable=False,
                details="At least one diagnosis item is required"
            )
        
        if len(output.study_recommendations) == 0:
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_INVALID_RESPONSE,
                message="No study recommendations provided",
                trace_id=trace_id,
                recoverable=False,
                details="At least one recommendation is required"
            )
        
        if len(output.practice_suggestions) == 0:
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_INVALID_RESPONSE,
                message="No practice suggestions provided",
                trace_id=trace_id,
                recoverable=False,
                details="At least one practice suggestion is required"
            )
        
        logger.info(f"[{trace_id}] Output validation passed")
