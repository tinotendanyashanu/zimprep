"""LLM Reasoning Service for Recommendation Engine.

This service handles all LLM interactions for generating recommendations.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..schemas.input import RecommendationInput
from ..schemas.output import RecommendationOutput
from ..schemas.errors import RecommendationError, RecommendationErrorCode
from ..prompts.recommendation_prompt import SYSTEM_ROLE_PROMPT, format_prompt

logger = logging.getLogger(__name__)


class LLMReasoningService:
    """
    Service for LLM-based recommendation generation.
    
    This service:
    - Assembles prompts from input data
    - Calls LLM API (OpenAI, Anthropic, etc.)
    - Parses and validates LLM responses
    - Calculates confidence scores
    """
    
    def __init__(
        self,
        llm_client: Any,  # Generic LLM client (OpenAI, Anthropic, etc.)
        model_name: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        timeout_seconds: int = 30,
    ):
        """
        Initialize LLM service.
        
        Args:
            llm_client: LLM client instance
            model_name: Model to use
            temperature: Temperature for generation (keep low for consistency)
            max_tokens: Maximum tokens to generate
            timeout_seconds: Request timeout
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout_seconds
    
    async def generate_recommendations(
        self,
        input_data: RecommendationInput
    ) -> RecommendationOutput:
        """
        Generate recommendations using LLM.
        
        Args:
            input_data: Validated input data
            
        Returns:
            RecommendationOutput with all recommendations
            
        Raises:
            RecommendationError: If LLM call fails or response is invalid
        """
        
        logger.info(f"[{input_data.trace_id}] Generating recommendations via LLM")
        
        try:
            # 1. Assemble prompt
            user_prompt = self._assemble_prompt(input_data)
            
            # 2. Call LLM
            llm_response = await self._call_llm(
                system_prompt=SYSTEM_ROLE_PROMPT,
                user_prompt=user_prompt,
                trace_id=input_data.trace_id
            )
            
            # 3. Parse and validate response
            recommendations = self._parse_response(llm_response, input_data.trace_id)
            
            # 4. Build output
            output = self._build_output(recommendations, input_data)
            
            logger.info(
                f"[{input_data.trace_id}] Recommendations generated successfully "
                f"(confidence: {output.confidence_score:.2f})"
            )
            
            return output
            
        except RecommendationError:
            raise
        except Exception as e:
            logger.error(f"[{input_data.trace_id}] Unexpected error: {str(e)}")
            raise RecommendationError(
                error_code=RecommendationErrorCode.INTERNAL_ERROR,
                message="Failed to generate recommendations",
                trace_id=input_data.trace_id,
                recoverable=False,
                details=str(e)
            )
    
    def _assemble_prompt(self, input_data: RecommendationInput) -> str:
        """Assemble prompt from input data."""
        
        return format_prompt(
            trace_id=input_data.trace_id,
            student_id=input_data.student_id,
            subject=input_data.subject,
            syllabus_version=input_data.syllabus_version,
            final_results=input_data.final_results.dict(),
            validated_marking_summary=input_data.validated_marking_summary.dict(),
            historical_performance_summary=(
                input_data.historical_performance_summary.dict()
                if input_data.historical_performance_summary
                else None
            ),
            constraints=input_data.constraints.dict(),
        )
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        trace_id: str
    ) -> str:
        """
        Call LLM API.
        
        Args:
            system_prompt: System role prompt
            user_prompt: User prompt with data
            trace_id: Trace ID for logging
            
        Returns:
            LLM response text
            
        Raises:
            RecommendationError: If LLM call fails
        """
        
        try:
            # Example for OpenAI-style API
            # Adapt this for your specific LLM client
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except TimeoutError:
            logger.error(f"[{trace_id}] LLM request timeout")
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_TIMEOUT,
                message="LLM request timed out",
                trace_id=trace_id,
                recoverable=True,
                details=f"Timeout after {self.timeout}s"
            )
        
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg:
                logger.warning(f"[{trace_id}] LLM rate limited")
                raise RecommendationError(
                    error_code=RecommendationErrorCode.LLM_RATE_LIMITED,
                    message="LLM service rate limited",
                    trace_id=trace_id,
                    recoverable=True,
                    details=str(e)
                )
            
            logger.error(f"[{trace_id}] LLM unavailable: {str(e)}")
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_UNAVAILABLE,
                message="LLM service is currently unavailable",
                trace_id=trace_id,
                recoverable=True,
                details=str(e)
            )
    
    def _parse_response(self, llm_response: str, trace_id: str) -> Dict[str, Any]:
        """
        Parse and validate LLM response.
        
        Args:
            llm_response: Raw LLM response
            trace_id: Trace ID for logging
            
        Returns:
            Parsed recommendations dict
            
        Raises:
            RecommendationError: If response is invalid
        """
        
        try:
            # Extract JSON from response (LLM might add markdown code blocks)
            json_str = llm_response.strip()
            
            if json_str.startswith("```json"):
                json_str = json_str[7:]  # Remove ```json
            if json_str.startswith("```"):
                json_str = json_str[3:]  # Remove ```
            if json_str.endswith("```"):
                json_str = json_str[:-3]  # Remove trailing ```
            
            json_str = json_str.strip()
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                "performance_diagnosis",
                "study_recommendations",
                "practice_suggestions",
                "motivation",
                "confidence_score"
            ]
            
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Validate confidence score
            confidence = data.get("confidence_score", 0)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                raise ValueError("Invalid confidence_score")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"[{trace_id}] Invalid JSON response: {str(e)}")
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_INVALID_RESPONSE,
                message="LLM returned invalid JSON",
                trace_id=trace_id,
                recoverable=False,
                details=f"JSON parse error: {str(e)}"
            )
        
        except ValueError as e:
            logger.error(f"[{trace_id}] Invalid response structure: {str(e)}")
            raise RecommendationError(
                error_code=RecommendationErrorCode.LLM_INVALID_RESPONSE,
                message="LLM returned invalid response structure",
                trace_id=trace_id,
                recoverable=False,
                details=str(e)
            )
    
    def _build_output(
        self,
        recommendations: Dict[str, Any],
        input_data: RecommendationInput
    ) -> RecommendationOutput:
        """Build structured output from LLM recommendations."""
        
        return RecommendationOutput(
            trace_id=input_data.trace_id,
            engine_name="recommendation",
            engine_version="1.0.0",
            timestamp=datetime.utcnow(),
            performance_diagnosis=recommendations["performance_diagnosis"],
            study_recommendations=recommendations["study_recommendations"],
            practice_suggestions=recommendations["practice_suggestions"],
            study_plan=recommendations.get("study_plan"),
            motivation=recommendations["motivation"],
            confidence_score=recommendations["confidence_score"],
            notes=recommendations.get("notes")
        )
