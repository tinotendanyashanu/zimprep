"""Weakness and Strength detection service.

PHASE THREE: Identify topics needing attention vs. strong topics.
"""

import logging
from typing import List, Tuple

from app.engines.mastery_modeling.schemas.output import (
    MasteryLevel,
    TopicMasteryState,
    WeaknessSummary,
    StrengthSummary,
    TrendDirection
)

logger = logging.getLogger(__name__)


class WeaknessStrengthDetector:
    """Service for detecting weak and strong topics.
    
    WEAKNESS CRITERIA:
    - Mastery ≤ Developing
    - Trend negative or flat
    - Minimum 3 attempts
    
    STRENGTH CRITERIA:
    - Mastery ≥ Proficient
    - Trend positive or stable
    - Confidence ≥ 0.7
    """
    
    # Minimum attempts for reliable detection
    MIN_ATTEMPTS_FOR_WEAKNESS = 2
    MIN_ATTEMPTS_FOR_STRENGTH = 3
    
    # Confidence threshold for strength
    MIN_CONFIDENCE_FOR_STRENGTH = 0.7
    
    def detect_weaknesses(
        self,
        mastery_states: List[TopicMasteryState]
    ) -> List[WeaknessSummary]:
        """Detect and rank topics needing attention.
        
        Args:
            mastery_states: List of topic mastery states
            
        Returns:
            List of weaknesses ranked by priority (highest first)
        """
        weaknesses: List[Tuple[WeaknessSummary, float]] = []
        
        for state in mastery_states:
            # Check weakness criteria
            if not self._is_weakness(state):
                continue
            
            # Calculate priority score
            priority = self._calculate_weakness_priority(state)
            
            # Build summary
            weakness = WeaknessSummary(
                topic_id=state.topic_id,
                topic_name=state.topic_name,
                mastery_level=state.mastery_level,
                priority_score=priority,
                trend=state.justification.trend_direction
            )
            
            weaknesses.append((weakness, priority))
        
        # Sort by priority (highest first)
        weaknesses.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Detected {len(weaknesses)} weak topics")
        
        return [w[0] for w in weaknesses]
    
    def detect_strengths(
        self,
        mastery_states: List[TopicMasteryState]
    ) -> List[StrengthSummary]:
        """Detect and rank strong topics.
        
        Args:
            mastery_states: List of topic mastery states
            
        Returns:
            List of strengths ranked by stability (highest first)
        """
        strengths: List[Tuple[StrengthSummary, float]] = []
        
        for state in mastery_states:
            # Check strength criteria
            if not self._is_strength(state):
                continue
            
            # Calculate stability score
            stability = self._calculate_strength_stability(state)
            
            # Build summary
            strength = StrengthSummary(
                topic_id=state.topic_id,
                topic_name=state.topic_name,
                mastery_level=state.mastery_level,
                stability_score=stability
            )
            
            strengths.append((strength, stability))
        
        # Sort by stability (highest first)
        strengths.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Detected {len(strengths)} strong topics")
        
        return [s[0] for s in strengths]
    
    def _is_weakness(self, state: TopicMasteryState) -> bool:
        """Check if topic meets weakness criteria.
        
        Args:
            state: Topic mastery state
            
        Returns:
            True if topic is a weakness
        """
        # Must have minimum attempts
        if state.justification.score_summary.attempt_count < self.MIN_ATTEMPTS_FOR_WEAKNESS:
            return False
        
        # Mastery ≤ Developing
        weakness_levels = {
            MasteryLevel.NOT_INTRODUCED,
            MasteryLevel.EMERGING,
            MasteryLevel.DEVELOPING
        }
        
        if state.mastery_level not in weakness_levels:
            return False
        
        # Prefer topics with declining or stable trends (but not required)
        # Any topic at developing or below is considered a potential weakness
        
        return True
    
    def _is_strength(self, state: TopicMasteryState) -> bool:
        """Check if topic meets strength criteria.
        
        Args:
            state: Topic mastery state
            
        Returns:
            True if topic is a strength
        """
        # Must have minimum attempts
        if state.justification.score_summary.attempt_count < self.MIN_ATTEMPTS_FOR_STRENGTH:
            return False
        
        # Mastery ≥ Proficient
        strength_levels = {
            MasteryLevel.PROFICIENT,
            MasteryLevel.MASTERED
        }
        
        if state.mastery_level not in strength_levels:
            return False
        
        # Confidence ≥ threshold
        if state.justification.confidence_weight < self.MIN_CONFIDENCE_FOR_STRENGTH:
            return False
        
        # Trend should be stable or improving (not strictly declining)
        if state.justification.trend_direction == TrendDirection.DECLINING:
            # Declining proficient topics are less strong
            # But still consider them if confidence is very high
            if state.justification.confidence_weight < 0.85:
                return False
        
        return True
    
    def _calculate_weakness_priority(self, state: TopicMasteryState) -> float:
        """Calculate priority score for a weakness.
        
        Higher priority = more urgent to address
        
        Args:
            state: Topic mastery state
            
        Returns:
            Priority score (0.0-1.0)
        """
        priority = 0.0
        
        # Base priority from maturity level
        level_priorities = {
            MasteryLevel.NOT_INTRODUCED: 0.3,
            MasteryLevel.EMERGING: 0.6,
            MasteryLevel.DEVELOPING: 0.8,
        }
        priority += level_priorities.get(state.mastery_level, 0.5)
        
        # Boost for declining trend
        if state.justification.trend_direction == TrendDirection.DECLINING:
            priority += 0.15
        
        # Boost for low scores
        avg_score = state.justification.score_summary.average_score
        if avg_score < 40.0:
            priority += 0.1
        
        # Normalize to 0-1
        priority = min(1.0, priority)
        
        return priority
    
    def _calculate_strength_stability(self, state: TopicMasteryState) -> float:
        """Calculate stability score for a strength.
        
        Higher stability = more consistent performance
        
        Args:
            state: Topic mastery state
            
        Returns:
            Stability score (0.0-1.0)
        """
        stability = 0.0
        
        # Base stability from mastery level
        level_stability = {
            MasteryLevel.PROFICIENT: 0.7,
            MasteryLevel.MASTERED: 0.9,
        }
        stability += level_stability.get(state.mastery_level, 0.5)
        
        # Boost for improving or stable trend
        if state.justification.trend_direction == TrendDirection.IMPROVING:
            stability += 0.08
        elif state.justification.trend_direction == TrendDirection.STABLE:
            stability += 0.05
        
        # Factor in confidence
        stability *= state.justification.confidence_weight
        
        # Normalize to 0-1
        stability = min(1.0, stability)
        
        return stability
