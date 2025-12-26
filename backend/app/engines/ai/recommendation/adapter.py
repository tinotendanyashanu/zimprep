"""Backend adapter for Recommendation Engine.

Integrates the recommendation engine with the ZimPrep backend orchestrator.
This adapter translates between the backend's EngineResponse contract and
the recommendation engine's native interfaces.
"""

import logging
import os
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.recommendation.engine import RecommendationEngine as CoreRecommendationEngine
from app.engines.ai.recommendation.schemas.input import RecommendationInput
from app.engines.ai.recommendation.schemas.output import RecommendationOutput
from app.engines.ai.recommendation.schemas.errors import RecommendationError, RecommendationErrorCode

logger = logging.getLogger(__name__)

ENGINE_NAME = "recommendation"
ENGINE_VERSION = "1.0.0"


class RecommendationEngineAdapter:
    """
    Backend adapter for Recommendation Engine.
    
    Adapts the core recommendation engine to work with the ZimPrep backend
    orchestrator's EngineResponse contract.
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        model_name: str = None,
        min_confidence_threshold: float = None,
    ):
        """
        Initialize recommendation engine adapter.
        
        Args:
            llm_client: LLM client (if None, will be created on first run())
            model_name: Model name (if None, will use env default)
            min_confidence_threshold: Confidence threshold (if None, will use env default)
        """
        
        # Store configuration
        self.llm_client = llm_client
        self.model_name = model_name or os.getenv("RECOMMENDATION_MODEL", "gpt-4")
        self.min_confidence_threshold = float(
            min_confidence_threshold or os.getenv("RECOMMENDATION_MIN_CONFIDENCE", "0.6")
        )
        self.temperature = float(os.getenv("RECOMMENDATION_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("RECOMMENDATION_MAX_TOKENS", "2000"))
        self.timeout = int(os.getenv("RECOMMENDATION_TIMEOUT", "30"))
        
        # Lazy initialization - core engine created on first run()
        self.core_engine = None
        
        logger.info(
            f"Recommendation Engine Adapter initialized "
            f"(model: {self.model_name}, confidence_threshold: {self.min_confidence_threshold})"
        )
    
    def _ensure_engine(self) -> None:
        """Ensure core engine is initialized (lazy initialization)."""
        if self.core_engine is None:
            if self.llm_client is None:
                self.llm_client = self._create_llm_client()
            
            self.core_engine = CoreRecommendationEngine(
                llm_client=self.llm_client,
                model_name=self.model_name,
                temperature=self.temperature,
                min_confidence_threshold=self.min_confidence_threshold,
                max_tokens=self.max_tokens,
                timeout_seconds=self.timeout,
            )
    
    def _create_llm_client(self) -> Any:
        """
        Create LLM client from environment configuration.
        
        Returns:
            LLM client instance
        """
        from app.config.settings import settings
        
        # Check for OpenAI
        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            try:
                import openai
                return openai.Client(api_key=openai_key)
            except ImportError:
                logger.error("openai package not installed")
                raise RuntimeError("openai package required but not installed")
        
        # Check for Anthropic (optional)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")  # Not in settings yet
        if anthropic_key:
            try:
                import anthropic
                return anthropic.Client(api_key=anthropic_key)
            except ImportError:
                logger.error("anthropic package not installed")
                raise RuntimeError("anthropic package required but not installed")
        
        # No API key found
        logger.error("No LLM API key found in environment")
        raise RuntimeError(
            "LLM API key required. Set OPENAI_API_KEY or ANTHROPIC_API_KEY"
        )
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[RecommendationOutput]:
        """
        Execute recommendation engine (backend interface).
        
        This method adapts the core engine to the backend's EngineResponse contract.
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with RecommendationOutput
        """
        
        # Ensure core engine is initialized (lazy initialization)
        self._ensure_engine()
        
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Parse and validate input
            input_data = RecommendationInput(**payload)
            
            # Override trace_id from context
            input_data.trace_id = trace_id
            
            logger.info(
                f"Recommendation Engine execution started",
                extra={
                    "trace_id": trace_id,
                    "student_id": input_data.student_id,
                    "subject": input_data.subject,
                }
            )
            
            # Execute core engine
            output = await self.core_engine.execute(input_data)
            
            # Build successful response
            return self._build_response(output, trace_id, start_time)
        
        except ValidationError as e:
            logger.error(
                f"Input validation failed",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Invalid input: {str(e)}",
                trace_id=trace_id,
                start_time=start_time,
                confidence=0.0
            )
        
        except RecommendationError as e:
            logger.error(
                f"Recommendation engine error: {e.error_code}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"{e.error_code}: {e.message}",
                trace_id=trace_id,
                start_time=start_time,
                confidence=0.0
            )
        
        except Exception as e:
            logger.exception(
                f"Unexpected error in recommendation engine",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time,
                confidence=0.0
            )
    
    def _build_response(
        self,
        output: RecommendationOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[RecommendationOutput]:
        """
        Build successful EngineResponse.
        
        Args:
            output: Recommendation engine output
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
            confidence=output.confidence_score,
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            f"Recommendation Engine execution completed",
            extra={
                "trace_id": trace_id,
                "confidence": output.confidence_score,
                "duration_ms": duration_ms,
                "diagnoses": len(output.performance_diagnosis),
                "recommendations": len(output.study_recommendations),
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
        trace_id: str,
        start_time: datetime,
        confidence: float = 0.0
    ) -> EngineResponse[RecommendationOutput]:
        """
        Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            confidence: Confidence score (default 0.0 for errors)
            
        Returns:
            EngineResponse with error
        """
        
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=confidence,
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.warning(
            f"Recommendation Engine execution failed",
            extra={
                "trace_id": trace_id,
                "duration_ms": duration_ms,
                "error": error_message,
            }
        )
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )


# Singleton instance for FastAPI dependency injection
_recommendation_engine_instance = None


def get_recommendation_engine() -> RecommendationEngineAdapter:
    """
    Get or create recommendation engine singleton instance.
    
    This is used for FastAPI dependency injection.
    
    Returns:
        RecommendationEngineAdapter instance
    """
    
    global _recommendation_engine_instance
    
    if _recommendation_engine_instance is None:
        _recommendation_engine_instance = RecommendationEngineAdapter()
    
    return _recommendation_engine_instance
