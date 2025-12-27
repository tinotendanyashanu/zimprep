"""Governance Reporting Engine - Main orchestrator-facing entry point.

PHASE FOUR: Regulator-safe audit and compliance reporting.

CRITICAL RULES:
- READ-ONLY operations on all source data
- NO student-identifiable data
- NO AI decision-making
- DETERMINISTIC report generation only
- Full auditability and version tracking
"""

import logging
from datetime import datetime
from typing import Optional
import uuid

from pymongo import MongoClient

from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.engine_response import EngineResponse

from app.engines.governance_reporting.schemas.input import (
    GovernanceReportingInput,
    ReportType
)
from app.engines.governance_reporting.schemas.output import GovernanceReportingOutput
from app.engines.governance_reporting.services.report_generation_service import ReportGenerationService
from app.engines.governance_reporting.repository.governance_repository import GovernanceReportingRepository
from app.engines.governance_reporting.errors.exceptions import GovernanceReportingException

logger = logging.getLogger(__name__)

ENGINE_NAME = "governance_reporting"
ENGINE_VERSION = "1.0.0"


class GovernanceReportingEngine:
    """Production-grade Governance Reporting Engine for ZimPrep.
    
    Generates regulator-safe audit and compliance reports from
    persisted system data without exposing student information.
    
    PHASE FOUR COMPLIANCE:
    - READ-ONLY: No modifications to any data
    - NON-AI: Pure statistical aggregation only
    - NO PII: Student data never exposed
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
        
        self.repository = GovernanceReportingRepository(mongo_client)
        self.report_service = ReportGenerationService()
    
    def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute governance reporting engine.
        
        MANDATORY EXECUTION FLOW:
        1. Validate input schema
        2. Load source data for report period (READ-ONLY)
        3. Generate report sections based on report_type
        4. Persist report (IMMUTABLE)
        5. Return response with audit trail
        
        Args:
            payload: Request payload (validated as GovernanceReportingInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with GovernanceReportingOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Starting governance reporting engine "
            f"(version={ENGINE_VERSION})"
        )
        
        try:
            # Step 1: Validate input
            input_data = GovernanceReportingInput(**payload)
            
            logger.info(
                f"[{trace_id}] Generating {input_data.report_type.value} report "
                f"(scope={input_data.scope.value}, period={input_data.time_period_start} to {input_data.time_period_end})"
            )
            
            # Step 2: Load source data (READ-ONLY)
            cost_data = self.repository.load_cost_tracking_data(
                scope=input_data.scope,
                scope_id=input_data.scope_id,
                start_date=input_data.time_period_start,
                end_date=input_data.time_period_end,
                trace_id=trace_id
            )
            
            audit_data = self.repository.load_audit_records(
                scope=input_data.scope,
                scope_id=input_data.scope_id,
                start_date=input_data.time_period_start,
                end_date=input_data.time_period_end,
                trace_id=trace_id
            )
            
            exam_results = self.repository.load_exam_results(
                scope=input_data.scope,
                scope_id=input_data.scope_id,
                start_date=input_data.time_period_start,
                end_date=input_data.time_period_end,
                trace_id=trace_id
            )
            
            # Step 3: Generate report sections
            output = self._generate_report(
                input_data=input_data,
                cost_data=cost_data,
                audit_data=audit_data,
                exam_results=exam_results,
                trace_id=trace_id
            )
            
            # Step 4: Persist report (IMMUTABLE)
            mongodb_id = self.repository.save_report(
                output=output,
                trace_id=trace_id
            )
            
            # Update output with MongoDB ID
            output = output.model_copy(update={"mongodb_id": mongodb_id})
            
            # Step 5: Return response
            return self._build_response(output, trace_id, start_time)
        
        except GovernanceReportingException as e:
            logger.error(f"[{trace_id}] Governance reporting error: {e}")
            return self._build_error_response(str(e), trace_id, start_time)
        
        except Exception as e:
            logger.exception(f"[{trace_id}] Unexpected error in governance reporting: {e}")
            return self._build_error_response(
                f"Internal error: {e}",
                trace_id,
                start_time
            )
    
    def _generate_report(
        self,
        input_data: GovernanceReportingInput,
        cost_data: list,
        audit_data: list,
        exam_results: list,
        trace_id: str
    ) -> GovernanceReportingOutput:
        """Generate governance report (DETERMINISTIC).
        
        Args:
            input_data: Validated input
            cost_data: AI cost tracking data
            audit_data: Audit trail data
            exam_results: Exam result data
            trace_id: Request trace ID
            
        Returns:
            Governance reporting output
        """
        report_id = str(uuid.uuid4())
        report_type = input_data.report_type
        
        logger.info(f"[{trace_id}] Generating {report_type.value} report (id={report_id})")
        
        # Generate report sections based on type
        ai_usage = None
        validation_stats = None
        appeal_stats = None
        cost_transparency = None
        fairness = None
        system_health = None
        
        if report_type in [ReportType.AI_USAGE, ReportType.COMPREHENSIVE]:
            ai_usage = self.report_service.generate_ai_usage_summary(
                cost_tracking_records=cost_data,
                trace_id=trace_id
            )
        
        if report_type in [ReportType.FAIRNESS, ReportType.COMPREHENSIVE]:
            validation_stats = self.report_service.generate_validation_statistics(
                audit_records=audit_data,
                trace_id=trace_id
            )
            fairness = self.report_service.generate_fairness_indicators(
                exam_results=exam_results,
                trace_id=trace_id
            )
        
        if report_type in [ReportType.APPEALS, ReportType.COMPREHENSIVE]:
            # Simplified: Would filter audit_data for appeals
            appeal_stats = self.report_service.generate_appeal_statistics(
                appeal_records=[],  # Filter from audit_data in production
                trace_id=trace_id
            )
        
        if report_type in [ReportType.COST, ReportType.COMPREHENSIVE]:
            cost_transparency = self.report_service.generate_cost_transparency(
                cost_tracking_records=cost_data,
                trace_id=trace_id
            )
        
        if report_type in [ReportType.SYSTEM_HEALTH, ReportType.COMPREHENSIVE]:
            system_health = self.report_service.generate_system_health(
                audit_records=audit_data,
                trace_id=trace_id
            )
        
        return GovernanceReportingOutput(
            trace_id=trace_id,
            engine_version=ENGINE_VERSION,
            report_id=report_id,
            report_type=report_type,
            scope=input_data.scope,
            scope_id=input_data.scope_id,
            time_period_start=input_data.time_period_start,
            time_period_end=input_data.time_period_end,
            generated_at=datetime.utcnow(),
            ai_usage_summary=ai_usage,
            validation_statistics=validation_stats,
            appeal_statistics=appeal_stats,
            cost_transparency=cost_transparency,
            fairness_indicators=fairness,
            system_health=system_health
        )
    
    def _build_response(
        self,
        output: GovernanceReportingOutput,
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
                "report_id": output.report_id,
                "report_type": output.report_type.value,
                "scope": output.scope.value
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
