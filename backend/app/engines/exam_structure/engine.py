"""Exam Structure Engine

DERIVATION-BASED ARCHITECTURE (ACTION 3)
=========================================

This engine derives ALL exam structure from the canonical_questions collection.

NO phantom collections are queried:
- subjects ❌ (does not exist)
- syllabuses ❌ (does not exist)
- papers ❌ (does not exist)
- paper_sections ❌ (does not exist)

CANONICAL SOURCE OF TRUTH:
- canonical_questions → subjects, levels, years, papers, question counts

DERIVATION LOGIC:
- subjects = distinct("subject")
- levels = distinct("level")
- years = distinct("year")
- papers = distinct("paper")
- question_count = count per (subject, year, paper)
- exam_metadata = DERIVED (duration/marks use fallback values)

All queries are deterministic and derived from ingestion data.
"""

import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import ValidationError
from pymongo import MongoClient

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext
from app.config.knowledge_contract import CANONICAL_QUESTIONS

from app.engines.exam_structure.schemas import (
    ExamStructureInput,
    ExamStructureOutput,
    SectionDefinition,
    QuestionType,
)
from app.engines.exam_structure.repository import ScheduleRepository
from app.engines.exam_structure.errors import (
    ExamStructureException,
    NoSubjectsFoundError,
    NoPapersFoundError,
    NoQuestionsFoundError,
    DatabaseError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "exam_structure"
ENGINE_VERSION = "2.0.0"  # ACTION 3: Derivation-based architecture


# Fallback metadata for derived exams (since we don't have authoritative data)
DEFAULT_EXAM_DURATION_MINUTES = 120
DEFAULT_MARKS_PER_QUESTION = 10
DEFAULT_PAPER_NAMES = {
    "1": "Paper 1",
    "2": "Paper 2",
    "3": "Paper 3",
}


class ExamStructureEngine:
    """Production-grade exam structure engine for ZimPrep.
    
    DERIVATION-BASED (ACTION 3):
    - ALL structure derived from canonical_questions
    - NO phantom collections queried
    - Fail-fast on empty data
    - Explicit error messages with trace_id
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize engine with MongoDB client.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
        """
        if mongo_client is None:
            from app.config.database import get_database
            db = get_database()
            self.mongo_client = db.client
            self._db_name = db.name
        else:
            self.mongo_client = mongo_client
            self._db_name = "zimprep"
        self.schedule_repo = ScheduleRepository(self.mongo_client)
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext,
    ) -> EngineResponse[ExamStructureOutput]:
        """Execute exam structure resolution engine.
        
        DERIVATION FLOW:
        1. Validate input contract
        2. Derive structure from canonical_questions
        3. Validate derived data is non-empty
        4. Return frozen output with confidence < 1.0 (derived data)
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ExamStructureOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        try:
            logger.info(
                "Exam Structure Engine execution started (DERIVATION MODE)",
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
                    candidate_timezone=payload.get("timezone", "Africa/Harare"),
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
            
            # Execute core derivation logic
            output = await self._execute_structure_derivation(
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
    
    async def _execute_structure_derivation(
        self,
        input_data: ExamStructureInput,
        trace_id: str,
    ) -> ExamStructureOutput:
        """Execute core structure derivation logic.
        
        DERIVATION STEPS:
        1. Verify MongoDB connection
        2. Derive subject metadata
        3. Derive paper metadata
        4. Count questions
        5. Generate fallback exam metadata
        6. Return derived structure
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Returns:
            ExamStructureOutput with derived data
            
        Raises:
            NoQuestionsFoundError: No questions found for paper
            DatabaseError: MongoDB connection failed
        """
        if not self.mongo_client:
            raise DatabaseError(
                message="MongoDB client not initialized",
                trace_id=trace_id,
                metadata={"subject_code": input_data.subject_code},
            )
        
        db = self.mongo_client[self._db_name]
        collection = db[CANONICAL_QUESTIONS]
        
        # Derive subject name (fallback to subject_code if not derivable)
        subject_name = input_data.subject_code  # Fallback
        
        # Derive paper name (use default mapping or fallback)
        paper_name = DEFAULT_PAPER_NAMES.get(
            input_data.paper_code,
            f"Paper {input_data.paper_code}"
        )
        
        # Count questions for this exact (subject, level, year, paper) combination
        question_count = collection.count_documents({
            "subject": input_data.subject_code,
            "level": input_data.syllabus_version,
            "year": str(input_data.year) if hasattr(input_data, 'year') else None,
            "paper": input_data.paper_code,
        })
        
        # FAIL-FAST: No questions found
        if question_count == 0:
            logger.error(
                "No questions found for paper",
                extra={
                    "trace_id": trace_id,
                    "subject": input_data.subject_code,
                    "level": input_data.syllabus_version,
                    "paper": input_data.paper_code,
                }
            )
            raise NoQuestionsFoundError(
                message=f"No questions found for {input_data.subject_code} "
                        f"(level: {input_data.syllabus_version}, paper: {input_data.paper_code}). "
                        f"Cannot create exam with empty question set.",
                trace_id=trace_id,
                metadata={
                    "subject": input_data.subject_code,
                    "level": input_data.syllabus_version,
                    "paper": input_data.paper_code,
                    "question_count": 0,
                },
            )
        
        # Derive exam metadata (using fallback values)
        duration_minutes = DEFAULT_EXAM_DURATION_MINUTES
        total_marks = question_count * DEFAULT_MARKS_PER_QUESTION
        
        # Create single section (since we don't have section definitions)
        sections = [
            SectionDefinition(
                section_id="A",
                section_name="Section A",
                question_type=QuestionType.STRUCTURED,
                num_questions=question_count,
                marks_per_question=DEFAULT_MARKS_PER_QUESTION,
                total_marks=total_marks,
                is_compulsory=True,
            )
        ]
        
        # Generate structure hash
        structure_hash = self._generate_structure_hash(
            subject_code=input_data.subject_code,
            syllabus_version=input_data.syllabus_version,
            paper_code=input_data.paper_code,
            sections=sections,
            total_marks=total_marks,
        )
        
        logger.info(
            "Structure derivation completed successfully",
            extra={
                "trace_id": trace_id,
                "subject_code": input_data.subject_code,
                "paper_code": input_data.paper_code,
                "structure_hash": structure_hash,
                "question_count": question_count,
                "total_marks": total_marks,
                "derivation_mode": "canonical_questions",
            }
        )
        
        # Return derived output with confidence < 1.0 (since metadata is inferred)
        output = ExamStructureOutput(
            subject_code=input_data.subject_code,
            subject_name=subject_name,
            syllabus_version=input_data.syllabus_version,
            paper_code=input_data.paper_code,
            paper_name=paper_name,
            duration_minutes=duration_minutes,
            total_marks=total_marks,
            sections=sections,
            mark_breakdown={"A": total_marks},
            source="DERIVED",  # Indicate this is derived, not authoritative
            structure_hash=structure_hash,
            confidence=0.8,  # Lower confidence for derived data
            upcoming_exams=[],
        )
        
        return output
    
    async def list_available_subjects(self, trace_id: str) -> List[Dict[str, Any]]:
        """List all available subjects from canonical_questions.
        
        Used by dashboard to show subjects student can practice.
        
        Args:
            trace_id: Trace ID for logging
            
        Returns:
            List of subject dictionaries with metadata
            
        Raises:
            NoSubjectsFoundError: No subjects found in canonical_questions
            DatabaseError: MongoDB connection failed
        """
        if not self.mongo_client:
            raise DatabaseError(
                message="MongoDB client not initialized",
                trace_id=trace_id,
                metadata={},
            )
        
        db = self.mongo_client[self._db_name]
        collection = db[CANONICAL_QUESTIONS]
        
        # Derive distinct subjects
        subjects = collection.distinct("subject")
        
        # FAIL-FAST: No subjects found
        if not subjects:
            logger.error(
                "No subjects found in canonical_questions",
                extra={"trace_id": trace_id}
            )
            raise NoSubjectsFoundError(
                message="No subjects found in canonical_questions collection. "
                        "Ingestion data may not be loaded.",
                trace_id=trace_id,
                metadata={"collection": CANONICAL_QUESTIONS},
            )
        
        # Build subject list with metadata
        subject_list = []
        for subject in subjects:
            # Count questions for this subject
            question_count = collection.count_documents({"subject": subject})
            
            # Get available years
            years = collection.distinct("year", {"subject": subject})
            
            subject_list.append({
                "subject_code": subject,
                "subject_name": subject,  # Fallback to code
                "question_count": question_count,
                "available_years": sorted(years, reverse=True),
            })
        
        logger.info(
            f"Listed {len(subject_list)} subjects from canonical_questions",
            extra={"trace_id": trace_id, "num_subjects": len(subject_list)}
        )
        
        return subject_list
    
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
        candidate_timezone: str = "Africa/Harare",
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
            # Import timezone utilities
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
                    "scheduled_date": time_info,
                    "time_remaining": time_remaining,
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
