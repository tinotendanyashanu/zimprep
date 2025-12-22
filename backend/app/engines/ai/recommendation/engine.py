"""Main Recommendation Engine.

This is Engine #10 in the ZimPrep architecture.
It generates personalized, syllabus-aligned study recommendations.

CRITICAL RULES:
- Runs ONLY after Results Engine
- Uses validated, immutable data
- Produces advisory output only
- Is auditable and explainable
- Does NOT modify scores or grades
"""

import logging
from typing import Optional, Any
from datetime import datetime

from .schemas.input import RecommendationInput
from .schemas.output import RecommendationOutput
from .schemas.errors import RecommendationError, RecommendationErrorCode
from .services.llm_service import LLMReasoningService
from .services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    ZimPrep Recommendation Engine (AI).
    
    Generates personalized, evidence-based study recommendations
    after final exam results have been validated.
    
    This engine:
    1. Validates input data
    2. Generates recommendations via LLM
    3. Validates recommendation quality
    4. Returns structured recommendations
    
    It does NOT:
    - Re-mark answers
    - Alter scores
    - Invent syllabus content
    - Override official results
    """
    
    ENGINE_NAME = "recommendation"
    ENGINE_VERSION = "1.0.0"
    
    def __init__(
        self,
        llm_client: Any,
        model_name: str = "gpt-4",
        temperature: float = 0.3,
        min_confidence_threshold: float = 0.6,
        max_tokens: int = 2000,
        timeout_seconds: int = 30,
    ):
        """
        Initialize Recommendation Engine.
        
        Args:
            llm_client: LLM client instance
            model_name: Model to use for recommendations
            temperature: Temperature for generation (keep low)
            min_confidence_threshold: Minimum acceptable confidence
            max_tokens: Maximum tokens to generate
            timeout_seconds: LLM request timeout
        """
        
        self.llm_service = LLMReasoningService(
            llm_client=llm_client,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )
        
        self.validation_service = ValidationService(
            min_confidence_threshold=min_confidence_threshold,
            require_weak_topics=True,
        )
        
        logger.info(
            f"Recommendation Engine initialized "
            f"(model: {model_name}, confidence_threshold: {min_confidence_threshold})"
        )
    
    async def execute(self, input_data: RecommendationInput) -> RecommendationOutput:
        """
        Execute recommendation engine.
        
        MANDATORY 7-STEP FLOW:
        1. Log entry
        2. Validate input
        3. Generate recommendations via LLM
        4. Validate output quality
        5. Log success
        6. Return recommendations
        7. Handle errors (if any)
        
        Args:
            input_data: Validated input from orchestrator
            
        Returns:
            RecommendationOutput with all recommendations
            
        Raises:
            RecommendationError: If any step fails
        """
        
        trace_id = input_data.trace_id
        
        try:
            # STEP 1: Log entry
            logger.info(
                f"[{trace_id}] Recommendation Engine STARTED "
                f"(student: {input_data.student_id}, subject: {input_data.subject})"
            )
            
            start_time = datetime.utcnow()
            
            # STEP 2: Validate input
            logger.info(f"[{trace_id}] Step 2/7: Validating input")
            self.validation_service.validate_input(input_data)
            
            # STEP 3: Generate recommendations via LLM
            logger.info(f"[{trace_id}] Step 3/7: Generating recommendations via LLM")
            recommendations = await self.llm_service.generate_recommendations(input_data)
            
            # STEP 4: Validate output quality
            logger.info(f"[{trace_id}] Step 4/7: Validating output quality")
            self.validation_service.validate_output(recommendations)
            
            # STEP 5: Log success
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            logger.info(
                f"[{trace_id}] Recommendation Engine COMPLETED "
                f"(duration: {duration_ms:.0f}ms, "
                f"confidence: {recommendations.confidence_score:.2f}, "
                f"diagnoses: {len(recommendations.performance_diagnosis)}, "
                f"recommendations: {len(recommendations.study_recommendations)})"
            )
            
            # STEP 6: Return recommendations
            return recommendations
            
        except RecommendationError as e:
            # STEP 7: Handle errors
            logger.error(
                f"[{trace_id}] Recommendation Engine FAILED "
                f"(error: {e.error_code}, message: {e.message})"
            )
            raise
        
        except Exception as e:
            # Unexpected error
            logger.error(f"[{trace_id}] Unexpected error: {str(e)}", exc_info=True)
            raise RecommendationError(
                error_code=RecommendationErrorCode.INTERNAL_ERROR,
                message="Internal engine error",
                trace_id=trace_id,
                recoverable=False,
                details=str(e)
            )
    
    def get_engine_info(self) -> dict:
        """Get engine metadata."""
        return {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "model": self.llm_service.model_name,
            "min_confidence_threshold": self.validation_service.min_confidence_threshold,
        }


# Convenience function for direct usage
async def generate_recommendations(
    input_data: RecommendationInput,
    llm_client: Any,
    model_name: str = "gpt-4",
    min_confidence_threshold: float = 0.6,
) -> RecommendationOutput:
    """
    Convenience function to generate recommendations.
    
    Args:
        input_data: Input data
        llm_client: LLM client
        model_name: Model to use
        min_confidence_threshold: Minimum confidence threshold
        
    Returns:
        RecommendationOutput
    """
    
    engine = RecommendationEngine(
        llm_client=llm_client,
        model_name=model_name,
        min_confidence_threshold=min_confidence_threshold,
    )
    
    return await engine.execute(input_data)
