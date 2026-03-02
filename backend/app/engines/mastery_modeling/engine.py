"""Mastery Modeling Engine - Main orchestrator-facing entry point.

PHASE THREE: AI-assisted mastery classification with full explainability.

CRITICAL RULES:
- OSS AI models only (NO paid LLMs)
- Deterministic fallback required
- NO modification to grading logic
- All classifications fully explainable
"""

import logging
import os
import statistics
from datetime import datetime
from pymongo import MongoClient
from pydantic import ValidationError

from app.orchestrator.execution_context import ExecutionContext
from app.contracts.engine_response import EngineResponse
from app.engines.mastery_modeling.schemas.input import MasteryModelingInput
from app.engines.mastery_modeling.schemas.output import (
    MasteryModelingOutput,
    TopicMasteryState,
)
from app.engines.mastery_modeling.services.classifier_service import ClassifierService
from app.engines.mastery_modeling.services.weakness_strength_detector import WeaknessStrengthDetector
from app.engines.mastery_modeling.repository.mastery_repository import MasteryRepository
from app.engines.mastery_modeling.errors.exceptions import (
    MasteryModelingException,
    InsufficientAnalyticsDataError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "mastery_modeling"
ENGINE_VERSION = "1.0.0"


class MasteryModelingEngine:
    """Production-grade Mastery Modeling Engine for ZimPrep.
    
    Classifies topic mastery levels using OSS AI with deterministic fallback,
    detecting weaknesses and strengths for adaptive learning.
    
    PHASE THREE COMPLIANCE:
    - OSS AI only (sentence-transformers)
    - Deterministic rule-based fallback
    - Full explainability with justification traces
    - NO grading logic alteration
    """
    
    def __init__(self, mongo_client: MongoClient | None = None, use_ai: bool = True):
        """Initialize engine.
        
        Args:
            mongo_client: Optional MongoDB client (for testing/DI)
            use_ai: Whether to use AI-assisted classification
        """
        if mongo_client is None:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            mongo_client = MongoClient(mongo_uri)
        
        self.classifier_service = ClassifierService(use_ai=use_ai)
        self.weakness_strength_detector = WeaknessStrengthDetector()
        self.repository = MasteryRepository(mongo_client)
        
        logger.info(f"✓ {ENGINE_NAME} v{ENGINE_VERSION} initialized (AI={use_ai})")
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute mastery modeling engine.
        
        MANDATORY EXECUTION FLOW:
        1. Validate input schema
        2. For each topic, classify mastery level
        3. Generate full justification traces
        4. Detect weaknesses (topics needing attention)
        5. Detect strengths (topics with strong performance)
        6. Persist immutable mastery states
        7. Return mastery modeling output
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with MasteryModelingOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Mastery Modeling Engine starting",
            extra={"trace_id": trace_id, "engine": ENGINE_NAME}
        )
        
        try:
            # Step 1: Validate input
            try:
                input_data = MasteryModelingInput(**payload)
            except ValidationError as e:
                logger.error(f"[{trace_id}] Input validation failed: {e}")
                return self._build_error_response(
                    f"Invalid input: {str(e)}",
                    trace_id,
                    start_time
                )
            
            logger.info(
                f"[{trace_id}] Classifying mastery: user={input_data.user_id}, "
                f"subject={input_data.subject}, topics={len(input_data.topic_analytics)}"
            )
            
            # Step 2: Check for sufficient data
            if not input_data.topic_analytics:
                raise InsufficientAnalyticsDataError(
                    user_id=input_data.user_id,
                    subject=input_data.subject,
                    trace_id=trace_id
                )
            
            # Step 3: Classify mastery for each topic
            mastery_states = []
            
            for topic_analytics in input_data.topic_analytics:
                mastery_level, justification = self.classifier_service.classify_mastery(
                    topic_analytics=topic_analytics,
                    time_decay_factor=input_data.time_decay_factor
                )
                
                state = TopicMasteryState(
                    topic_id=topic_analytics.topic_id,
                    topic_name=topic_analytics.topic_name,
                    mastery_level=mastery_level,
                    justification=justification,
                    computed_at=datetime.utcnow()
                )
                
                mastery_states.append(state)
                
                logger.debug(
                    f"[{trace_id}] Topic {topic_analytics.topic_id}: {mastery_level.value}"
                )
            
            # Step 4: Detect weaknesses
            weaknesses = self.weakness_strength_detector.detect_weaknesses(mastery_states)
            
            # Step 5: Detect strengths
            strengths = self.weakness_strength_detector.detect_strengths(mastery_states)
            
            # Step 6: Calculate overall confidence
            confidences = [state.justification.confidence_weight for state in mastery_states]
            overall_confidence = statistics.mean(confidences) if confidences else 0.0
            
            # Step 7: Build output
            output = MasteryModelingOutput(
                trace_id=trace_id,
                engine_version=ENGINE_VERSION,
                user_id=input_data.user_id,
                subject=input_data.subject,
                computed_at=datetime.utcnow(),
                topic_mastery_states=mastery_states,
                weaknesses=weaknesses,
                strengths=strengths,
                total_topics_analyzed=len(mastery_states),
                overall_confidence=overall_confidence,
                source_analytics_snapshot_id=payload.get("analytics_snapshot_id")
            )
            
            # Step 8: Persist mastery states (immutable)
            mastery_ids = self.repository.save_mastery_states(output, trace_id)
            
            # Update output with first mastery ID as snapshot reference
            output_dict = output.model_dump()
            output_dict["mastery_snapshot_id"] = mastery_ids[0] if mastery_ids else None
            output_with_id = MasteryModelingOutput(**output_dict)
            
            logger.info(
                f"[{trace_id}] Mastery modeling complete: "
                f"{len(mastery_states)} topics, {len(weaknesses)} weaknesses, "
                f"{len(strengths)} strengths"
            )
            
            return self._build_response(output_with_id, trace_id, start_time)
            
        except MasteryModelingException as e:
            logger.error(f"[{trace_id}] Mastery modeling error: {e.message}")
            return self._build_error_response(e.message, trace_id, start_time)
        except Exception as e:
            logger.error(f"[{trace_id}] Unexpected error: {e}", exc_info=True)
            return self._build_error_response(
                f"Internal error: {str(e)}",
                trace_id,
                start_time
            )
    
    def _build_response(
        self,
        output: MasteryModelingOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse."""
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return EngineResponse(
            engine_name=ENGINE_NAME,
            success=True,
            data=output.model_dump(),
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            error_message=None
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build error EngineResponse."""
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return EngineResponse(
            engine_name=ENGINE_NAME,
            success=False,
            data={},
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )
