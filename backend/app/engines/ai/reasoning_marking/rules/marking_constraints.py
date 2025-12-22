"""Marking constraints and business rules.

These rules are enforced programmatically (not by LLM) to ensure
compliance with exam board requirements.
"""

from typing import List
from app.engines.ai.reasoning_marking.schemas import (
    RubricPoint,
    AwardedPoint,
    ReasoningMarkingOutput,
)
from app.engines.ai.reasoning_marking.errors import ConstraintViolationError


class MarkingConstraints:
    """Business rules for marking validation.
    
    These constraints are HARD requirements that cannot be violated.
    """
    
    @staticmethod
    def validate_max_marks_not_exceeded(
        awarded_marks: float,
        max_marks: int,
        trace_id: str
    ) -> None:
        """Ensure awarded marks do not exceed maximum.
        
        This is a CRITICAL constraint - no exceptions allowed.
        
        Args:
            awarded_marks: Total marks to be awarded
            max_marks: Maximum possible marks
            trace_id: Trace ID for error reporting
            
        Raises:
            ConstraintViolationError: If constraint violated
        """
        if awarded_marks > max_marks:
            raise ConstraintViolationError(
                trace_id=trace_id,
                constraint="MAX_MARKS_LIMIT",
                details=f"Attempted to award {awarded_marks} marks but max is {max_marks}"
            )
    
    @staticmethod
    def validate_rubric_point_exists(
        point_id: str,
        official_rubric: List[RubricPoint],
        trace_id: str
    ) -> RubricPoint:
        """Ensure awarded point exists in official rubric.
        
        Args:
            point_id: Point ID to validate
            official_rubric: Official rubric points
            trace_id: Trace ID for error reporting
            
        Returns:
            RubricPoint: The validated rubric point
            
        Raises:
            ConstraintViolationError: If point not in rubric
        """
        for rubric_point in official_rubric:
            if rubric_point.point_id == point_id:
                return rubric_point
        
        raise ConstraintViolationError(
            trace_id=trace_id,
            constraint="RUBRIC_POINT_EXISTS",
            details=f"Point {point_id} not found in official rubric"
        )
    
    @staticmethod
    def validate_evidence_citation(
        awarded_point: AwardedPoint,
        trace_id: str
    ) -> None:
        """Ensure every awarded point cites evidence.
        
        Args:
            awarded_point: Point to validate
            trace_id: Trace ID for error reporting
            
        Raises:
            ConstraintViolationError: If no evidence cited
        """
        if not awarded_point.evidence_id:
            raise ConstraintViolationError(
                trace_id=trace_id,
                constraint="EVIDENCE_CITATION_REQUIRED",
                details=f"Point {awarded_point.point_id} does not cite evidence"
            )
    
    @staticmethod
    def validate_marks_sum_correctly(
        awarded_points: List[AwardedPoint],
        expected_total: float,
        trace_id: str,
        tolerance: float = 0.01
    ) -> None:
        """Ensure breakdown sums to total (within tolerance).
        
        Args:
            awarded_points: List of awarded points
            expected_total: Expected sum
            trace_id: Trace ID
            tolerance: Floating point tolerance
            
        Raises:
            ConstraintViolationError: If sum doesn't match
        """
        actual_total = sum(p.marks for p in awarded_points)
        
        if abs(actual_total - expected_total) > tolerance:
            raise ConstraintViolationError(
                trace_id=trace_id,
                constraint="MARKS_SUM_MISMATCH",
                details=f"Breakdown sums to {actual_total} but expected {expected_total}"
            )
    
    @staticmethod
    def validate_no_negative_marks(
        awarded_marks: float,
        trace_id: str
    ) -> None:
        """Ensure no negative marks awarded.
        
        Args:
            awarded_marks: Marks to validate
            trace_id: Trace ID
            
        Raises:
            ConstraintViolationError: If negative
        """
        if awarded_marks < 0:
            raise ConstraintViolationError(
                trace_id=trace_id,
                constraint="NO_NEGATIVE_MARKS",
                details=f"Negative marks not allowed: {awarded_marks}"
            )
    
    @staticmethod
    def validate_output(
        output: ReasoningMarkingOutput,
        official_rubric: List[RubricPoint],
        trace_id: str
    ) -> None:
        """Run all constraint validations on output.
        
        Args:
            output: Engine output to validate
            official_rubric: Official rubric
            trace_id: Trace ID
            
        Raises:
            ConstraintViolationError: If any constraint violated
        """
        # Check max marks
        MarkingConstraints.validate_max_marks_not_exceeded(
            output.awarded_marks,
            output.max_marks,
            trace_id
        )
        
        # Check no negative marks
        MarkingConstraints.validate_no_negative_marks(
            output.awarded_marks,
            trace_id
        )
        
        # Check breakdown sum
        MarkingConstraints.validate_marks_sum_correctly(
            output.mark_breakdown,
            output.awarded_marks,
            trace_id
        )
        
        # Check each awarded point
        for awarded_point in output.mark_breakdown:
            # Must exist in rubric
            MarkingConstraints.validate_rubric_point_exists(
                awarded_point.point_id,
                official_rubric,
                trace_id
            )
            
            # Must cite evidence
            MarkingConstraints.validate_evidence_citation(
                awarded_point,
                trace_id
            )
