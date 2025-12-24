"""Reasoning Service - LLM-powered marking logic.

This service uses constrained LLM prompting to perform evidence-based marking.
"""

import os
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from openai import OpenAI

from app.engines.ai.reasoning_marking.schemas import (
    RubricPoint,
    RetrievedEvidence,
    AnswerType,
    AwardedPoint,
    MissingPoint,
)
from app.engines.ai.reasoning_marking.errors import (
    LLMServiceError,
    LLMOutputMalformedError,
)

logger = logging.getLogger(__name__)


class ReasoningService:
    """LLM-powered reasoning service for marking.
    
    STRICT CONSTRAINTS:
    - LLM may ONLY use provided evidence
    - LLM may ONLY award marks defined in rubric
    - Every awarded mark MUST cite evidence
    - No speculation or external knowledge
    """
    
    # Model configuration
    MODEL_ID = "gpt-4o-2024-08-06"  # Supports structured outputs
    TEMPERATURE = 0.0  # Deterministic
    MAX_TOKENS = 2000
    
    def __init__(self):
        """Initialize OpenAI client."""
        from app.config.settings import settings
        
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    def perform_reasoning(
        self,
        student_answer: str,
        rubric_points: List[RubricPoint],
        retrieved_evidence: List[RetrievedEvidence],
        answer_type: AnswerType,
        subject: str,
        question_id: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """Perform constrained LLM reasoning to allocate marks.
        
        Args:
            student_answer: Raw student answer text
            rubric_points: Official rubric points
            retrieved_evidence: Evidence from Retrieval Engine
            answer_type: Type of answer
            subject: Subject name
            question_id: Question ID
            trace_id: Trace ID
            
        Returns:
            Dict with 'awarded_points' and 'missing_points'
            
        Raises:
            LLMServiceError: If LLM API fails
            LLMOutputMalformedError: If LLM output is invalid
        """
        # Load appropriate prompt template
        prompt = self._build_prompt(
            student_answer,
            rubric_points,
            retrieved_evidence,
            answer_type,
            subject
        )
        
        # Call LLM with structured output (PHASE 6: with timeout)
        try:
            from app.core.utils.timeout import with_timeout_sync, AITimeoutError
            from app.config.settings import settings
            
            # Wrap OpenAI call with timeout protection
            def _make_openai_call():
                return self.client.chat.completions.create(
                    model=self.MODEL_ID,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a ZIMSEC examiner performing evidence-based marking."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                    response_format={"type": "json_object"}
                )
            
            # Apply timeout (async wrapper for sync function)
            import asyncio
            try:
                # Check if we're in an async context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context, run synchronously with timeout check
                    import time
                    start_time = time.time()
                    response = _make_openai_call()
                    elapsed = time.time() - start_time
                    
                    if elapsed > settings.AI_TIMEOUT_SECONDS:
                        logger.warning(
                            f"OpenAI call took {elapsed:.1f}s (timeout: {settings.AI_TIMEOUT_SECONDS}s)",
                            extra={"trace_id": trace_id}
                        )
                else:
                    # Not in async context, just call directly
                    response = _make_openai_call()
            except RuntimeError:
                # No event loop, call directly
                response = _make_openai_call()
            
            raw_output = response.choices[0].message.content
            
            logger.info(
                "LLM reasoning completed",
                extra={
                    "trace_id": trace_id,
                    "question_id": question_id,
                    "model": self.MODEL_ID,
                    "tokens_used": response.usage.total_tokens
                }
            )
            
        except AITimeoutError as e:
            logger.error(
                f"AI timeout: {str(e)}",
                extra={"trace_id": trace_id, "timeout_seconds": settings.AI_TIMEOUT_SECONDS}
            )
            raise LLMServiceError(
                trace_id=trace_id,
                service_error=f"OpenAI API timed out after {settings.AI_TIMEOUT_SECONDS}s",
                original_error=e
            )
            
        except Exception as e:
            logger.error(
                "LLM API call failed",
                extra={"trace_id": trace_id, "error": str(e)},
                exc_info=True
            )
            raise LLMServiceError(
                trace_id=trace_id,
                service_error="OpenAI API call failed",
                original_error=e
            )
        
        # Parse and validate output
        try:
            parsed = json.loads(raw_output)
            awarded_points, missing_points = self._parse_llm_output(
                parsed,
                rubric_points,
                retrieved_evidence,
                trace_id
            )
            
            return {
                "awarded_points": awarded_points,
                "missing_points": missing_points
            }
            
        except Exception as e:
            logger.error(
                "Failed to parse LLM output",
                extra={"trace_id": trace_id, "raw_output": raw_output},
                exc_info=True
            )
            raise LLMOutputMalformedError(
                trace_id=trace_id,
                reason=str(e),
                raw_output=raw_output
            )
    
    def _build_prompt(
        self,
        student_answer: str,
        rubric_points: List[RubricPoint],
        retrieved_evidence: List[RetrievedEvidence],
        answer_type: AnswerType,
        subject: str
    ) -> str:
        """Build prompt from template.
        
        Args:
            student_answer: Student's answer
            rubric_points: Rubric points
            retrieved_evidence: Evidence
            answer_type: Answer type
            subject: Subject
            
        Returns:
            Formatted prompt
        """
        # Load template based on answer type
        template_file = {
            AnswerType.ESSAY: "essay_prompt.txt",
            AnswerType.SHORT_ANSWER: "short_answer_prompt.txt",
            AnswerType.STRUCTURED: "structured_prompt.txt"
        }[answer_type]
        
        template_path = self.prompts_dir / template_file
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Format evidence
        evidence_text = self._format_evidence(retrieved_evidence)
        
        # Format rubric
        rubric_text = self._format_rubric(rubric_points)
        
        # Fill template
        prompt = template.format(
            subject=subject,
            rubric=rubric_text,
            evidence=evidence_text,
            student_answer=student_answer
        )
        
        return prompt
    
    def _format_evidence(self, evidence_items: List[RetrievedEvidence]) -> str:
        """Format evidence for prompt."""
        lines = []
        for i, ev in enumerate(evidence_items, 1):
            lines.append(f"[EVIDENCE-{i}] (ID: {ev.evidence_id}, Relevance: {ev.relevance_score:.2f})")
            lines.append(f"Source: {ev.source_type}")
            lines.append(f"Content: {ev.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_rubric(self, rubric_points: List[RubricPoint]) -> str:
        """Format rubric for prompt."""
        lines = []
        for point in rubric_points:
            lines.append(f"- [{point.point_id}] {point.description} ({point.marks} marks)")
        
        return "\n".join(lines)
    
    def _parse_llm_output(
        self,
        parsed: Dict[str, Any],
        rubric_points: List[RubricPoint],
        retrieved_evidence: List[RetrievedEvidence],
        trace_id: str
    ) -> tuple:
        """Parse LLM JSON output into structured objects.
        
        Returns:
            Tuple of (awarded_points, missing_points)
        """
        awarded_points = []
        missing_points = []
        
        # Create lookup maps
        rubric_map = {p.point_id: p for p in rubric_points}
        evidence_map = {e.evidence_id: e for e in retrieved_evidence}
        
        # Parse awarded points
        for item in parsed.get("awarded_points", []):
            point_id = item["point_id"]
            
            if point_id not in rubric_map:
                raise LLMOutputMalformedError(
                    trace_id=trace_id,
                    reason=f"LLM awarded point not in rubric: {point_id}"
                )
            
            rubric_point = rubric_map[point_id]
            
            awarded_points.append(
                AwardedPoint(
                    point_id=point_id,
                    description=rubric_point.description,
                    marks=rubric_point.marks,
                    awarded=True,
                    evidence_id=item["evidence_id"],
                    evidence_excerpt=item.get("evidence_excerpt")
                )
            )
        
        # Parse missing points
        for item in parsed.get("missing_points", []):
            point_id = item["point_id"]
            
            if point_id not in rubric_map:
                raise LLMOutputMalformedError(
                    trace_id=trace_id,
                    reason=f"LLM referenced unknown point: {point_id}"
                )
            
            rubric_point = rubric_map[point_id]
            
            missing_points.append(
                MissingPoint(
                    point_id=point_id,
                    description=rubric_point.description,
                    marks=rubric_point.marks,
                    reason=item.get("reason")
                )
            )
        
        return awarded_points, missing_points
