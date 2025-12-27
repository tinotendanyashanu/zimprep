"""Aggregation Service - Cohort-level analytics computation.

PHASE FOUR: Pure statistical aggregation from student-level data.
"""

import logging
from typing import List, Dict, Any
from statistics import mean, median, stdev
from collections import defaultdict

from app.engines.institutional_analytics.schemas.output import (
    TopicMasteryDistribution,
    MasteryLevelCounts,
    MasteryLevelPercentages,
    CohortAverageScore,
    TrendIndicator,
    CoverageGap
)

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for computing cohort-level aggregated analytics.
    
    CRITICAL RULES:
    - All operations are DETERMINISTIC
    - NO AI involved
    - READ-ONLY operations on source data
    - Full explainability through statistical methods
    """
    
    @staticmethod
    def aggregate_mastery_distribution(
        mastery_states: List[Dict[str, Any]],
        trace_id: str
    ) -> List[TopicMasteryDistribution]:
        """Aggregate mastery level distributions per topic.
        
        Args:
            mastery_states: List of topic mastery state documents
            trace_id: Request trace ID
            
        Returns:
            List of topic mastery distributions
        """
        # Group by topic
        topic_groups: Dict[str, List[str]] = defaultdict(list)
        topic_names: Dict[str, str] = {}
        
        for state in mastery_states:
            for topic_state in state.get("topic_mastery_states", []):
                topic_id = topic_state["topic_id"]
                mastery_level = topic_state["mastery_level"]
                topic_groups[topic_id].append(mastery_level)
                topic_names[topic_id] = topic_state.get("topic_name", topic_id)
        
        distributions = []
        
        for topic_id, mastery_levels in topic_groups.items():
            # Count occurrences of each mastery level
            counts = {
                "NOT_INTRODUCED": mastery_levels.count("NOT_INTRODUCED"),
                "EMERGING": mastery_levels.count("EMERGING"),
                "DEVELOPING": mastery_levels.count("DEVELOPING"),
                "PROFICIENT": mastery_levels.count("PROFICIENT"),
                "MASTERED": mastery_levels.count("MASTERED")
            }
            
            total = len(mastery_levels)
            percentages = {
                level: (count / total * 100.0) if total > 0 else 0.0
                for level, count in counts.items()
            }
            
            distributions.append(
                TopicMasteryDistribution(
                    topic_id=topic_id,
                    topic_name=topic_names[topic_id],
                    mastery_level_counts=MasteryLevelCounts(**counts),
                    mastery_level_percentages=MasteryLevelPercentages(**percentages)
                )
            )
        
        logger.debug(
            f"[{trace_id}] Aggregated mastery distribution for {len(distributions)} topics"
        )
        
        return distributions
    
    @staticmethod
    def aggregate_cohort_scores(
        analytics_snapshots: List[Dict[str, Any]],
        trace_id: str
    ) -> List[CohortAverageScore]:
        """Aggregate cohort average scores per topic.
        
        Args:
            analytics_snapshots: List of learning analytics snapshots
            trace_id: Request trace ID
            
        Returns:
            List of cohort average scores
        """
        # Group scores by topic
        topic_scores: Dict[str, List[float]] = defaultdict(list)
        
        for snapshot in analytics_snapshots:
            for topic_analytics in snapshot.get("topic_analytics", []):
                topic_id = topic_analytics["topic_id"]
                # Use rolling average from each student's analytics
                rolling_avg = topic_analytics.get("rolling_average")
                if rolling_avg is not None:
                    topic_scores[topic_id].append(rolling_avg)
        
        cohort_scores = []
        
        for topic_id, scores in topic_scores.items():
            if len(scores) > 0:
                cohort_scores.append(
                    CohortAverageScore(
                        topic_id=topic_id,
                        average_score=mean(scores),
                        median_score=median(scores),
                        sample_size=len(scores)
                    )
                )
        
        logger.debug(
            f"[{trace_id}] Aggregated cohort scores for {len(cohort_scores)} topics"
        )
        
        return cohort_scores
    
    @staticmethod
    def aggregate_trend_indicators(
        analytics_snapshots: List[Dict[str, Any]],
        trace_id: str
    ) -> List[TrendIndicator]:
        """Aggregate trend indicators per topic.
        
        Args:
            analytics_snapshots: List of learning analytics snapshots
            trace_id: Request trace ID
            
        Returns:
            List of trend indicators
        """
        # Group trends by topic
        topic_trends: Dict[str, List[str]] = defaultdict(list)
        topic_scores: Dict[str, List[float]] = defaultdict(list)
        
        for snapshot in analytics_snapshots:
            for topic_analytics in snapshot.get("topic_analytics", []):
                topic_id = topic_analytics["topic_id"]
                trend_direction = topic_analytics.get("trend", {}).get("direction")
                rolling_avg = topic_analytics.get("rolling_average")
                
                if trend_direction:
                    topic_trends[topic_id].append(trend_direction)
                if rolling_avg is not None:
                    topic_scores[topic_id].append(rolling_avg)
        
        indicators = []
        
        for topic_id in topic_trends.keys():
            trends = topic_trends[topic_id]
            scores = topic_scores.get(topic_id, [])
            
            # Determine cohort trend (majority vote)
            improving_count = trends.count("improving")
            stable_count = trends.count("stable")
            declining_count = trends.count("declining")
            
            if improving_count > stable_count and improving_count > declining_count:
                cohort_trend = "improving"
            elif declining_count > stable_count and declining_count > improving_count:
                cohort_trend = "declining"
            elif stable_count >= improving_count and stable_count >= declining_count:
                cohort_trend = "stable"
            else:
                cohort_trend = "insufficient_data"
            
            # Calculate cohort volatility
            volatility = stdev(scores) if len(scores) > 1 else 0.0
            
            indicators.append(
                TrendIndicator(
                    topic_id=topic_id,
                    trend_direction=cohort_trend,
                    cohort_volatility=volatility
                )
            )
        
        logger.debug(
            f"[{trace_id}] Aggregated trend indicators for {len(indicators)} topics"
        )
        
        return indicators
    
    @staticmethod
    def identify_coverage_gaps(
        analytics_snapshots: List[Dict[str, Any]],
        trace_id: str,
        min_practice_threshold: int = 10
    ) -> List[CoverageGap]:
        """Identify topics with low practice coverage.
        
        Args:
            analytics_snapshots: List of learning analytics snapshots
            trace_id: Request trace ID
            min_practice_threshold: Minimum practice frequency
            
        Returns:
            List of coverage gaps
        """
        # Aggregate practice frequency per topic
        topic_practice: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"frequency": 0, "last_practiced": None, "name": ""}
        )
        
        for snapshot in analytics_snapshots:
            for topic_analytics in snapshot.get("topic_analytics", []):
                topic_id = topic_analytics["topic_id"]
                topic_name = topic_analytics.get("topic_name", topic_id)
                timeline = topic_analytics.get("timeline", {})
                attempt_count = len(timeline.get("attempt_timestamps", []))
                
                topic_practice[topic_id]["frequency"] += attempt_count
                topic_practice[topic_id]["name"] = topic_name
                
                # Track most recent practice
                timestamps = timeline.get("attempt_timestamps", [])
                if timestamps:
                    latest = max(timestamps)
                    current_latest = topic_practice[topic_id]["last_practiced"]
                    if current_latest is None or latest > current_latest:
                        topic_practice[topic_id]["last_practiced"] = latest
        
        gaps = []
        
        for topic_id, data in topic_practice.items():
            if data["frequency"] < min_practice_threshold:
                gaps.append(
                    CoverageGap(
                        topic_id=topic_id,
                        topic_name=data["name"],
                        practice_frequency=data["frequency"],
                        last_practiced_at=data["last_practiced"]
                    )
                )
        
        # Sort by frequency (lowest first)
        gaps.sort(key=lambda g: g.practice_frequency)
        
        logger.debug(
            f"[{trace_id}] Identified {len(gaps)} coverage gaps "
            f"(threshold={min_practice_threshold})"
        )
        
        return gaps
