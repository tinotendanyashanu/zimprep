"""Mark allocation validator.

Validates mark consistency across sections and paper.
"""

import logging
from typing import List

from app.engines.exam_structure.schemas.section import SectionDefinition
from app.engines.exam_structure.errors import MarkAllocationMismatchError

logger = logging.getLogger(__name__)


def validate_mark_consistency(
    sections: List[SectionDefinition],
    paper_total_marks: int,
    trace_id: str,
) -> None:
    """Validate mark allocation consistency.
    
    Checks:
    - Each section's total_marks = num_questions × marks_per_question
    - Sum of all section totals = paper total marks
    
    Args:
        sections: List of section definitions
        paper_total_marks: Expected total marks for the paper
        trace_id: Request trace ID for logging
        
    Raises:
        MarkAllocationMismatchError: Mark allocation inconsistent
    """
    # Validate each section's internal consistency
    for section in sections:
        expected_total = section.num_questions * section.marks_per_question
        
        if section.total_marks != expected_total:
            raise MarkAllocationMismatchError(
                message=(
                    f"Section '{section.section_id}' mark mismatch: "
                    f"total_marks={section.total_marks} but "
                    f"num_questions × marks_per_question = {expected_total}"
                ),
                trace_id=trace_id,
                metadata={
                    "section_id": section.section_id,
                    "total_marks": section.total_marks,
                    "num_questions": section.num_questions,
                    "marks_per_question": section.marks_per_question,
                    "expected_total": expected_total,
                },
            )
    
    # Compute sum of section totals
    sections_sum = sum(s.total_marks for s in sections)
    
    # Validate against paper total
    if sections_sum != paper_total_marks:
        section_breakdown = {s.section_id: s.total_marks for s in sections}
        
        raise MarkAllocationMismatchError(
            message=(
                f"Paper total marks mismatch: "
                f"sum of sections={sections_sum} but "
                f"paper total_marks={paper_total_marks}"
            ),
            trace_id=trace_id,
            metadata={
                "paper_total_marks": paper_total_marks,
                "sections_sum": sections_sum,
                "section_breakdown": section_breakdown,
            },
        )
    
    logger.info(
        "Mark consistency validation passed",
        extra={
            "trace_id": trace_id,
            "paper_total_marks": paper_total_marks,
            "num_sections": len(sections),
        }
    )
