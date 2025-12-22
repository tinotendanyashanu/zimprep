"""
Reporting & Analytics Engine - Trend Analyzer Service

Analyzes performance trends over time.
All analysis is deterministic and based on historical data only.
"""

from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID


class TrendAnalyzerService:
    """
    Service for analyzing performance trends.
    
    Responsibilities:
    - Analyze longitudinal performance
    - Identify improvement and decline areas
    - Calculate trend metrics
    - Provide data-driven insights
    """
    
    # Thresholds for trend classification
    IMPROVEMENT_THRESHOLD = 5.0  # +5% is considered improvement
    DECLINE_THRESHOLD = -5.0  # -5% is considered decline
    
    def __init__(self, trace_id: UUID):
        """
        Initialize the trend analyzer.
        
        Args:
            trace_id: Trace ID for audit logging
        """
        self.trace_id = trace_id
    
    def analyze_longitudinal_performance(
        self,
        historical_results: List[Dict[str, Any]],
        topic_filter: str | None = None,
    ) -> Dict[str, Any]:
        """
        Analyze performance over time.
        
        Args:
            historical_results: List of historical exam results
            topic_filter: Optional topic to filter by
            
        Returns:
            Dictionary containing:
                - overall_trend: str (improving, stable, declining)
                - trend_percentage: float (rate of change)
                - data_points: List of data points
                - insights: List[str] (human-readable insights)
        """
        if not historical_results:
            return {
                "overall_trend": "stable",
                "trend_percentage": 0.0,
                "data_points": [],
                "insights": ["Insufficient data for trend analysis"],
            }
        
        # Sort by date
        sorted_results = sorted(
            historical_results,
            key=lambda x: x.get("exam_date", datetime.min),
        )
        
        # Filter by topic if specified
        if topic_filter:
            sorted_results = [
                r for r in sorted_results
                if topic_filter in r.get("topics", [])
            ]
        
        if len(sorted_results) < 2:
            return {
                "overall_trend": "stable",
                "trend_percentage": 0.0,
                "data_points": sorted_results,
                "insights": ["Need at least 2 data points for trend analysis"],
            }
        
        # Calculate trend
        scores = [r.get("percentage", 0.0) for r in sorted_results]
        first_score = scores[0]
        last_score = scores[-1]
        trend_percentage = last_score - first_score
        
        # Classify trend
        if trend_percentage >= self.IMPROVEMENT_THRESHOLD:
            overall_trend = "improving"
        elif trend_percentage <= self.DECLINE_THRESHOLD:
            overall_trend = "declining"
        else:
            overall_trend = "stable"
        
        # Generate insights
        insights = self._generate_trend_insights(
            overall_trend, trend_percentage, scores
        )
        
        return {
            "overall_trend": overall_trend,
            "trend_percentage": trend_percentage,
            "data_points": sorted_results,
            "insights": insights,
        }
    
    def identify_improvement_areas(
        self,
        topic_trends: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[str]]:
        """
        Identify which topics are improving and which are declining.
        
        Args:
            topic_trends: Dictionary mapping topic names to historical results
            
        Returns:
            Dictionary with:
                - improving: List of topic names
                - stable: List of topic names
                - declining: List of topic names
        """
        improving = []
        stable = []
        declining = []
        
        for topic, results in topic_trends.items():
            if len(results) < 2:
                stable.append(topic)
                continue
            
            # Sort by date
            sorted_results = sorted(
                results,
                key=lambda x: x.get("exam_date", datetime.min),
            )
            
            scores = [r.get("percentage", 0.0) for r in sorted_results]
            trend = scores[-1] - scores[0]
            
            if trend >= self.IMPROVEMENT_THRESHOLD:
                improving.append(topic)
            elif trend <= self.DECLINE_THRESHOLD:
                declining.append(topic)
            else:
                stable.append(topic)
        
        return {
            "improving": improving,
            "stable": stable,
            "declining": declining,
        }
    
    def calculate_trend_metrics(
        self,
        data_points: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Calculate various trend metrics.
        
        Args:
            data_points: List of performance data points
            
        Returns:
            Dictionary containing:
                - average: Overall average
                - moving_average: Recent moving average (last 3 points)
                - volatility: Standard deviation
                - rate_of_change: Change per time period
        """
        if not data_points:
            return {
                "average": 0.0,
                "moving_average": 0.0,
                "volatility": 0.0,
                "rate_of_change": 0.0,
            }
        
        scores = [d.get("percentage", 0.0) for d in data_points]
        
        # Average
        average = sum(scores) / len(scores)
        
        # Moving average (last 3 points)
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        moving_average = sum(recent_scores) / len(recent_scores)
        
        # Volatility (standard deviation)
        variance = sum((x - average) ** 2 for x in scores) / len(scores)
        volatility = variance ** 0.5
        
        # Rate of change
        if len(scores) >= 2:
            total_change = scores[-1] - scores[0]
            time_periods = len(scores) - 1
            rate_of_change = total_change / time_periods
        else:
            rate_of_change = 0.0
        
        return {
            "average": average,
            "moving_average": moving_average,
            "volatility": volatility,
            "rate_of_change": rate_of_change,
        }
    
    def _generate_trend_insights(
        self,
        trend: str,
        trend_percentage: float,
        scores: List[float],
    ) -> List[str]:
        """Generate human-readable insights from trend data."""
        insights = []
        
        # Overall trend insight
        if trend == "improving":
            insights.append(
                f"Performance has improved by {trend_percentage:.1f}% over the analyzed period"
            )
        elif trend == "declining":
            insights.append(
                f"Performance has declined by {abs(trend_percentage):.1f}% over the analyzed period"
            )
        else:
            insights.append("Performance has remained stable over the analyzed period")
        
        # Consistency insight
        if len(scores) >= 3:
            variance = sum((x - sum(scores) / len(scores)) ** 2 for x in scores) / len(scores)
            std_dev = variance ** 0.5
            
            if std_dev < 5:
                insights.append("Performance has been consistent across attempts")
            elif std_dev > 15:
                insights.append("Performance has shown significant variation across attempts")
        
        return insights
