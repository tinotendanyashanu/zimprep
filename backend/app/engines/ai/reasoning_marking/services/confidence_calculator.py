"""Confidence Calculator Service.

Calculates AI confidence in marking assessment based on multiple factors.
"""

from typing import List
import logging

from app.engines.ai.reasoning_marking.schemas import (
    RubricPoint,
    RetrievedEvidence,
    AwardedPoint,
)

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Service for calculating marking confidence.
    
    IMPORTANT: Confidence ≠ student quality
               Confidence = AI certainty in the marking
    """
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.5
    LOW_CONFIDENCE = 0.0
    
    @staticmethod
    def calculate_confidence(
        rubric_points: List[RubricPoint],
        awarded_points: List[AwardedPoint],
        retrieved_evidence: List[RetrievedEvidence],
        answer_length: int,
        trace_id: str
    ) -> float:
        """Calculate overall confidence score.
        
        Confidence factors:
        1. Evidence coverage (% of rubric points with supporting evidence)
        2. Evidence quality (average relevance score)
        3. Answer clarity (length and structure indicators)
        4. Rubric match density (how well evidence maps to rubric)
        
        Args:
            rubric_points: Official rubric
            awarded_points: Points awarded by LLM
            retrieved_evidence: Evidence from Retrieval Engine
            answer_length: Length of student answer
            trace_id: Trace ID
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Factor 1: Evidence coverage
        evidence_coverage = ConfidenceCalculator._calculate_evidence_coverage(
            rubric_points,
            awarded_points
        )
        
        # Factor 2: Evidence quality
        evidence_quality = ConfidenceCalculator._calculate_evidence_quality(
            retrieved_evidence
        )
        
        # Factor 3: Answer clarity
        answer_clarity = ConfidenceCalculator._calculate_answer_clarity(
            answer_length
        )
        
        # Factor 4: Rubric match density
        rubric_match = ConfidenceCalculator._calculate_rubric_match(
            rubric_points,
            awarded_points
        )
        
        # Weighted combination
        # Evidence coverage and quality are most important for legal defensibility
        confidence = (
            0.35 * evidence_coverage +
            0.35 * evidence_quality +
            0.15 * answer_clarity +
            0.15 * rubric_match
        )
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        logger.info(
            "Confidence calculated",
            extra={
                "trace_id": trace_id,
                "confidence": confidence,
                "evidence_coverage": evidence_coverage,
                "evidence_quality": evidence_quality,
                "answer_clarity": answer_clarity,
                "rubric_match": rubric_match
            }
        )
        
        return confidence
    
    @staticmethod
    def _calculate_evidence_coverage(
        rubric_points: List[RubricPoint],
        awarded_points: List[AwardedPoint]
    ) -> float:
        """Calculate what % of awarded points have evidence.
        
        Returns:
            Score 0.0 to 1.0
        """
        if not awarded_points:
            # No points awarded - could be legitimate zero score
            return 0.7  # Neutral confidence
        
        # All awarded points MUST have evidence (enforced by schema)
        # So we check uniqueness of evidence
        unique_evidence = set(p.evidence_id for p in awarded_points if p.evidence_id)
        
        # More diverse evidence = higher confidence
        diversity_score = min(1.0, len(unique_evidence) / max(1, len(awarded_points)))
        
        return diversity_score
    
    @staticmethod
    def _calculate_evidence_quality(
        retrieved_evidence: List[RetrievedEvidence]
    ) -> float:
        """Calculate average relevance score of evidence.
        
        Returns:
            Score 0.0 to 1.0
        """
        if not retrieved_evidence:
            return 0.0
        
        avg_relevance = sum(e.relevance_score for e in retrieved_evidence) / len(retrieved_evidence)
        return avg_relevance
    
    @staticmethod
    def _calculate_answer_clarity(answer_length: int) -> float:
        """Estimate answer clarity based on length.
        
        Very short or very long answers may be unclear.
        This is a rough heuristic.
        
        Returns:
            Score 0.0 to 1.0
        """
        if answer_length < 10:
            return 0.3  # Too short
        elif answer_length < 50:
            return 0.7  # Short answer
        elif answer_length < 500:
            return 1.0  # Good length
        elif answer_length < 2000:
            return 0.9  # Long essay
        else:
            return 0.7  # Very long, may be verbose
    
    @staticmethod
    def _calculate_rubric_match(
        rubric_points: List[RubricPoint],
        awarded_points: List[AwardedPoint]
    ) -> float:
        """Calculate how well awarded points cover the rubric.
        
        Returns:
            Score 0.0 to 1.0
        """
        if not rubric_points:
            return 0.0
        
        # What fraction of rubric points were awarded?
        awarded_ratio = len(awarded_points) / len(rubric_points)
        
        # Both extremes (0% or 100%) can be legitimate
        # We want a U-shaped curve - high confidence at extremes
        if awarded_ratio < 0.2:
            return 0.9  # Clear fail, high confidence
        elif awarded_ratio > 0.8:
            return 0.9  # Clear pass, high confidence
        else:
            return 0.7  # Partial credit, moderate confidence
    
    @staticmethod
    def get_confidence_label(confidence: float) -> str:
        """Get human-readable confidence label.
        
        Args:
            confidence: Confidence score
            
        Returns:
            Label: "high", "medium", or "low"
        """
        if confidence >= ConfidenceCalculator.HIGH_CONFIDENCE:
            return "high"
        elif confidence >= ConfidenceCalculator.MEDIUM_CONFIDENCE:
            return "medium"
        else:
            return "low"
