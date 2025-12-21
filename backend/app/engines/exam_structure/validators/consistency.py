"""Section consistency validator.

Validates section definition structure and completeness.
"""

import logging
from typing import List

from app.engines.exam_structure.schemas.section import SectionDefinition, QuestionType
from app.engines.exam_structure.errors import SectionDefinitionError

logger = logging.getLogger(__name__)


def validate_section_consistency(
    sections: List[SectionDefinition],
    trace_id: str,
) -> None:
    """Validate section definitions for consistency.
    
    Checks:
    - At least one section exists
    - No duplicate section IDs
    - All required fields present
    - Question types valid
    - Positive integers for counts and marks
    
    Args:
        sections: List of section definitions
        trace_id: Request trace ID for logging
        
    Raises:
        SectionDefinitionError: Section definitions invalid
    """
    if not sections:
        raise SectionDefinitionError(
            message="Paper must have at least one section",
            trace_id=trace_id,
            metadata={"num_sections": 0},
        )
    
    # Check for duplicate section IDs
    section_ids = [s.section_id for s in sections]
    if len(section_ids) != len(set(section_ids)):
        duplicates = [sid for sid in section_ids if section_ids.count(sid) > 1]
        raise SectionDefinitionError(
            message=f"Duplicate section IDs detected: {duplicates}",
            trace_id=trace_id,
            metadata={"duplicate_ids": duplicates},
        )
    
    # Validate each section
    for section in sections:
        # Pydantic already validates required fields and types
        # Additional business logic validation
        
        # Verify question type is valid (enum check)
        if not isinstance(section.question_type, QuestionType):
            raise SectionDefinitionError(
                message=f"Invalid question type for section '{section.section_id}': {section.question_type}",
                trace_id=trace_id,
                metadata={
                    "section_id": section.section_id,
                    "invalid_type": str(section.question_type),
                },
            )
        
        # Verify positive values (Pydantic gt=0 should catch this, but double-check)
        if section.num_questions <= 0:
            raise SectionDefinitionError(
                message=f"Section '{section.section_id}' has invalid num_questions: {section.num_questions}",
                trace_id=trace_id,
                metadata={
                    "section_id": section.section_id,
                    "num_questions": section.num_questions,
                },
            )
        
        if section.marks_per_question <= 0:
            raise SectionDefinitionError(
                message=f"Section '{section.section_id}' has invalid marks_per_question: {section.marks_per_question}",
                trace_id=trace_id,
                metadata={
                    "section_id": section.section_id,
                    "marks_per_question": section.marks_per_question,
                },
            )
        
        if section.total_marks <= 0:
            raise SectionDefinitionError(
                message=f"Section '{section.section_id}' has invalid total_marks: {section.total_marks}",
                trace_id=trace_id,
                metadata={
                    "section_id": section.section_id,
                    "total_marks": section.total_marks,
                },
            )
    
    logger.info(
        "Section consistency validation passed",
        extra={
            "trace_id": trace_id,
            "num_sections": len(sections),
        }
    )
