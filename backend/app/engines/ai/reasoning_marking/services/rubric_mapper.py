"""Rubric Mapper Service.

NON-AI service that decomposes official rubric into atomic mark points.
This ensures LLMs never define rubric structure.
"""

from typing import List, Dict, Any
import logging

from app.engines.ai.reasoning_marking.schemas import RubricPoint
from app.engines.ai.reasoning_marking.errors import InvalidRubricError

logger = logging.getLogger(__name__)


class RubricMapperService:
    """Service for processing and validating official rubrics.
    
    CRITICAL: This is a NON-AI service. No LLM is involved in rubric decomposition.
    """
    
    @staticmethod
    def decompose_rubric(
        rubric_points: List[RubricPoint],
        trace_id: str
    ) -> Dict[str, RubricPoint]:
        """Decompose rubric into a dictionary for fast lookup.
        
        Args:
            rubric_points: List of atomic rubric points
            trace_id: Trace ID for logging
            
        Returns:
            Dict mapping point_id to RubricPoint
            
        Raises:
            InvalidRubricError: If rubric is malformed
        """
        if not rubric_points:
            raise InvalidRubricError(
                trace_id=trace_id,
                reason="Rubric is empty"
            )
        
        rubric_map = {}
        total_marks = 0.0
        
        for point in rubric_points:
            # Check for duplicates
            if point.point_id in rubric_map:
                raise InvalidRubricError(
                    trace_id=trace_id,
                    reason=f"Duplicate point_id: {point.point_id}"
                )
            
            # Validate marks are positive
            if point.marks <= 0:
                raise InvalidRubricError(
                    trace_id=trace_id,
                    reason=f"Point {point.point_id} has non-positive marks: {point.marks}"
                )
            
            rubric_map[point.point_id] = point
            total_marks += point.marks
        
        logger.info(
            "Rubric decomposed",
            extra={
                "trace_id": trace_id,
                "point_count": len(rubric_map),
                "total_marks": total_marks
            }
        )
        
        return rubric_map
    
    @staticmethod
    def get_rubric_summary(rubric_points: List[RubricPoint]) -> str:
        """Generate a human-readable summary of rubric points.
        
        This is used to provide context to the LLM without allowing
        it to modify the rubric structure.
        
        Args:
            rubric_points: List of rubric points
            
        Returns:
            Formatted rubric summary
        """
        lines = ["OFFICIAL RUBRIC:"]
        lines.append("=" * 60)
        
        for i, point in enumerate(rubric_points, 1):
            lines.append(f"\n{i}. [{point.point_id}] ({point.marks} marks)")
            lines.append(f"   {point.description}")
        
        lines.append("\n" + "=" * 60)
        total = sum(p.marks for p in rubric_points)
        lines.append(f"TOTAL AVAILABLE MARKS: {total}")
        
        return "\n".join(lines)
    
    @staticmethod
    def validate_rubric_integrity(
        rubric_points: List[RubricPoint],
        max_marks: int,
        trace_id: str
    ) -> None:
        """Validate that rubric is internally consistent.
        
        Args:
            rubric_points: Rubric points
            max_marks: Expected maximum marks
            trace_id: Trace ID
            
        Raises:
            InvalidRubricError: If rubric is invalid
        """
        total_marks = sum(p.marks for p in rubric_points)
        
        # Allow small floating point tolerance
        if abs(total_marks - max_marks) > 0.01:
            raise InvalidRubricError(
                trace_id=trace_id,
                reason=f"Rubric total ({total_marks}) does not match max_marks ({max_marks})"
            )
        
        logger.debug(
            "Rubric integrity validated",
            extra={
                "trace_id": trace_id,
                "rubric_total": total_marks,
                "max_marks": max_marks
            }
        )
