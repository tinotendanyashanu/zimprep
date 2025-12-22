"""Aggregation service for the Results Engine.

Handles all mark calculations with deterministic arithmetic.
All operations use explicit decimal precision (2 decimal places).
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from app.engines.results.schemas.input import PaperInput, SectionBreakdown

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for aggregating marks across papers and sections.
    
    All arithmetic is deterministic with explicit precision handling.
    No rounding unless specified in syllabus rules.
    """
    
    # Precision for all calculations (2 decimal places)
    PRECISION = Decimal("0.01")
    
    @classmethod
    def aggregate_section_marks(
        cls,
        sections: List[SectionBreakdown]
    ) -> tuple[float, float]:
        """Sum marks within a paper's sections.
        
        Args:
            sections: List of section breakdowns
            
        Returns:
            Tuple of (total_max_marks, total_awarded_marks)
        """
        if not sections:
            return 0.0, 0.0
        
        total_max = Decimal("0")
        total_awarded = Decimal("0")
        
        for section in sections:
            total_max += Decimal(str(section.max_marks))
            total_awarded += Decimal(str(section.awarded_marks))
        
        # Round to precision
        total_max = total_max.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
        total_awarded = total_awarded.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
        
        logger.debug(
            "Aggregated %d sections: max=%.2f, awarded=%.2f",
            len(sections),
            total_max,
            total_awarded
        )
        
        return float(total_max), float(total_awarded)
    
    @classmethod
    def apply_paper_weighting(
        cls,
        awarded_marks: float,
        max_marks: float,
        weighting: float
    ) -> float:
        """Calculate a paper's weighted contribution to the final total.
        
        This normalizes the paper marks to the maximum scale and applies
        the weighting factor.
        
        Args:
            awarded_marks: Marks achieved on the paper
            max_marks: Maximum marks for the paper
            weighting: Paper weighting (0.0-1.0)
            
        Returns:
            Weighted contribution to final total
            
        Example:
            Paper 1: 75/100 marks, weighting 0.5 (50%)
            -> (75/100) * (100 * 0.5) = 37.5 marks out of 50
        """
        if max_marks == 0:
            logger.warning("Paper has zero max marks, returning 0 weighted contribution")
            return 0.0
        
        # Convert to Decimal for precision
        awarded = Decimal(str(awarded_marks))
        maximum = Decimal(str(max_marks))
        weight = Decimal(str(weighting))
        
        # Calculate percentage achieved
        percentage = awarded / maximum
        
        # Apply weighting (contribution out of 100)
        weighted_contribution = percentage * Decimal("100") * weight
        
        # Round to precision
        result = weighted_contribution.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
        
        logger.debug(
            "Applied weighting: %.2f/%.2f (%.2f%%) * %.2f = %.2f",
            awarded_marks,
            max_marks,
            percentage * 100,
            weighting,
            result
        )
        
        return float(result)
    
    @classmethod
    def calculate_subject_total(
        cls,
        papers: List[PaperInput]
    ) -> float:
        """Calculate the final weighted total across all papers.
        
        Args:
            papers: List of paper inputs with marks and weightings
            
        Returns:
            Total weighted marks (out of 100)
        """
        if not papers:
            logger.warning("No papers provided for subject total calculation")
            return 0.0
        
        total = Decimal("0")
        
        for paper in papers:
            weighted_contribution = cls.apply_paper_weighting(
                awarded_marks=paper.awarded_marks,
                max_marks=paper.max_marks,
                weighting=paper.weighting
            )
            total += Decimal(str(weighted_contribution))
        
        # Round to precision
        result = total.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
        
        logger.info(
            "Calculated subject total from %d papers: %.2f",
            len(papers),
            result
        )
        
        return float(result)
    
    @classmethod
    def calculate_percentage(
        cls,
        awarded_marks: float,
        max_marks: float
    ) -> float:
        """Calculate percentage score.
        
        Args:
            awarded_marks: Marks achieved
            max_marks: Maximum possible marks
            
        Returns:
            Percentage (0.0-100.0)
        """
        if max_marks == 0:
            logger.warning("Cannot calculate percentage with zero max marks")
            return 0.0
        
        awarded = Decimal(str(awarded_marks))
        maximum = Decimal(str(max_marks))
        
        percentage = (awarded / maximum) * Decimal("100")
        result = percentage.quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
        
        return float(result)
