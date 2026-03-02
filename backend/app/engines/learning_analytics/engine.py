"""Learning Analytics Engine - Main orchestrator-facing entry point.

PHASE THREE: Longitudinal learning intelligence from historical data.

CRITICAL RULES:
- READ-ONLY operations on exam results
- NO modification to grading logic
- Deterministic and replayable
- NO AI calls (pure statistics)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List
from pymongo import MongoClient
from pydantic import ValidationError

from app.orchestrator.execution_context import ExecutionContext
from app.contracts.engine_response import EngineResponse
from app.engines.learning_analytics.schemas.input import LearningAnalyticsInput
from app.engines.learning_analytics.schemas.output import (
    LearningAnalyticsOutput,
    TopicAnalytics,
    TopicPerformanceTimeline,
    TrendAnalysis,
    ConfidenceAdjustedScore,
    TrendDirection,
)
from app.engines.learning_analytics.services.aggregation_service import AggregationService
from app.engines.learning_analytics.repository.analytics_repository import LearningAnalyticsRepository
from app.engines.learning_analytics.errors.exceptions import (
    LearningAnalyticsException,
    InsufficientDataError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "learning_analytics"
ENGINE_VERSION = "1.0.0"


class LearningAnalyticsEngine:
    """Production-grade Learning Analytics Engine for ZimPrep.
    
    Transforms immutable exam results into longitudinal learning signals
    through pure statistical analysis.
    
    PHASE THREE COMPLIANCE:
    - NO grading logic alteration
    - READ-ONLY operations
    - Deterministic calculations
    - Full auditability
    """
    
    def __init__(self, mongo_client: MongoClient | None = None):
        """Initialize engine.
        
        Args:
            mongo_client: Optional MongoDB client (for testing/DI)
        """
        if mongo_client is None:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            mongo_client = MongoClient(mongo_uri)
        
        self.aggregation_service = AggregationService()
        self.repository = LearningAnalyticsRepository(mongo_client)
        
        logger.info(f"✓ {ENGINE_NAME} v{ENGINE_VERSION} initialized")
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute learning analytics engine.
        
        MANDATORY EXECUTION FLOW:
        1. Validate input schema
        2. Load historical exam results (READ-ONLY)
        3. Extract topic-level performance timelines
        4. Compute statistical metrics (rolling avg, trend, volatility)
        5. Generate confidence-adjusted scores
        6. Persist immutable snapshot
        7. Return analytics output
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with LearningAnalyticsOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Learning Analytics Engine starting",
            extra={"trace_id": trace_id, "engine": ENGINE_NAME}
        )
        
        try:
            # Step 1: Validate input
            try:
                input_data = LearningAnalyticsInput(**payload)
            except ValidationError as e:
                logger.error(f"[{trace_id}] Input validation failed: {e}")
                return self._build_error_response(
                    f"Invalid input: {str(e)}",
                    trace_id,
                    start_time
                )
            
            logger.info(
                f"[{trace_id}] Analyzing user={input_data.user_id}, "
                f"subject={input_data.subject}, window={input_data.time_window_days}d"
            )
            
            # Step 2: Load historical results (READ-ONLY)
            historical_results = self._load_historical_results(
                user_id=input_data.user_id,
                subject=input_data.subject,
                topic_id=input_data.topic_id,
                time_window_days=input_data.time_window_days,
                trace_id=trace_id
            )
            
            # Step 3: Check for sufficient data
            if len(historical_results) < input_data.min_attempts:
                logger.warning(
                    f"[{trace_id}] Insufficient data: {len(historical_results)} attempts "
                    f"(need {input_data.min_attempts})"
                )
                
                # Return empty analytics with status flag
                output = LearningAnalyticsOutput(
                    trace_id=trace_id,
                    engine_version=ENGINE_VERSION,
                    user_id=input_data.user_id,
                    subject=input_data.subject,
                    analyzed_at=datetime.utcnow(),
                    topic_analytics=[],
                    total_attempts_analyzed=len(historical_results),
                    time_window_days=input_data.time_window_days,
                    has_sufficient_data=False,
                    notes=f"Insufficient attempts: found {len(historical_results)}, need {input_data.min_attempts}",
                    source_attempt_ids=[]
                )
                
                return self._build_response(output, trace_id, start_time)
            
            # Step 4: Extract topic-level timelines
            topic_timelines = self._extract_topic_timelines(
                historical_results,
                trace_id
            )
            
            # Step 5: Compute analytics for each topic
            topic_analytics_list: List[TopicAnalytics] = []
            
            for topic_id, timeline_data in topic_timelines.items():
                topic_analytics = self._compute_topic_analytics(
                    topic_id=topic_id,
                    timeline_data=timeline_data,
                    trace_id=trace_id
                )
                topic_analytics_list.append(topic_analytics)
            
            # Step 6: Build output
            source_attempt_ids = [r.get("trace_id", "") for r in historical_results]
            
            output = LearningAnalyticsOutput(
                trace_id=trace_id,
                engine_version=ENGINE_VERSION,
                user_id=input_data.user_id,
                subject=input_data.subject,
                analyzed_at=datetime.utcnow(),
                topic_analytics=topic_analytics_list,
                total_attempts_analyzed=len(historical_results),
                time_window_days=input_data.time_window_days,
                has_sufficient_data=True,
                source_attempt_ids=source_attempt_ids
            )
            
            # Step 7: Persist snapshot (immutable)
            snapshot_id = self.repository.save_snapshot(output, trace_id)
            
            # Update output with snapshot ID (create new instance since frozen)
            output_dict = output.model_dump()
            output_dict["snapshot_id"] = snapshot_id
            output_with_id = LearningAnalyticsOutput(**output_dict)
            
            logger.info(
                f"[{trace_id}] Learning analytics computed: "
                f"{len(topic_analytics_list)} topics, snapshot={snapshot_id}"
            )
            
            return self._build_response(output_with_id, trace_id, start_time)
            
        except LearningAnalyticsException as e:
            logger.error(f"[{trace_id}] Analytics error: {e.message}")
            return self._build_error_response(e.message, trace_id, start_time)
        except Exception as e:
            logger.error(f"[{trace_id}] Unexpected error: {e}", exc_info=True)
            return self._build_error_response(
                f"Internal error: {str(e)}",
                trace_id,
                start_time
            )
    
    def _load_historical_results(
        self,
        user_id: str,
        subject: str,
        topic_id: str | None,
        time_window_days: int,
        trace_id: str
    ) -> List[dict]:
        """Load historical exam results (READ-ONLY).
        
        Args:
            user_id: Student identifier
            subject: Subject code
            topic_id: Optional topic filter
            time_window_days: Analysis window
            trace_id: Trace ID for logging
            
        Returns:
            List of exam result documents
        """
        # Access results repository
        from app.engines.results.repository.results_repo import ResultsRepository
        
        results_repo = ResultsRepository(
            mongo_client=self.repository.client,
            database_name="zimprep"
        )
        
        # Query historical results
        results = results_repo.find_by_candidate(
            candidate_id=user_id,
            subject_code=subject
        )
        
        # Filter by time window
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        filtered_results = [
            r for r in results
            if r.get("issued_at", datetime.min) >= cutoff_date
        ]
        
        logger.info(
            f"[{trace_id}] Loaded {len(filtered_results)} results "
            f"(from {len(results)} total)"
        )
        
        return filtered_results
    
    def _extract_topic_timelines(
        self,
        results: List[dict],
        trace_id: str
    ) -> dict:
        """Extract per-topic performance timelines.
        
        Args:
            results: List of exam results
            trace_id: Trace ID
            
        Returns:
            Dict mapping topic_id to timeline data
        """
        topic_timelines = {}
        
        for result in results:
            # Extract topic breakdown
            topic_breakdown = result.get("topic_breakdown", [])
            issued_at = result.get("issued_at", datetime.utcnow())
            result_trace_id = result.get("trace_id", "")
            
            for topic in topic_breakdown:
                topic_id = topic.get("topic_code", "")
                topic_name = topic.get("topic_name", "")
                percentage = topic.get("percentage", 0.0)
                
                if not topic_id:
                    continue
                
                if topic_id not in topic_timelines:
                    topic_timelines[topic_id] = {
                        "topic_name": topic_name,
                        "timestamps": [],
                        "scores": [],
                        "trace_ids": []
                    }
                
                topic_timelines[topic_id]["timestamps"].append(issued_at)
                topic_timelines[topic_id]["scores"].append(percentage)
                topic_timelines[topic_id]["trace_ids"].append(result_trace_id)
        
        logger.info(f"[{trace_id}] Extracted {len(topic_timelines)} topic timelines")
        
        return topic_timelines
    
    def _compute_topic_analytics(
        self,
        topic_id: str,
        timeline_data: dict,
        trace_id: str
    ) -> TopicAnalytics:
        """Compute analytics for a single topic.
        
        Args:
            topic_id: Topic identifier
            timeline_data: Timeline data dict
            trace_id: Trace ID
            
        Returns:
            TopicAnalytics object
        """
        timestamps = timeline_data["timestamps"]
        scores = timeline_data["scores"]
        trace_ids = timeline_data["trace_ids"]
        topic_name = timeline_data["topic_name"]
        
        # Sort by timestamp
        sorted_data = sorted(zip(timestamps, scores, trace_ids))
        timestamps, scores, trace_ids = zip(*sorted_data)
        timestamps = list(timestamps)
        scores = list(scores)
        trace_ids = list(trace_ids)
        
        # Build timeline
        timeline = TopicPerformanceTimeline(
            topic_id=topic_id,
            topic_name=topic_name,
            attempt_timestamps=timestamps,
            attempt_scores=scores,
            attempt_ids=trace_ids
        )
        
        # Compute metrics using aggregation service
        rolling_avg = self.aggregation_service.calculate_rolling_average(scores)
        
        slope, r_squared = self.aggregation_service.detect_trend_slope(
            timestamps,
            scores
        )
        
        trend_direction = self.aggregation_service.classify_trend_direction(slope)
        
        volatility = self.aggregation_service.calculate_volatility(scores)
        
        trend = TrendAnalysis(
            slope=slope,
            direction=trend_direction,
            volatility=volatility,
            r_squared=r_squared
        )
        
        # Confidence-adjusted score
        weighted_score, confidence = self.aggregation_service.confidence_weighted_score(scores)
        
        # Factor in attempt count for confidence
        attempt_confidence = self.aggregation_service.calculate_attempt_confidence(
            len(scores)
        )
        overall_confidence = (confidence + attempt_confidence) / 2
        
        confidence_adjusted = ConfidenceAdjustedScore(
            raw_average=sum(scores) / len(scores),
            weighted_score=weighted_score,
            confidence=overall_confidence,
            sample_size=len(scores)
        )
        
        return TopicAnalytics(
            topic_id=topic_id,
            topic_name=topic_name,
            timeline=timeline,
            rolling_average=rolling_avg,
            trend=trend,
            confidence_adjusted=confidence_adjusted
        )
    
    def _build_response(
        self,
        output: LearningAnalyticsOutput,
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
