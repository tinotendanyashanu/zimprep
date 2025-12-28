"""
Reporting & Analytics Engine - Core Engine

Version: 1.0.0
Type: Core Engine (NON-AI)
Confidence: Always 1.0 (deterministic)

This engine transforms immutable exam results into human-readable,
role-appropriate insights. It NEVER calculates marks, infers performance,
or performs AI reasoning. It ONLY formats, aggregates, visualizes, and
exports already-finalized data.
"""

from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
import logging

from app.engines.reporting_analytics.schemas.input import ReportingInput, UserRole
from app.engines.reporting_analytics.schemas.output import (
    ReportingOutput,
    ReportType,
    VisualSection,
)
from pymongo import MongoClient
from app.config.settings import settings
from app.engines.results.repository.results_repo import ResultsRepository
from app.engines.reporting_analytics.rules.visibility_rules import VisibilityEnforcer
from app.engines.reporting_analytics.rules.aggregation_rules import AggregationRules
from app.engines.reporting_analytics.services.report_builder import ReportBuilderService
from app.engines.reporting_analytics.services.trend_analyzer import TrendAnalyzerService
from app.engines.reporting_analytics.services.visualization_mapper import VisualizationMapperService
from app.engines.reporting_analytics.services.pdf_renderer import PDFRendererService
from app.engines.reporting_analytics.services.export_service import ExportService
from app.engines.reporting_analytics.services.azure_export_storage_service import AzureExportStorageService
from app.engines.reporting_analytics.services.performance_calculator import PerformanceCalculator
from app.engines.reporting_analytics.schemas.input import ReportingScope, ExportFormat
from app.engines.reporting_analytics.errors.exceptions import (
    ReportingEngineError,
    InvalidRoleError,
    ResultsNotFoundError,
    ReportGenerationError,
    ExportFailureError,
    VisibilityViolationError,
)

logger = logging.getLogger(__name__)


