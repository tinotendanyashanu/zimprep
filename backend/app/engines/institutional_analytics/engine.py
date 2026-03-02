"""Institutional Analytics Engine - Main orchestrator-facing entry point.

PHASE FOUR: Cohort-level aggregated analytics with privacy safeguards.

CRITICAL RULES:
- READ-ONLY operations on all source data
- NO modification to student marks or data
- Minimum cohort size enforcement (anti-reidentification)
- NO AI involved in analytics computation
- Full auditability and version tracking
"""

import logging
from datetime import datetime
from typing import Optional

from pymongo import MongoClient

from app.orchestrator.execution_context import ExecutionContext
from app.contracts.engine_response import EngineResponse

from app.engines.institutional_analytics.schemas.input import InstitutionalAnalyticsInput
from app.engines.institutional_analytics.schemas.output import InstitutionalAnalyticsOutput
from app.engines.institutional_analytics.services.privacy_service import PrivacyService
from app.engines.institutional_analytics.services.aggregation_service import AggregationService
from app.engines.institutional_analytics.repository.institutional_repository import InstitutionalAnalyticsRepository
from app.engines.institutional_analytics.errors.exceptions import (
    InstitutionalAnalyticsException,
    InsufficientCohortSizeError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "institutional_analytics"
ENGINE_VERSION = "1.0.0"


class InstitutionalAnalyticsEngine:
    """Production-grade Institutional Analytics Engine for ZimPrep.
    
    Aggregates student-level analytics into cohort-level views for
    teachers, schools, and institutions while maintaining strict
    privacy safeguards.
    
    PHASE FOUR COMPLIANCE:
    - READ-ONLY: No modifications to student data
    - PRIVACY: Minimum cohort sizes enforced
    - NON-AI: Pure statistical aggregation only
    - AUDITABLE: Full version tracking and trace linkage
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize engine.
        
        Args:
            mongo_client: Optional MongoDB client (for testing/DI)
        """
        if mongo_client is None:
            # Production: Get from config
            from app.config.database import get_mongo_client
            mongo_client = get_mongo_client()
        
        self.repository = InstitutionalAnalyticsRepository(mongo_client)
        self.privacy_service = PrivacyService()
        self.aggregation_service = AggregationService()
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute institutional analytics engine.
        
        MANDATORY EXECUTION FLOW:
        1. Validate input schema
        2. Validate minimum cohort size configuration
        3. Load student IDs for scope (READ-ONLY)
        4. Check cohort size against minimum threshold
        5. If sufficient, aggregate analytics from source data
        6. If insufficient, return redacted output
        7. Persist snapshot (IMMUTABLE)
        8. Return response with audit trail
        
        Args:
            payload: Request payload (validated as InstitutionalAnalyticsInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with InstitutionalAnalyticsOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Starting institutional analytics engine "
            f"(version={ENGINE_VERSION})"
        )
        
        try:
            # Step 1: Validate input
            input_data = InstitutionalAnalyticsInput(**payload)
            
            # Step 2: Validate minimum cohort size configuration
            self.privacy_service.validate_min_cohort_size(input_data.min_cohort_size)
            
            # Step 3: Load student IDs for scope (READ-ONLY)
            student_ids = self.repository.get_student_ids_for_scope(
                scope=input_data.scope,
                scope_id=input_data.scope_id,
                trace_id=trace_id
            )
            
            cohort_size = len(student_ids)
            
            logger.info(
                f"[{trace_id}] Cohort size: {cohort_size} students "
                f"(scope={input_data.scope.value}, scope_id={input_data.scope_id})"
            )
            
            # Step 4: Check cohort size against minimum threshold
            sufficient_cohort = self.privacy_service.check_cohort_size(
                cohort_size=cohort_size,
                min_cohort_size=input_data.min_cohort_size,
                scope=input_data.scope.value,
                scope_id=input_data.scope_id,
                trace_id=trace_id
            )
            
            if not sufficient_cohort:
                # Step 6: Return redacted output
                redacted_data = self.privacy_service.redact_data(
                    cohort_size=cohort_size,
                    min_cohort_size=input_data.min_cohort_size,
                    trace_id=trace_id
                )
                
                output = InstitutionalAnalyticsOutput(
                    trace_id=trace_id,
                    engine_version=ENGINE_VERSION,
                    scope=input_data.scope,
                    scope_id=input_data.scope_id,
                    subject=input_data.subject,
                    cohort_size=cohort_size,
                    computed_at=datetime.utcnow(),
                    time_window_days=input_data.time_window_days,
                    min_cohort_size_enforced=input_data.min_cohort_size,
                    **redacted_data
                )
            
            else:
                # Step 5: Aggregate analytics from source data
                output = self._compute_analytics(
                    input_data=input_data,
                    student_ids=student_ids,
                    cohort_size=cohort_size,
                    trace_id=trace_id
                )
            
            # Step 7: Persist snapshot (IMMUTABLE)
            snapshot_id = self.repository.save_snapshot(
                output=output,
                trace_id=trace_id
            )
            
            # Update output with snapshot ID
            output = output.model_copy(update={"snapshot_id": snapshot_id})
            
            # Step 8: Return response
            return self._build_response(output, trace_id, start_time)
        
        except InsufficientCohortSizeError as e:
            logger.error(f"[{trace_id}] Insufficient cohort size: {e}")
            return self._build_error_response(str(e), trace_id, start_time)
        
        except InstitutionalAnalyticsException as e:
            logger.error(f"[{trace_id}] Institutional analytics error: {e}")
            return self._build_error_response(str(e), trace_id, start_time)
        
        except Exception as e:
            logger.exception(f"[{trace_id}] Unexpected error in institutional analytics: {e}")
            return self._build_error_response(
                f"Internal error: {e}",
                trace_id,
                start_time
            )
    
    def _compute_analytics(
        self,
        input_data: InstitutionalAnalyticsInput,
        student_ids: list[str],
        cohort_size: int,
        trace_id: str
    ) -> InstitutionalAnalyticsOutput:
        """Compute cohort-level analytics (DETERMINISTIC).
        
        Args:
            input_data: Validated input
            student_ids: List of student user IDs
            cohort_size: Cohort size
            trace_id: Request trace ID
            
        Returns:
            Institutional analytics output
        """
        logger.info(f"[{trace_id}] Computing cohort analytics for {cohort_size} students")
        
        # Load source data (READ-ONLY)
        learning_analytics = self.repository.load_learning_analytics_snapshots(
            user_ids=student_ids,
            subject=input_data.subject,
            time_window_days=input_data.time_window_days,
            trace_id=trace_id
        )
        
        mastery_states = self.repository.load_mastery_states(
            user_ids=student_ids,
            subject=input_data.subject,
            trace_id=trace_id
        )
        
        # Extract source snapshot versions for audit trail
        source_versions = [
            snap.get("snapshot_id") for snap in learning_analytics
            if snap.get("snapshot_id")
        ]
        source_versions.extend([
            state.get("mastery_snapshot_id") for state in mastery_states
            if state.get("mastery_snapshot_id")
        ])
        
        # Compute aggregations (DETERMINISTIC)
        mastery_distribution = self.aggregation_service.aggregate_mastery_distribution(
            mastery_states=mastery_states,
            trace_id=trace_id
        )
        
        cohort_scores = self.aggregation_service.aggregate_cohort_scores(
            analytics_snapshots=learning_analytics,
            trace_id=trace_id
        )
        
        trend_indicators = self.aggregation_service.aggregate_trend_indicators(
            analytics_snapshots=learning_analytics,
            trace_id=trace_id
        )
        
        coverage_gaps = self.aggregation_service.identify_coverage_gaps(
            analytics_snapshots=learning_analytics,
            trace_id=trace_id
        )
        
        return InstitutionalAnalyticsOutput(
            trace_id=trace_id,
            engine_version=ENGINE_VERSION,
            scope=input_data.scope,
            scope_id=input_data.scope_id,
            subject=input_data.subject,
            cohort_size=cohort_size,
            topic_mastery_distribution=mastery_distribution,
            cohort_average_scores=cohort_scores,
            trend_indicators=trend_indicators,
            coverage_gaps=coverage_gaps,
            privacy_redacted=False,
            min_cohort_size_enforced=input_data.min_cohort_size,
            computed_at=datetime.utcnow(),
            time_window_days=input_data.time_window_days,
            source_snapshot_versions=source_versions
        )
    
    def _build_response(
        self,
        output: InstitutionalAnalyticsOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse."""
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=True,
            engine_name=ENGINE_NAME,
            trace_id=trace_id,
            data=output.model_dump(),
            execution_time_ms=duration_ms,
            metadata={
                "cohort_size": output.cohort_size,
                "privacy_redacted": output.privacy_redacted,
                "topics_analyzed": len(output.topic_mastery_distribution)
            }
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build error EngineResponse."""
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=False,
            engine_name=ENGINE_NAME,
            trace_id=trace_id,
            error=error_message,
            execution_time_ms=duration_ms
        )
