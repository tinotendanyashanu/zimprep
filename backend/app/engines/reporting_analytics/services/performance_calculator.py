"""Performance Calculator Service for Reporting & Analytics Engine.

CRITICAL: This service is DETERMINISTIC and DATA-DRIVEN ONLY.
- NO AI/LLM calls
- NO hardcoded fallbacks
- NO invented heuristics
- ONLY real calculations from persisted exam results

Version: 1.0.0
Type: Deterministic calculation service
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Deterministic performance metric calculator.
    
    Computes dashboard metrics from persisted exam results:
    - Average grade
    - Improvement trend
    - Topic strengths
    - Topic weaknesses
    
    All calculations are reproducible and based solely on database data.
    """
    
    # Standard ZIMSEC grading scale boundaries (percentage-based)
    GRADE_BOUNDARIES = [
        ("A*", 90.0, 100.0),
        ("A", 80.0, 89.99),
        ("B", 70.0, 79.99),
        ("C", 60.0, 69.99),
        ("D", 50.0, 59.99),
        ("E", 40.0, 49.99),
        ("U", 0.0, 39.99),
    ]
    
    @classmethod
    def calculate_average_grade(cls, results: List[dict]) -> Optional[str]:
        """Calculate average grade from all completed exams.
        
        Args:
            results: List of exam result documents from MongoDB
            
        Returns:
            Letter grade (A*, A, B, C, D, E, U) or None if no results
            
        Algorithm:
            1. Extract percentage scores from all results
            2. Calculate arithmetic mean
            3. Resolve mean percentage to letter grade using boundaries
        """
        if not results:
            logger.debug("No results provided - returning None for average grade")
            return None
        
        # Extract percentages
        percentages = []
        for result in results:
            percentage = result.get("percentage")
            if percentage is not None:
                percentages.append(float(percentage))
        
        if not percentages:
            logger.warning("No valid percentage scores found in results")
            return None
        
        # Calculate average
        avg_percentage = sum(percentages) / len(percentages)
        
        # Resolve to grade
        grade = cls._percentage_to_grade(avg_percentage)
        
        logger.info(
            f"Calculated average grade: {grade} from {len(percentages)} exams (avg: {avg_percentage:.2f}%)"
        )
        
        return grade
    
    @classmethod
    def calculate_improvement_trend(
        cls,
        results: List[dict],
        window_size: int = 3,
        stable_threshold: float = 5.0
    ) -> str:
        """Calculate improvement trend from recent exam attempts.
        
        Args:
            results: List of exam result documents (will be sorted by date)
            window_size: Number of recent attempts to analyze (default: 3)
            stable_threshold: Percentage points to consider "stable" (default: 5.0)
            
        Returns:
            One of: "improving", "declining", "stable", "insufficient_data"
            
        Algorithm:
            1. Sort by issued_at (most recent first)
            2. Take last N attempts (window_size)
            3. If < 2 attempts, return "insufficient_data"
            4. Calculate linear trend: compare first vs last in window
            5. If delta > threshold: "improving" or "declining"
            6. Otherwise: "stable"
        """
        if not results:
            logger.debug("No results - returning insufficient_data")
            return "insufficient_data"
        
        # Sort by issued_at descending (most recent first)
        sorted_results = sorted(
            results,
            key=lambda r: r.get("issued_at", datetime.min),
            reverse=True
        )
        
        # Take the most recent N attempts
        recent_results = sorted_results[:window_size]
        
        # Need at least 2 to calculate trend
        if len(recent_results) < 2:
            logger.debug(f"Only {len(recent_results)} exam(s) - insufficient for trend")
            return "insufficient_data"
        
        # Extract percentages (reverse to oldest-to-newest for trend calc)
        percentages = []
        for result in reversed(recent_results):
            percentage = result.get("percentage")
            if percentage is not None:
                percentages.append(float(percentage))
        
        if len(percentages) < 2:
            return "insufficient_data"
        
        # Calculate simple trend: first vs last
        oldest_score = percentages[0]
        newest_score = percentages[-1]
        delta = newest_score - oldest_score
        
        # Determine trend
        if delta > stable_threshold:
            trend = "improving"
        elif delta < -stable_threshold:
            trend = "declining"
        else:
            trend = "stable"
        
        logger.info(
            f"Calculated trend: {trend} (delta: {delta:+.2f}%, window: {len(percentages)} exams)"
        )
        
        return trend
    
    @classmethod
    def identify_strengths(
        cls,
        results: List[dict],
        top_n: int = 3
    ) -> List[str]:
        """Identify top-performing topics from exam history.
        
        Args:
            results: List of exam result documents
            top_n: Number of top topics to return (default: 3)
            
        Returns:
            List of topic names (sorted by average score, descending)
            
        Algorithm:
            1. Aggregate topic_breakdown data from all results
            2. Calculate average percentage per topic
            3. Sort by average percentage (descending)
            4. Return top N topic names
        """
        if not results:
            logger.debug("No results - returning empty strengths")
            return []
        
        # Aggregate topic scores
        topic_scores = cls._aggregate_topic_scores(results)
        
        if not topic_scores:
            logger.debug("No topic breakdown data found - returning empty strengths")
            return []
        
        # Sort by average percentage (descending)
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda item: item[1]["avg_percentage"],
            reverse=True
        )
        
        # Take top N
        strengths = [topic_name for topic_name, _ in sorted_topics[:top_n]]
        
        logger.info(f"Identified strengths: {strengths}")
        
        return strengths
    
    @classmethod
    def identify_weaknesses(
        cls,
        results: List[dict],
        bottom_n: int = 3,
        min_attempts: int = 2
    ) -> List[str]:
        """Identify lowest-performing topics from exam history.
        
        Args:
            results: List of exam result documents
            bottom_n: Number of bottom topics to return (default: 3)
            min_attempts: Minimum attempts required to be considered (default: 2)
            
        Returns:
            List of topic names (sorted by average score, ascending)
            
        Algorithm:
            1. Aggregate topic_breakdown data from all results
            2. Filter topics with >= min_attempts
            3. Calculate average percentage per topic
            4. Sort by average percentage (ascending)
            5. Return bottom N topic names
        """
        if not results:
            logger.debug("No results - returning empty weaknesses")
            return []
        
        # Aggregate topic scores
        topic_scores = cls._aggregate_topic_scores(results)
        
        if not topic_scores:
            logger.debug("No topic breakdown data found - returning empty weaknesses")
            return []
        
        # Filter by minimum attempts
        filtered_topics = {
            topic_name: data
            for topic_name, data in topic_scores.items()
            if data["attempt_count"] >= min_attempts
        }
        
        if not filtered_topics:
            logger.debug(
                f"No topics with >= {min_attempts} attempts - returning empty weaknesses"
            )
            return []
        
        # Sort by average percentage (ascending)
        sorted_topics = sorted(
            filtered_topics.items(),
            key=lambda item: item[1]["avg_percentage"],
            reverse=False  # Ascending for weaknesses
        )
        
        # Take bottom N
        weaknesses = [topic_name for topic_name, _ in sorted_topics[:bottom_n]]
        
        logger.info(f"Identified weaknesses: {weaknesses}")
        
        return weaknesses
    
    # --- PRIVATE HELPER METHODS ---
    
    @classmethod
    def _percentage_to_grade(cls, percentage: float) -> str:
        """Convert percentage score to letter grade.
        
        Args:
            percentage: Percentage score (0-100)
            
        Returns:
            Letter grade (A*, A, B, C, D, E, U)
        """
        for grade, min_pct, max_pct in cls.GRADE_BOUNDARIES:
            if min_pct <= percentage <= max_pct:
                return grade
        
        # Fallback to lowest grade
        return "U"
    
    @classmethod
    def _aggregate_topic_scores(cls, results: List[dict]) -> Dict[str, Dict[str, float]]:
        """Aggregate topic breakdown scores across all results.
        
        Args:
            results: List of exam result documents
            
        Returns:
            Dictionary mapping topic_name -> {avg_percentage, attempt_count}
            
        Example:
            {
                "Mathematics": {"avg_percentage": 85.0, "attempt_count": 3},
                "Physics": {"avg_percentage": 65.0, "attempt_count": 2}
            }
        """
        # Collect scores per topic
        topic_data: Dict[str, List[float]] = defaultdict(list)
        
        for result in results:
            topic_breakdown = result.get("topic_breakdown", [])
            
            for topic in topic_breakdown:
                topic_name = topic.get("topic_name")
                percentage = topic.get("percentage")
                
                if topic_name and percentage is not None:
                    topic_data[topic_name].append(float(percentage))
        
        # Calculate averages
        aggregated = {}
        for topic_name, percentages in topic_data.items():
            avg_percentage = sum(percentages) / len(percentages)
            aggregated[topic_name] = {
                "avg_percentage": avg_percentage,
                "attempt_count": len(percentages)
            }
        
        return aggregated