class ReportingAnalyticsEngine:
    """
    Reporting & Analytics Engine (v1.0.0)
    
    Position in Pipeline:
    - Runs AFTER: Results Engine, Recommendation Engine
    - Runs BEFORE: Audit & Compliance Engine
    
    Execution Flow (9 steps):
    1. Validate input schema
    2. Verify role-based visibility rules
    3. Load immutable Results Engine output
    4. Assemble report sections
    5. Aggregate historical trends (if requested)
    6. Render exports (PDF / CSV)
    7. Produce deterministic output
    8. Return ReportingOutput
    9. Pass full trace to Audit Engine (via orchestrator)
    
    CRITICAL CONSTRAINTS:
    - NEVER modify marks or grades
    - NEVER recalculate results
    - NEVER perform predictions or AI reasoning
    - NEVER call other engines directly
    - NEVER write to Results storage
    - ALWAYS produce confidence = 1.0
    """
    
    ENGINE_NAME = "reporting_analytics"
    ENGINE_VERSION = "1.0.0"
    ENGINE_TYPE = "core"  # Non-AI
    
    def __init__(self):
        """Initialize the Reporting & Analytics Engine."""
        self.logger = logger
        
        # Initialize repository connection
        try:
            self.mongo_client = MongoClient(settings.MONGODB_URI)
            self.results_repo = ResultsRepository(self.mongo_client)
            self.logger.info("Connected to ResultsRepository")
        except Exception as e:
            self.logger.warning(f"Failed to connect to ResultsRepository: {e}")
            self.results_repo = None
        
        # Initialize Azure storage service for export persistence
        self.azure_storage = AzureExportStorageService()
    
    async def execute(
        self,
        input_data: ReportingInput,
        results_data: Dict[str, Any] | None = None,
        historical_data: List[Dict[str, Any]] | None = None,
        engine_outputs: Dict[str, Any] | None = None,
    ) -> ReportingOutput:
        """
        Execute the 9-step reporting flow.
        
        Args:
            input_data: Validated ReportingInput
            results_data: Immutable results from Results Engine
            historical_data: Optional historical performance data
            
        Returns:
            ReportingOutput with deterministic confidence = 1.0
            
        Raises:
            ReportingEngineError: If any step fails
        """
        trace_id = input_data.trace_id
        
        self.logger.info(
            f"[{trace_id}] Starting Reporting & Analytics Engine execution",
            extra={
                "trace_id": str(trace_id),
                "user_id": str(input_data.user_id),
                "role": input_data.role.value,
                "scope": input_data.reporting_scope.value,
            }
        )
        
        try:
            # Step 1: Validate input schema (already done by Pydantic)
            self._log_step(trace_id, 1, "Input schema validated")
            
            # Step 2: Verify role-based visibility rules
            self._verify_visibility(input_data)
            self._log_step(trace_id, 2, "Visibility rules verified")
            
            # Step 3: Load immutable Results Engine output
            results = self._load_results_data(input_data, results_data)
            self._log_step(trace_id, 3, "Results data loaded")
            
            # Step 4: Assemble report sections
            report_data = self._assemble_report(
                input_data, results, historical_data
            )
            self._log_step(trace_id, 4, "Report sections assembled")
            
            # Step 5: Aggregate historical trends (if requested)
            if input_data.reporting_scope == ReportingScope.LONGITUDINAL:
                report_data = self._aggregate_trends(
                    input_data, report_data, historical_data
                )
                self._log_step(trace_id, 5, "Historical trends aggregated")
            else:
                self._log_step(trace_id, 5, "Historical trends skipped (scope: {})".format(
                    input_data.reporting_scope.value
                ))
            
            # Step 6: Render exports (PDF / CSV)
            export_metadata = self._render_exports(
                input_data, report_data
            )
            self._log_step(trace_id, 6, "Exports rendered")
            
            # Step 7: Produce deterministic output
            visual_sections = self._generate_visualizations(
                input_data, report_data
            )
            self._log_step(trace_id, 7, "Visualizations generated")
            
            # Step 8: Return ReportingOutput
            output = self._build_output(
                input_data,
                report_data,
                visual_sections,
                export_metadata,
            )
            self._log_step(trace_id, 8, "Output assembled")
            
            # Step 9: Pass full trace to Audit Engine (handled by orchestrator)
            self._log_step(
                trace_id,
                9,
                "Trace prepared for Audit Engine (orchestrator will handle)"
            )
            
            self.logger.info(
                f"[{trace_id}] Reporting & Analytics Engine execution completed",
                extra={
                    "trace_id": str(trace_id),
                    "report_id": str(output.report_id),
                    "confidence": output.confidence,
                }
            )
            
            return output
        
        except ReportingEngineError:
            # Re-raise our custom errors
            raise
        
        except Exception as e:
            # Wrap unexpected errors
            self.logger.error(
                f"[{trace_id}] Unexpected error in Reporting & Analytics Engine",
                extra={
                    "trace_id": str(trace_id),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise ReportGenerationError(
                message=f"Unexpected error in reporting engine: {str(e)}",
                trace_id=trace_id,
                context={"error": str(e)},
            )
    
    def _verify_visibility(self, input_data: ReportingInput) -> None:
        """
        Step 2: Verify role-based visibility rules.
        
        Args:
            input_data: Validated input
            
        Raises:
            VisibilityViolationError: If access is not permitted
            InvalidRoleError: If role is invalid
        """
        enforcer = VisibilityEnforcer(trace_id=input_data.trace_id)
        
        # Verify access (simplified - in production, check against DB)
        enforcer.verify_access(
            user_id=input_data.user_id,
            role=input_data.role,
            target_student_id=None,  # Would be determined from exam_session_id
            target_school_id=None,  # Would be determined from exam_session_id
        )
    
    def _load_results_data(
        self,
        input_data: ReportingInput,
        results_data: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """
        Step 3: Load immutable Results Engine output.
        
        Args:
            input_data: Validated input
            results_data: Pre-loaded results data (from orchestrator)
            
        Returns:
            Results data
            
        Raises:
            ResultsNotFoundError: If results cannot be found
        """
        if input_data.reporting_scope in [ReportingScope.DASHBOARD, ReportingScope.HISTORY]:
            # For Dashboard/History, we fetch ALL results for the user
            if not self.results_repo:
                raise ResultsNotFoundError(
                    message="Results repository not available",
                    trace_id=input_data.trace_id,
                    context={}
                )
            
            # Fetch recent results
            recent_results = self.results_repo.find_by_candidate(
                candidate_id=str(input_data.user_id)
            )
            
            # Convert ObjectIds to strings if necessary
            for r in recent_results:
                if "_id" in r:
                    r["_id"] = str(r["_id"])
            
            return {"dashboard_results": recent_results}

        if results_data is None:
            # In production, check repository if not provided by orchestrator
            if self.results_repo and input_data.exam_session_id:
                # Try to find by trace_id first (if exam_session_id was trace_id) 
                # or we need to look up by candidate + exam + subject
                # For simplicity, if we have exam_session_id, assume strict lookup might be needed,
                # but currently pipelines pass results_data explicitly.
                pass

            # Raise error if still not found
            raise ResultsNotFoundError(
                message=f"Results not found for exam session {input_data.exam_session_id}",
                trace_id=input_data.trace_id,
                context={
                    "exam_session_id": str(input_data.exam_session_id),
                    "subject_code": input_data.subject_code,
                },
            )
        
        # Validate that we have the minimum required data
        required_fields = ["exam_title", "subject_name", "percentage", "grade"]
        missing_fields = [f for f in required_fields if f not in results_data]
        
        if missing_fields:
            raise ReportGenerationError(
                message=f"Results data missing required fields: {missing_fields}",
                trace_id=input_data.trace_id,
                context={
                    "missing_fields": missing_fields,
                },
            )
        
        return results_data
    
    def _assemble_report(
        self,
        input_data: ReportingInput,
        results: Dict[str, Any],
        historical_data: List[Dict[str, Any]] | None,
        engine_outputs: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Step 4: Assemble report sections based on role.
        
        Args:
            input_data: Validated input
            results: Results data
            historical_data: Optional historical data
            
        Returns:
            Assembled report data (role-specific)
            
        Raises:
            ReportGenerationError: If assembly fails
        """
        builder = ReportBuilderService(trace_id=input_data.trace_id)
        
        if input_data.reporting_scope in [ReportingScope.DASHBOARD, ReportingScope.HISTORY]:
            # Custom dashboard/history payload
            dashboard_results = results.get("dashboard_results", [])
            
            # Transform for frontend consumption
            recent_exams = []
            for res in dashboard_results:
                recent_exams.append({
                    "exam_id": res.get("exam_id"),
                    "exam_name": f"{res.get('subject_name')} - {res.get('paper_code', 'Paper 1')}",
                    "date": res.get("issued_at", datetime.now()).isoformat(),
                    "grade": res.get("grade"),
                    "marks": res.get("total_marks"),
                    "max_marks": res.get("max_total_marks"),
                    "trace_id": res.get("trace_id"),
                    "can_appeal": True
                })

            if input_data.reporting_scope == ReportingScope.HISTORY:
                return {
                    "history": recent_exams  # Return all, no truncation
                }

            # Calculate real performance metrics from database
            calculator = PerformanceCalculator()
            avg_grade = calculator.calculate_average_grade(dashboard_results)
            improvement_trend = calculator.calculate_improvement_trend(dashboard_results)
            strengths = calculator.identify_strengths(dashboard_results)
            weaknesses = calculator.identify_weaknesses(dashboard_results)

            # CRITICAL: Upcoming exams are NO LONGER hardcoded
            # They are provided by the Exam Structure Engine via orchestrator
            # If exam_structure engine hasn't run yet or failed, this will be empty
            upcoming_exams = []
            if engine_outputs and "exam_structure" in engine_outputs:
                # Extract upcoming_exams from exam_structure engine output
                exam_structure_output = engine_outputs.get("exam_structure", {})
                upcoming_exams = exam_structure_output.get("upcoming_exams", [])
            
            # CRITICAL: Recommendations are NO LONGER hardcoded
            # They will be injected by the orchestrator from the Recommendation Engine output
            # If recommendation engine hasn't run yet or failed, this will be empty
            # The gateway/controller is responsible for merging recommendation data
            return {
                "dashboard": {
                    "recent_exams": recent_exams[:5], # Top 5
                    "upcoming_exams": upcoming_exams,  # From Exam Structure Engine
                    "performance": {
                        "average_grade": avg_grade,
                        "improvement_trend": improvement_trend,
                        "strengths": strengths,
                        "weaknesses": weaknesses
                    },
                    "recommendations": []  # Empty - will be populated from Recommendation Engine
                }
            }
        
        if input_data.role == UserRole.STUDENT:
            report = builder.build_student_report(results, historical_data)
            return report.model_dump()
        
        elif input_data.role == UserRole.PARENT:
            report = builder.build_parent_report(results, historical_data)
            return report.model_dump()
        
        elif input_data.role == UserRole.SCHOOL_ADMIN:
            # For school reports, results should contain cohort data
            cohort_results = results.get("cohort_results", [])
            historical_trends = results.get("historical_trends", [])
            report = builder.build_school_report(cohort_results, historical_trends)
            return report.model_dump()
        
        else:
            raise InvalidRoleError(
                message=f"Unsupported role: {input_data.role}",
                trace_id=input_data.trace_id,
                context={"role": str(input_data.role)},
            )
    
    def _aggregate_trends(
        self,
        input_data: ReportingInput,
        report_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]] | None,
    ) -> Dict[str, Any]:
        """
        Step 5: Aggregate historical trends (if requested).
        
        Args:
            input_data: Validated input
            report_data: Current report data
            historical_data: Historical performance data
            
        Returns:
            Report data with trends added
        """
        if not historical_data:
            return report_data
        
        analyzer = TrendAnalyzerService(trace_id=input_data.trace_id)
        
        # Calculate overall trends
        trend_analysis = analyzer.analyze_longitudinal_performance(
            historical_data
        )
        
        # Add trend data to report
        report_data["trend_analysis"] = trend_analysis
        
        # Calculate metrics
        metrics = analyzer.calculate_trend_metrics(historical_data)
        report_data["trend_metrics"] = metrics
        
        return report_data
    
    def _render_exports(
        self,
        input_data: ReportingInput,
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Step 6: Render exports (PDF / CSV / JSON).
        
        Args:
            input_data: Validated input
            report_data: Complete report data
            
        Returns:
            Dictionary of export metadata (download URLs, sizes)
            
        Raises:
            ExportFailureError: If export fails
        """
        export_service = ExportService(trace_id=input_data.trace_id)
        pdf_service = PDFRendererService(trace_id=input_data.trace_id)
        
        exports = []
        export_metadata = {}
        
        # Generate and persist exports based on requested format
        if input_data.export_format == ExportFormat.PDF:
            try:
                # Generate PDF content
                pdf_bytes = pdf_service.render_report_to_pdf(
                    report_data=report_data,
                    report_type=input_data.role.value,
                    watermark_text=f"Generated: {datetime.now().isoformat()}",
                )
                
                # Persist to Azure Blob Storage
                azure_metadata = self.azure_storage.save_export(
                    content=pdf_bytes,
                    content_type="application/pdf",
                    user_id=str(input_data.user_id),
                    trace_id=str(input_data.trace_id),
                    export_type="pdf",
                    filename=f"report_{input_data.trace_id}.pdf",
                )
                
                # Add to exports if successfully persisted
                if azure_metadata:
                    exports.append({
                        "type": "pdf",
                        "download_url": azure_metadata["download_url"],
                        "content_type": azure_metadata["content_type"],
                        "size_bytes": azure_metadata["size_bytes"],
                    })
                else:
                    self.logger.warning(
                        f"[{input_data.trace_id}] PDF export failed to persist to Azure",
                        extra={"trace_id": str(input_data.trace_id)}
                    )
            except Exception as e:
                self.logger.error(
                    f"[{input_data.trace_id}] PDF export generation failed",
                    extra={"trace_id": str(input_data.trace_id), "error": str(e)},
                    exc_info=True
                )
        
        if input_data.export_format == ExportFormat.CSV:
            try:
                # Generate CSV content
                csv_string = export_service.export_to_csv(
                    report_data=report_data,
                    report_type=input_data.role.value,
                )
                csv_bytes = csv_string.encode('utf-8')
                
                # Persist to Azure Blob Storage
                azure_metadata = self.azure_storage.save_export(
                    content=csv_bytes,
                    content_type="text/csv",
                    user_id=str(input_data.user_id),
                    trace_id=str(input_data.trace_id),
                    export_type="csv",
                    filename=f"report_{input_data.trace_id}.csv",
                )
                
                # Add to exports if successfully persisted
                if azure_metadata:
                    exports.append({
                        "type": "csv",
                        "download_url": azure_metadata["download_url"],
                        "content_type": azure_metadata["content_type"],
                        "size_bytes": azure_metadata["size_bytes"],
                    })
                else:
                    self.logger.warning(
                        f"[{input_data.trace_id}] CSV export failed to persist to Azure",
                        extra={"trace_id": str(input_data.trace_id)}
                    )
            except Exception as e:
                self.logger.error(
                    f"[{input_data.trace_id}] CSV export generation failed",
                    extra={"trace_id": str(input_data.trace_id), "error": str(e)},
                    exc_info=True
                )
        
        if input_data.export_format == ExportFormat.JSON:
            try:
                # Generate JSON content
                json_string = export_service.export_to_json(report_data)
                json_bytes = json_string.encode('utf-8')
                
                # Persist to Azure Blob Storage
                azure_metadata = self.azure_storage.save_export(
                    content=json_bytes,
                    content_type="application/json",
                    user_id=str(input_data.user_id),
                    trace_id=str(input_data.trace_id),
                    export_type="json",
                    filename=f"report_{input_data.trace_id}.json",
                )
                
                # Add to exports if successfully persisted
                if azure_metadata:
                    exports.append({
                        "type": "json",
                        "download_url": azure_metadata["download_url"],
                        "content_type": azure_metadata["content_type"],
                        "size_bytes": azure_metadata["size_bytes"],
                    })
                else:
                    self.logger.warning(
                        f"[{input_data.trace_id}] JSON export failed to persist to Azure",
                        extra={"trace_id": str(input_data.trace_id)}
                    )
            except Exception as e:
                self.logger.error(
                    f"[{input_data.trace_id}] JSON export generation failed",
                    extra={"trace_id": str(input_data.trace_id), "error": str(e)},
                    exc_info=True
                )
        
        # Return exports metadata (empty array if all failed)
        return {"exports": exports}
    
    def _generate_visualizations(
        self,
        input_data: ReportingInput,
        report_data: Dict[str, Any],
    ) -> List[VisualSection]:
        """
        Step 7: Generate visualization sections.
        
        Args:
            input_data: Validated input
            report_data: Complete report data
            
        Returns:
            List of VisualSection objects
        """
        mapper = VisualizationMapperService(trace_id=input_data.trace_id)
        
        visual_sections = mapper.generate_visual_sections(
            report_data=report_data,
            role=input_data.role.value,
        )
        
        return visual_sections
    
    def _build_output(
        self,
        input_data: ReportingInput,
        report_data: Dict[str, Any],
        visual_sections: List[VisualSection],
        export_metadata: Dict[str, Any],
    ) -> ReportingOutput:
        """
        Step 8: Build the final output.
        
        Args:
            input_data: Validated input
            report_data: Complete report data
            visual_sections: Visualization sections
            export_metadata: Export metadata with download URLs
            
        Returns:
            ReportingOutput with confidence = 1.0
        """
        # Map role to report type
        role_to_type = {
            UserRole.STUDENT: ReportType.STUDENT,
            UserRole.PARENT: ReportType.PARENT,
            UserRole.SCHOOL_ADMIN: ReportType.SCHOOL,
        }
        
        return ReportingOutput(
            report_id=uuid4(),
            report_type=role_to_type[input_data.role],
            generated_at=datetime.now(),
            data_payload=report_data,
            visual_sections=visual_sections,
            export_links=export_metadata,  # Now contains {"exports": [...]}
            confidence=1.0,  # Always deterministic
            trace_id=input_data.trace_id,
            metadata={
                "engine_name": self.ENGINE_NAME,
                "engine_version": self.ENGINE_VERSION,
                "engine_type": self.ENGINE_TYPE,
                "reporting_scope": input_data.reporting_scope.value,
                "export_format": input_data.export_format.value,
                "feature_flags": input_data.feature_flags_snapshot,
            },
        )
    
    def _log_step(self, trace_id: UUID, step: int, message: str) -> None:
        """Log a step in the execution flow."""
        self.logger.info(
            f"[{trace_id}] Step {step}/9: {message}",
            extra={
                "trace_id": str(trace_id),
                "step": step,
                "engine": self.ENGINE_NAME,
            }
        )
