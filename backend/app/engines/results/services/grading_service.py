"""Grading service for the Results Engine.

Resolves final letter grades using subject-specific grade boundaries.
All grade resolution is data-driven and deterministic.
"""

import logging

from app.engines.results.schemas.grading import GradingScale

logger = logging.getLogger(__name__)


class GradingService:
    """Service for grade resolution and pass/fail determination.
    
    Grade boundaries are data-driven (no hard-coded grades).
    Supports subject-specific grading scales.
    Deterministic: same input always produces same grade.
    """
    
    @classmethod
    def resolve_grade(
        cls,
        total_marks: float,
        grading_scale: GradingScale
    ) -> str:
        """Resolve the letter grade for a given total mark.
        
        Uses the grade boundaries from the grading scale to determine
        the appropriate letter grade.
        
        Args:
            total_marks: Total weighted marks achieved
            grading_scale: Subject-specific grading scale
            
        Returns:
            Letter grade (e.g., 'A*', 'A', 'B', 'C', 'D', 'E', 'U')
        """
        grade = grading_scale.resolve_grade(total_marks)
        
        logger.info(
            "Resolved grade '%s' for %.2f marks (subject: %s, syllabus: %s)",
            grade,
            total_marks,
            grading_scale.subject_code,
            grading_scale.syllabus_version
        )
        
        return grade
    
    @classmethod
    def determine_pass_status(
        cls,
        total_marks: float,
        grading_scale: GradingScale
    ) -> bool:
        """Determine if the total marks constitute a pass.
        
        Args:
            total_marks: Total weighted marks achieved
            grading_scale: Subject-specific grading scale
            
        Returns:
            True if marks meet or exceed pass threshold
        """
        is_passing = grading_scale.is_passing(total_marks)
        
        logger.info(
            "Pass status: %s (%.2f marks, pass threshold: %.2f)",
            "PASS" if is_passing else "FAIL",
            total_marks,
            grading_scale.pass_mark
        )
        
        return is_passing
    
    @classmethod
    def get_grade_info(
        cls,
        total_marks: float,
        grading_scale: GradingScale
    ) -> dict:
        """Get comprehensive grade information.
        
        Args:
            total_marks: Total weighted marks achieved
            grading_scale: Subject-specific grading scale
            
        Returns:
            Dictionary with grade, pass_status, and boundary info
        """
        grade = cls.resolve_grade(total_marks, grading_scale)
        pass_status = cls.determine_pass_status(total_marks, grading_scale)
        
        # Find the boundary that was used
        boundary_info = None
        for boundary in grading_scale.boundaries:
            if boundary.grade == grade:
                boundary_info = {
                    "min_marks": boundary.min_marks,
                    "max_marks": boundary.max_marks,
                    "marks_above_minimum": total_marks - boundary.min_marks
                }
                break
        
        return {
            "grade": grade,
            "pass_status": pass_status,
            "total_marks": total_marks,
            "pass_mark": grading_scale.pass_mark,
            "boundary_info": boundary_info
        }
