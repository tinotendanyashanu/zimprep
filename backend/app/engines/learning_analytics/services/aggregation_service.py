"""Statistical aggregation service for Learning Analytics Engine.

PHASE THREE: Pure statistical calculations (NO AI).
All methods are deterministic and replayable.
"""

import logging
import statistics
from typing import List, Tuple
from datetime import datetime

from app.engines.learning_analytics.schemas.output import TrendDirection

logger = logging.getLogger(__name__)


class AggregationService:
    """Pure statistical aggregation service.
    
    CRITICAL RULES:
    - NO AI calls
    - Deterministic calculations only
    - Fully replayable from same inputs
    """
    
    @staticmethod
    def calculate_rolling_average(
        scores: List[float],
        window: int = 5
    ) -> float:
        """Calculate rolling average of most recent scores.
        
        Args:
            scores: List of scores (chronological order)
            window: Rolling window size (default: 5)
            
        Returns:
            Rolling average (last N scores or all if less than N)
        """
        if not scores:
            return 0.0
        
        # Take last N scores (or all if less than N)
        recent_scores = scores[-window:] if len(scores) >= window else scores
        
        return statistics.mean(recent_scores)
    
    @staticmethod
    def detect_trend_slope(
        timestamps: List[datetime],
        scores: List[float]
    ) -> Tuple[float, float | None]:
        """Detect performance trend using linear regression.
        
        Args:
            timestamps: List of attempt timestamps
            scores: List of corresponding scores
            
        Returns:
            Tuple of (slope, r_squared)
            - slope: Rate of change (positive = improving)
            - r_squared: Fit quality (0-1), None if insufficient data
        """
        if len(scores) < 2:
            return 0.0, None
        
        # Convert timestamps to numeric values (days since first attempt)
        if not timestamps:
            return 0.0, None
        
        first_time = timestamps[0]
        x_values = [(t - first_time).total_seconds() / 86400 for t in timestamps]  # Days
        y_values = scores
        
        # Simple linear regression
        n = len(x_values)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        # Calculate slope
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0, None
        
        slope = numerator / denominator
        
        # Calculate R-squared
        y_predictions = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_total = sum((y - y_mean) ** 2 for y in y_values)
        ss_residual = sum((y - y_pred) ** 2 for y, y_pred in zip(y_values, y_predictions))
        
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0.0
        
        logger.debug(
            f"Trend analysis: slope={slope:.4f}, r²={r_squared:.4f}, n={n}"
        )
        
        return slope, r_squared
    
    @staticmethod
    def classify_trend_direction(
        slope: float,
        threshold: float = 0.5
    ) -> TrendDirection:
        """Classify trend direction from slope.
        
        Args:
            slope: Linear regression slope
            threshold: Minimum slope magnitude to classify as improving/declining
            
        Returns:
            TrendDirection enum value
        """
        if slope > threshold:
            return TrendDirection.IMPROVING
        elif slope < -threshold:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    @staticmethod
    def calculate_volatility(scores: List[float]) -> float:
        """Calculate performance volatility (standard deviation).
        
        Args:
            scores: List of scores
            
        Returns:
            Standard deviation (consistency measure)
        """
        if len(scores) < 2:
            return 0.0
        
        return statistics.stdev(scores)
    
    @staticmethod
    def confidence_weighted_score(
        scores: List[float],
        confidence_scores: List[float] | None = None
    ) -> Tuple[float, float]:
        """Calculate confidence-weighted average score.
        
        Args:
            scores: List of performance scores
            confidence_scores: Optional list of confidence weights (0-1)
                              If None, all scores weighted equally
            
        Returns:
            Tuple of (weighted_score, overall_confidence)
        """
        if not scores:
            return 0.0, 0.0
        
        # If no confidence scores provided, use equal weights
        if confidence_scores is None or len(confidence_scores) != len(scores):
            confidence_scores = [1.0] * len(scores)
        
        # Weighted average
        total_weight = sum(confidence_scores)
        if total_weight == 0:
            return statistics.mean(scores), 0.0
        
        weighted_sum = sum(
            score * conf
            for score, conf in zip(scores, confidence_scores)
        )
        
        weighted_average = weighted_sum / total_weight
        overall_confidence = statistics.mean(confidence_scores)
        
        return weighted_average, overall_confidence
    
    @staticmethod
    def calculate_attempt_confidence(
        attempt_count: int,
        max_confidence_attempts: int = 10
    ) -> float:
        """Calculate confidence based on number of attempts.
        
        More attempts = higher confidence in metrics.
        
        Args:
            attempt_count: Number of attempts analyzed
            max_confidence_attempts: Number of attempts for full confidence
            
        Returns:
            Confidence score (0.0-1.0)
        """
        return min(1.0, attempt_count / max_confidence_attempts)
