"""Practice Assembly Engine.

Main orchestrator-facing entry point for assembling intelligent practice sessions.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse, EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.core.practice_assembly.schemas import (
    PracticeAssemblyInput,
    PracticeAssemblyOutput,
)
from app.engines.core.practice_assembly.services import (
    QuestionSelector,
    DifficultyBalancer,
    SessionBuilder,
)
from app.engines.core.practice_assembly.errors import (
    PracticeAssemblyError,
    InsufficientQuestionsError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "practice_assembly"
ENGINE_VERSION = "1.0.0"


class PracticeAssemblyEngine:
    """Production-grade practice assembly engine for ZimPrep.
    
    Assembles intelligent practice sessions by selecting questions,
    balancing difficulty, and organizing optimal study experiences.
    
    CRITICAL RULES:
    1. This engine ONLY assembles sessions - does NOT mark answers
    2. Marking happens in Reasoning & Marking Engine
    3. Topic expansion via Topic Intelligence Engine (orchestrator call)
    4. Deterministic selection (same input → same output, modulo randomization)
    5. Respects student history (recency filter)
    
    Execution Flow (7 steps):
    1. Validate input schema
    2. Expand topics using Topic Intelligence (if enabled)
    3. Query available questions for topics
    4. Filter questions (recency, type, already attempted)
    5. Balance difficulty distribution
    6. Select questions (randomize within tiers)
    7. Build and return practice session
    """
    
    def __init__(self, mongodb_client=None, orchestrator=None):
        """Initialize engine with services.
        
        Args:
            mongodb_client: MongoDB client for question queries (optional)
            orchestrator: Orchestrator instance for Topic Intelligence calls (optional)
        """
        self.question_selector = QuestionSelector(mongodb_client)
        self.difficulty_balancer = DifficultyBalancer()
        self.session_builder = SessionBuilder()
        self.orchestrator = orchestrator
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute practice assembly engine.
        
        Implements the mandatory 7-step execution flow.
        
        Args:
            payload: Input data (validated against PracticeAssemblyInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with PracticeAssemblyOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Practice Assembly Engine started",
            extra={"engine": ENGINE_NAME, "trace_id": trace_id}
        )
        
        try:
            # Step 1: Validate input schema
            try:
                engine_input = PracticeAssemblyInput(**payload)
            except ValidationError as e:
                error_msg = f"Input validation failed: {str(e)}"
                logger.error(f"[{trace_id}] {error_msg}")
                return self._build_error_response(error_msg, trace_id, start_time)
            
            # Step 2: Expand topics using Topic Intelligence (if enabled)
            all_topics = engine_input.primary_topic_ids.copy()
            related_topics_added = []
            
            if engine_input.include_related_topics and self.orchestrator:
                logger.info(f"[{trace_id}] Expanding topics via Topic Intelligence")
                
                for topic_id in engine_input.primary_topic_ids:
                    try:
                        # Call Topic Intelligence Engine via orchestrator
                        # (In production, this would be an actual orchestrator call)
                        # related_result = await self.orchestrator.execute_engine(
                        #     engine_name="topic_intelligence",
                        #     payload={
                        #         "operation": "find_similar",
                        #         "query_topic_id": topic_id,
                        #         "similarity_threshold": engine_input.similarity_threshold,
                        #         "max_results": 3,
                        #     },
                        #     context=context
                        # )
                        # related_topics = [
                        #     t["topic_id"]
                        #     for t in related_result.data.get("similar_topics", [])
                        # ]
                        
                        # Placeholder: simulated topic expansion
                        related_topics = []  # Would come from Topic Intelligence
                        
                        all_topics.extend(related_topics)
                        related_topics_added.extend(related_topics)
                        
                    except Exception as e:
                        logger.warning(
                            f"[{trace_id}] Topic expansion failed for {topic_id}: {str(e)}"
                        )
                        # Continue without expansion (graceful degradation)
            
            logger.info(f"[{trace_id}] Using topics: {all_topics}")
            
            # Step 3: Query available questions
            logger.info(f"[{trace_id}] Querying questions...")
            available_questions = await self.question_selector.select_questions(
                topic_ids=all_topics,
                subject=engine_input.subject,
                syllabus_version=engine_input.syllabus_version,
                user_id=engine_input.user_id,
                exclude_recent_days=engine_input.exclude_recent_days,
                preferred_question_types=engine_input.preferred_question_types,
                trace_id=trace_id
            )
            
            logger.info(f"[{trace_id}] Found {len(available_questions)} available questions")
            
            # Step 4: Balance difficulty distribution
            logger.info(f"[{trace_id}] Balancing difficulty...")
            balanced_questions = self.difficulty_balancer.balance_questions(
                available_questions=available_questions,
                target_distribution=engine_input.difficulty_distribution,
                max_questions=engine_input.max_questions,
                trace_id=trace_id
            )
            
            # Step 5: Build practice session
            logger.info(f"[{trace_id}] Building session...")
            practice_session = self.session_builder.build_session(
                user_id=engine_input.user_id,
                session_type=engine_input.session_type,
                subject=engine_input.subject,
                topics=all_topics,
                questions=balanced_questions,
                time_limit_minutes=engine_input.time_limit_minutes,
                trace_id=trace_id
            )
            
            # Step 6: Calculate metadata
            difficulty_breakdown = self.difficulty_balancer.get_difficulty_breakdown(
                balanced_questions
            )
            
            # Step 7: Build output
            output = PracticeAssemblyOutput(
                trace_id=trace_id,
                session_id=practice_session.session_id,
                practice_session=practice_session,
                topics_included=all_topics,
                related_topics_added=related_topics_added,
                total_questions=len(balanced_questions),
                estimated_duration_minutes=practice_session.estimated_duration_minutes,
                difficulty_breakdown=difficulty_breakdown,
                engine_version=ENGINE_VERSION,
                metadata={
                    "session_type": engine_input.session_type,
                    "topic_expansion_enabled": engine_input.include_related_topics,
                }
            )
            
            logger.info(f"[{trace_id}] Practice assembly completed successfully")
            return self._build_response(output, trace_id, start_time)
            
        except InsufficientQuestionsError as e:
            error_msg = f"Insufficient questions: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except Exception as e:
            error_msg = f"Unexpected engine error: {str(e)}"
            logger.exception(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
    
    def _build_response(
        self,
        output: PracticeAssemblyOutput,
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
                confidence=1.0,  # Assembly is deterministic
                metadata={
                    "session_id": output.session_id,
                    "total_questions": output.total_questions,
                    "session_type": output.practice_session.session_type,
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
                metadata={"error_type": "practice_assembly_error"}
            )
        )
