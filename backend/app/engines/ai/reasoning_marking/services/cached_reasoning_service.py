"""Cached Reasoning Service - LLM-powered marking with intelligent caching.

PHASE TWO: This service adds prompt-evidence hash caching to prevent duplicate LLM calls.
"""

import logging
from typing import List, Dict, Any

from app.core.utils.prompt_evidence_hasher import PromptEvidenceHasher
from app.engines.ai.ai_routing_cost_control.services.cache_service import CacheService
from app.engines.ai.reasoning_marking.services.reasoning_service import ReasoningService


logger = logging.getLogger(__name__)


class CachedReasoningService(ReasoningService):
    """Reasoning service with intelligent caching to prevent duplicate AI calls.
    
    Cache Strategy:
    - Before LLM call: check cache using prompt-evidence hash
    - On cache hit: return cached result immediately (zero cost)
    - On cache miss: call LLM, store result, return
    
    Cache Key Components:
    - Normalized student answer
    - Evidence IDs + versions
    - Rubric version
    - Engine version
    - Prompt template version
    """
    
    def __init__(self, redis_client=None, mongodb_client=None):
        """Initialize with cache service.
        
        Args:
            redis_client: Redis client for hot cache
            mongodb_client: MongoDB client for persistent cache
        """
        super().__init__()
        
        # PHASE TWO: Add caching components
        self.cache_service = CacheService(
            redis_client=redis_client,
            mongodb_client=mongodb_client
        )
        self.hasher = PromptEvidenceHasher()
    
    async def perform_reasoning_with_cache(
        self,
        student_answer: str,
        rubric_points: List,
        retrieved_evidence: List,
        answer_type,
        subject: str,
        question_id: str,
        trace_id: str,
        rubric_version: str = "1.0.0",
        engine_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """Perform reasoning with intelligent caching.
        
        Args:
            student_answer: Raw student answer
            rubric_points: Rubric points
            retrieved_evidence: Retrieved evidence
            answer_type: Answer type
            subject: Subject name
            question_id: Question ID
            trace_id: Trace ID
            rubric_version: Rubric version for cache key
            engine_version: Engine version for cache key
            
        Returns:
            Dict with awarded_points and missing_points
        """
        # STEP 1: Generate cache key
        evidence_ids = [ev.evidence_id for ev in retrieved_evidence]
        evidence_versions = {
            ev.evidence_id: ev.metadata.get("version", "1.0.0")
            for ev in retrieved_evidence
        }
        
        cache_key = self.hasher.generate_cache_key(
            student_answer=student_answer,
            evidence_ids=evidence_ids,
            evidence_versions=evidence_versions,
            rubric_version=rubric_version,
            engine_version=engine_version,
            prompt_template_version="1.0.0"
        )
        
        logger.info(
            f"[{trace_id}] Cache key generated: {cache_key[:16]}...",
            extra={"trace_id": trace_id, "cache_key": cache_key}
        )
        
        # STEP 2: Check cache
        cache_decision = await self.cache_service.lookup(cache_key, trace_id)
        
        if cache_decision.cache_hit:
            logger.info(
                f"[{trace_id}] CACHE HIT ({cache_decision.cache_source}) - "
                f"Skipping LLM call (cost=$0)",
                extra={
                    "trace_id": trace_id,
                    "cache_source": cache_decision.cache_source,
                    "cache_key": cache_key[:16]
                }
            )
            
            # Return cached result
            cached_result = cache_decision.cached_data or {}
            return {
                "awarded_points": cached_result.get("awarded_points", []),
                "missing_points": cached_result.get("missing_points", []),
                "cache_hit": True,
                "cache_source": cache_decision.cache_source
            }
        
        # STEP 3: Cache miss - call LLM (original behavior)
        logger.info(
            f"[{trace_id}] CACHE MISS - Calling LLM",
            extra={"trace_id": trace_id, "cache_key": cache_key[:16]}
        )
        
        result = self.perform_reasoning(
            student_answer=student_answer,
            rubric_points=rubric_points,
            retrieved_evidence=retrieved_evidence,
            answer_type=answer_type,
            subject=subject,
            question_id=question_id,
            trace_id=trace_id
        )
        
        # STEP 4: Store result in cache
        await self.cache_service.store(
            cache_key=cache_key,
            result=result,
            trace_id=trace_id
        )
        
        logger.info(
            f"[{trace_id}] Result cached for future use",
            extra={"trace_id": trace_id, "cache_key": cache_key[:16]}
        )
        
        # Add cache metadata to result
        result["cache_hit"] = False
        result["cache_source"] = "none"
        
        return result
