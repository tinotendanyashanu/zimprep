"""AI Routing & Cost Control Engine.

Main orchestrator-facing entry point for intelligent AI request routing,
caching, and cost management.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse, EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.ai_routing_cost_control.schemas import (
    RoutingDecisionInput,
    RoutingDecisionOutput,
    RoutingDecision,
    CacheDecision,
    ModelSelection,
)
from app.engines.ai.ai_routing_cost_control.services import (
    CacheService,
    ModelSelector,
    CostTracker,
)
from app.engines.ai.ai_routing_cost_control.errors import (
    AIRoutingError,
    CostLimitExceededError,
    ModelSelectionError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "ai_routing_cost_control"
ENGINE_VERSION = "1.0.0"


class AIRoutingCostControlEngine:
    """Production-grade AI routing and cost control engine for ZimPrep.
    
    Intelligently routes AI requests to optimize cost and performance:
    - Cache-first: Avoids re-executing identical requests
    - Model selection: OSS vs paid based on tier and request type
    - Cost limits: Enforces daily/monthly budgets with graceful degradation
    
    CRITICAL RULES:
    1. This engine does NOT execute AI - it decides HOW AI should execute
    2. Caching prevents wasteful regeneration (90% cost savings potential)
    3. Cost limits enforced with queueing (not hard failure)
    4. Every routing decision is fully auditable
    5. Emergency kill switch available for cost control
    
    Execution Flow (5 steps):
    1. Validate input schema
    2. Compute cache key and check cache (Redis → MongoDB)
    3. If cache miss: Select model (OSS vs paid)
    4. Check cost limits (daily/monthly per user/school)
    5. Return routing decision (cache_hit/execute/queue)
    """
    
    def __init__(self, redis_client=None, mongodb_client=None):
        """Initialize engine with services.
        
        Args:
            redis_client: Redis client for hot cache (optional)
            mongodb_client: MongoDB client for persistent storage (optional)
        """
        self.cache_service = CacheService(redis_client, mongodb_client)
        self.model_selector = ModelSelector()
        self.cost_tracker = CostTracker(mongodb_client)
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute AI routing and cost control engine.
        
        Implements the mandatory 5-step execution flow.
        
        Args:
            payload: Input data (validated against RoutingDecisionInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with RoutingDecisionOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] AI Routing & Cost Control Engine started",
            extra={"engine": ENGINE_NAME, "trace_id": trace_id}
        )
        
        try:
            # Step 1: Validate input schema
            try:
                engine_input = RoutingDecisionInput(**payload)
            except ValidationError as e:
                error_msg = f"Input validation failed: {str(e)}"
                logger.error(f"[{trace_id}] {error_msg}")
                return self._build_error_response(error_msg, trace_id, start_time)
            
            # Step 2: Compute cache key and check cache
            logger.info(f"[{trace_id}] Computing cache key...")
            cache_key = self.cache_service.generate_cache_key(
                prompt_hash=engine_input.prompt_hash,
                evidence_hash=engine_input.evidence_hash,
                syllabus_version=engine_input.syllabus_version
            )
            
            cache_decision = await self.cache_service.lookup(cache_key, trace_id)
            
            # Cache hit - return immediately
            if cache_decision.cache_hit and engine_input.allow_cache:
                logger.info(f"[{trace_id}] Cache HIT - skipping AI execution")
                
                output = RoutingDecisionOutput(
                    trace_id=trace_id,
                    routing_decision=RoutingDecision(
                        decision="cache_hit",
                        reason=f"Cached result  found in {cache_decision.cache_source}"
                    ),
                    cache_decision=cache_decision,
                    model_selection=None,
                    should_execute=False,
                    queue_for_later=False,
                    cached_result=None,  # Would contain actual cached data
                    cost_estimate_usd=0.0,
                    cumulative_cost_today_usd=await self.cost_tracker.get_user_cost_today(engine_input.user_id),
                    cumulative_cost_month_usd=await self.cost_tracker.get_user_cost_month(engine_input.user_id),
                    cost_limit_remaining_usd=0.0,  # Will be calculated below
                    school_cost_remaining_usd=0.0,
                    cache_key=cache_key,
                    escalation_triggered=False,
                    engine_version=ENGINE_VERSION,
                    metadata={"cache_source": cache_decision.cache_source}
                )
                
                return self._build_response(output, trace_id, start_time)
            
            # Step 3: Cache miss - select model
            logger.info(f"[{trace_id}] Cache MISS - selecting model...")
            
            is_escalation = engine_input.previous_confidence is not None and \
                          self.model_selector.should_escalate(
                              engine_input.previous_confidence,
                              engine_input.cost_policy
                          )
            
            model_selection = self.model_selector.select_model(
                request_type=engine_input.request_type,
                user_tier=engine_input.user_tier,
                cost_policy=engine_input.cost_policy,
                is_escalation=is_escalation
            )
            
            logger.info(
                f"[{trace_id}] Selected model: {model_selection.selected_model} "
                f"({model_selection.model_tier}) - {model_selection.selection_reason}"
            )
            
            # Step 4: Check cost limits
            logger.info(f"[{trace_id}] Checking cost limits...")
            
            within_limits, limit_reason = await self.cost_tracker.check_limits(
                user_id=engine_input.user_id,
                school_id=engine_input.school_id,
                estimated_cost=model_selection.estimated_cost_usd,
                cost_policy=engine_input.cost_policy,
                trace_id=trace_id
            )
            
            # Get budget remaining
            budgets = await self.cost_tracker.get_remaining_budget(
                user_id=engine_input.user_id,
                school_id=engine_input.school_id,
                cost_policy=engine_input.cost_policy
            )
            
            # Step 5: Return routing decision
            if within_limits:
                # Execute AI now
                logger.info(f"[{trace_id}] Within cost limits - AI should execute")
                
                # Record usage (optimistic - actual cost may vary)
                await self.cost_tracker.record_usage(
                    user_id=engine_input.user_id,
                    school_id=engine_input.school_id,
                    request_type=engine_input.request_type,
                    model=model_selection.selected_model,
                    cost_usd=model_selection.estimated_cost_usd,
                    trace_id=trace_id
                )
                
                output = RoutingDecisionOutput(
                    trace_id=trace_id,
                    routing_decision=RoutingDecision(
                        decision=model_selection.model_tier + "_model",  # oss_model or paid_model
                        reason=model_selection.selection_reason
                    ),
                    cache_decision=cache_decision,
                    model_selection=model_selection,
                    should_execute=True,
                    queue_for_later=False,
                    cached_result=None,
                    cost_estimate_usd=model_selection.estimated_cost_usd,
                    cumulative_cost_today_usd=await self.cost_tracker.get_user_cost_today(engine_input.user_id),
                    cumulative_cost_month_usd=await self.cost_tracker.get_user_cost_month(engine_input.user_id),
                    cost_limit_remaining_usd=budgets["daily_remaining"],
                    school_cost_remaining_usd=budgets["school_monthly_remaining"],
                    cache_key=cache_key,
                    escalation_triggered=is_escalation,
                    engine_version=ENGINE_VERSION,
                    metadata={
                        "model": model_selection.selected_model,
                        "tier": model_selection.model_tier
                    }
                )
            else:
                # Cost limit exceeded - queue for batch processing
                logger.warning(
                    f"[{trace_id}] Cost limit exceeded - queueing for batch processing: {limit_reason}"
                )
                
                output = RoutingDecisionOutput(
                    trace_id=trace_id,
                    routing_decision=RoutingDecision(
                        decision="queued",
                        reason=limit_reason
                    ),
                    cache_decision=cache_decision,
                    model_selection=model_selection,
                    should_execute=False,
                    queue_for_later=True,
                    cached_result=None,
                    cost_estimate_usd=model_selection.estimated_cost_usd,
                    cumulative_cost_today_usd=await self.cost_tracker.get_user_cost_today(engine_input.user_id),
                    cumulative_cost_month_usd=await self.cost_tracker.get_user_cost_month(engine_input.user_id),
                    cost_limit_remaining_usd=budgets["daily_remaining"],
                    school_cost_remaining_usd=budgets["school_monthly_remaining"],
                    cache_key=cache_key,
                    escalation_triggered=is_escalation,
                    engine_version=ENGINE_VERSION,
                    metadata={"queue_reason": limit_reason}
                )
            
            logger.info(f"[{trace_id}] AI routing completed successfully")
            return self._build_response(output, trace_id, start_time)
            
        except ModelSelectionError as e:
            error_msg = f"Model selection failed: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except Exception as e:
            error_msg = f"Unexpected engine error: {str(e)}"
            logger.exception(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
    
    def _build_response(
        self,
        output: RoutingDecisionOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=True,
            data=output.model_dump(),
            error=None,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=1.0,  # Routing decisions are deterministic
                metadata={
                    "routing_decision": output.routing_decision.decision,
                    "cache_hit": output.cache_decision.cache_hit,
                    "should_execute": output.should_execute,
                    "queue_for_later": output.queue_for_later,
                }
            )
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build error EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=0.0,
                metadata={"error_type": "ai_routing_error"}
            )
        )
