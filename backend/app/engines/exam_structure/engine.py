"""Exam Structure Engine

Main orchestrator-facing entry point for exam structure resolution.
"""

import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import ValidationError
from pymongo import MongoClient

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.exam_structure.schemas import (
    ExamStructureInput,
    ExamStructureOutput,
    SectionDefinition,
    QuestionType,
)
from app.engines.exam_structure.repository import (
    SubjectRepository,
    SyllabusRepository,
    PaperRepository,
    ScheduleRepository,
)
from app.engines.exam_structure.validators import (
    validate_section_consistency,
    validate_mark_consistency,
)
from app.engines.exam_structure.errors import (
    ExamStructureException,
    SubjectNotFoundError,
    InvalidSyllabusVersionError,
    PaperNotFoundError,
    SectionDefinitionError,
    MarkAllocationMismatchError,
    DatabaseError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "exam_structure"
ENGINE_VERSION = "1.0.0"


class ExamStructureEngine:
    """Production-grade exam structure engine for ZimPrep.
    
    Defines the official ZIMSEC exam blueprint according to standards.
    Fails closed on any inconsistency or error.
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize engine with repository dependencies.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
        """
        self.subject_repo = SubjectRepository(mongo_client)
        self.syllabus_repo = SyllabusRepository(mongo_client)
        self.paper_repo = PaperRepository(mongo_client)
        self.schedule_repo = ScheduleRepository(mongo_client)
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext,
    ) -> EngineResponse[ExamStructureOutput]:
        """Execute exam structure resolution engine.
        
        Implements the mandatory 10-step execution flow:
        1. Validate input contract
        2. Load subject definition
        3. Load syllabus definition
        4. Load paper definition
        5. Load section layout
        6. Validate section definitions
        7. Validate total mark consistency
        8. Compute section totals
        9. Generate deterministic structure hash
        10. Return frozen output
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ExamStructureOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        try:
            # Step 1: Validate input contract
            logger.info(
                "Exam Structure Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            # Check if this is a dashboard request (fetch upcoming exams only)
            is_dashboard_request = payload.get("dashboard_mode", False)  
            
            if is_dashboard_request:
                # Dashboard mode: fetch upcoming exams without exam structure
                candidate_id = payload.get("candidate_id")
                if not candidate_id:
                    logger.warning("Dashboard request missing candidate_id", extra={"trace_id": trace_id})
                    return self._build_dashboard_only_response([], trace_id, start_time)
                
                upcoming_exams = await self._fetch_upcoming_exams(
                    candidate_id=candidate_id,
                    cohort_id=payload.get("cohort_id"),
                    school_id=payload.get("school_id"),
                    trace_id=trace_id,
                    limit=payload.get("limit", 10),
                    candidate_timezone=payload.get("timezone", "Africa/Harare"),  # NEW
                )
                
                return self._build_dashboard_only_response(upcoming_exams, trace_id, start_time)
            
            # Standard exam structure resolution
            try:
                input_data = ExamStructureInput(**payload)
            except ValidationError as e:
                logger.error(
                    "Input validation failed",
                    extra={"trace_id": trace_id, "errors": e.errors()},
                )
                return self._build_error_response(
                    error_message=f"Input validation failed: {str(e)}",
                    trace_id=trace_id,
                    start_time=start_time,
                )
            
            # Execute core logic
            output = await self._execute_structure_resolution(
                input_data=input_data,
                trace_id=trace_id,
            )
            
            # Build success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time,
            )
            
        except ExamStructureException as e:
            # Known engine errors
            logger.error(
                "Engine error",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error_message": e.message,
                    "metadata": e.metadata,
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=e.message,
                trace_id=trace_id,
                start_time=start_time,
            )
        except Exception as e:
            # Unexpected errors - fail closed
            logger.error(
                "Unexpected engine error",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time,
            )
    
    async def _execute_structure_resolution(
        self,
        input_data: ExamStructureInput,
        trace_id: str,
    ) -> ExamStructureOutput:
        """Execute core structure resolution logic.
        
        Steps 2-10 of the mandatory execution flow.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Returns:
            ExamStructureOutput
        """
        # Step 2: Load subject definition
        subject = await self.subject_repo.get_subject(
            subject_code=input_data.subject_code,
            trace_id=trace_id,
        )
        
        # Step 3: Load syllabus definition
        syllabus = await self.syllabus_repo.get_syllabus(
            subject_code=input_data.subject_code,
            syllabus_version=input_data.syllabus_version,
            trace_id=trace_id,
        )
        
        # Step 4: Load paper definition
        paper = await self.paper_repo.get_paper(
            subject_code=input_data.subject_code,
            syllabus_version=input_data.syllabus_version,
            paper_code=input_data.paper_code,
            trace_id=trace_id,
        )
        
        # Step 5: Load section layout
        paper_id = str(paper["_id"])
        sections_raw = await self.paper_repo.get_sections(
            paper_id=paper_id,
            trace_id=trace_id,
        )
        
        # Convert to Pydantic models
        sections = self._parse_sections(sections_raw, trace_id)
        
        # Step 6: Validate section definitions
        validate_section_consistency(sections, trace_id)
        
        # Step 7: Validate total mark consistency
        paper_total_marks = paper["total_marks"]
        validate_mark_consistency(sections, paper_total_marks, trace_id)
        
        # Step 8: Compute section totals (already in sections, just create breakdown)
        mark_breakdown = {s.section_id: s.total_marks for s in sections}
        
        # Step 9: Generate deterministic structure hash
        structure_hash = self._generate_structure_hash(
            subject_code=input_data.subject_code,
            syllabus_version=input_data.syllabus_version,
            paper_code=input_data.paper_code,
            sections=sections,
            total_marks=paper_total_marks,
        )
        
        # Step 10: Fetch upcoming exams if requested (dashboard context)
        upcoming_exams = []
        # Check if this is a dashboard request with upcoming exams
        # This will be handled by checking payload in run() method
        
        # Step 11: Return frozen output
        output = ExamStructureOutput(
            subject_code=input_data.subject_code,
            subject_name=subject["name"],
            syllabus_version=input_data.syllabus_version,
            paper_code=input_data.paper_code,
            paper_name=paper["paper_name"],
            duration_minutes=paper["duration_minutes"],
            total_marks=paper_total_marks,
            sections=sections,
            mark_breakdown=mark_breakdown,
            source="ZIMSEC",
            structure_hash=structure_hash,
            confidence=1.0,  # Official verified data
            upcoming_exams=upcoming_exams,
        )
        
        execution_time_ms = int((datetime.utcnow() - datetime.fromisoformat(trace_id.split('-')[0])).total_seconds() * 1000) if '-' in trace_id else 0
        
        logger.info(
            "Structure resolution completed successfully",
            extra={
                "trace_id": trace_id,
                "subject_code": input_data.subject_code,
                "paper_code": input_data.paper_code,
                "structure_hash": structure_hash,
                "num_sections": len(sections),
                "total_marks": paper_total_marks,
            }
        )
        
        return output
    
    def _parse_sections(
        self,
        sections_raw: list[Dict[str, Any]],
        trace_id: str,
    ) -> list[SectionDefinition]:
        """Parse raw section documents to SectionDefinition models.
        
        Args:
            sections_raw: Raw MongoDB documents
            trace_id: Trace ID
            
        Returns:
            List of validated SectionDefinition objects
            
        Raises:
            SectionDefinitionError: Section parsing failed
        """
        sections = []
        
        for section_doc in sections_raw:
            try:
                section = SectionDefinition(
                    section_id=section_doc["section_id"],
                    section_name=section_doc["section_name"],
                    question_type=QuestionType(section_doc["question_type"]),
                    num_questions=section_doc["num_questions"],
                    marks_per_question=section_doc["marks_per_question"],
                    total_marks=section_doc.get("total_marks", 
                                                section_doc["num_questions"] * section_doc["marks_per_question"]),
                    is_compulsory=section_doc.get("is_compulsory", True),
                )
                sections.append(section)
            except (KeyError, ValueError, ValidationError) as e:
                logger.error(
                    "Failed to parse section",
                    extra={
                        "trace_id": trace_id,
                        "section_doc": section_doc,
                        "error": str(e),
                    },
                    exc_info=True
                )
                raise SectionDefinitionError(
                    message=f"Failed to parse section: {str(e)}",
                    trace_id=trace_id,
                    metadata={"section_doc": section_doc},
                )
        
        return sections
    
    def _generate_structure_hash(
        self,
        subject_code: str,
        syllabus_version: str,
        paper_code: str,
        sections: list[SectionDefinition],
        total_marks: int,
    ) -> str:
        """Generate deterministic SHA-256 hash of structure.
        
        Used for version tracking and change detection.
        
        Args:
            subject_code: Subject code
            syllabus_version: Syllabus version
            paper_code: Paper code
            sections: Section definitions
            total_marks: Total marks
            
        Returns:
            64-character hex SHA-256 hash
        """
        # Create canonical string representation
        parts = [
            subject_code,
            syllabus_version,
            paper_code,
            str(total_marks),
        ]
        
        # Add each section in deterministic order
        for section in sorted(sections, key=lambda s: s.section_id):
            parts.extend([
                section.section_id,
                section.section_name,
                section.question_type.value,
                str(section.num_questions),
                str(section.marks_per_question),
                str(section.total_marks),
            ])
        
        # Compute hash
        canonical = "|".join(parts)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    
    async def _fetch_upcoming_exams(
        self,
        candidate_id: str,
        cohort_id: Optional[str],
        school_id: Optional[str],
        trace_id: str,
        limit: int = 10,
        candidate_timezone: str = "Africa/Harare",  # NEW: Timezone parameter
    ) -> list[Dict[str, Any]]:
        """Fetch upcoming scheduled exams for a candidate.
        
        Args:
            candidate_id: Candidate ID
            cohort_id: Optional cohort ID
            school_id: Optional school ID
            trace_id: Trace ID for logging
            limit: Maximum exams to return
            candidate_timezone: Candidate's local timezone (IANA format)
            
        Returns:
            List of formatted upcoming exam objects with timezone conversion
        """
        try:
            # Import  timezone utilities
            from app.utils.timezone_helper import format_exam_time, get_time_until_exam
            
            schedules = await self.schedule_repo.get_upcoming_exams(
                candidate_id=candidate_id,
                cohort_id=cohort_id,
                school_id=school_id,
                limit=limit,
            )
            
            # Format for dashboard consumption with timezone conversion
            upcoming_exams = []
            for schedule in schedules:
                scheduled_date = schedule.get("scheduled_date")
                
                # Format time with timezone conversion
                time_info = format_exam_time(scheduled_date, candidate_timezone)
                
                # Calculate time remaining
                time_remaining = get_time_until_exam(scheduled_date)
                
                upcoming_exams.append({
                    "exam_id": schedule.get("exam_id"),
                    "subject": schedule.get("subject_name"),
                    "paper": schedule.get("paper_name"),
                    "scheduled_date": time_info,  # Now includes UTC, local, timezone, display
                    "time_remaining": time_remaining,  # Days, hours, urgency level
                    "duration_minutes": schedule.get("duration_minutes"),
                    "status": schedule.get("status"),
                })
            
            logger.info(
                f"Fetched {len(upcoming_exams)} upcoming exams",
                extra={
                    "trace_id": trace_id,
                    "candidate_id": candidate_id,
                    "num_exams": len(upcoming_exams),
                    "timezone": candidate_timezone,
                }
            )
            
            return upcoming_exams
        
        except Exception as e:
            logger.error(
                f"Error fetching upcoming exams: {e}",
                extra={
                    "trace_id": trace_id,
                    "candidate_id": candidate_id,
                    "error": str(e),
                },
                exc_info=True
            )
            return []
    
    def _build_dashboard_only_response(
        self,
        upcoming_exams: list[Dict[str, Any]],
        trace_id: str,
        start_time: datetime,
    ) -> EngineResponse:
        """Build response for dashboard-only requests (no exam structure).
        
        Args:
            upcoming_exams: List of upcoming exams
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with only upcoming_exams field
        """
        # Create minimal output with just upcoming exams
        # This is used when the dashboard pipeline calls exam_structure
        # but doesn't need actual exam structure data
        output_data = {
            "upcoming_exams": upcoming_exams
        }
        
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0,
        )
        
        return EngineResponse(
            success=True,
            data=output_data,
            error=None,
            trace=trace,
        )

    
    def _build_response(
        self,
        output: ExamStructureOutput,
        trace_id: str,
        start_time: datetime,
    ) -> EngineResponse[ExamStructureOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=output.confidence,
        )
        
        return EngineResponse[ExamStructureOutput](
            success=True,
            data=output,
            error=None,
            trace=trace,
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime,
    ) -> EngineResponse[ExamStructureOutput]:
        """Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with error
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0,  # Zero confidence on error
        )
        
        return EngineResponse[ExamStructureOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace,
        )
