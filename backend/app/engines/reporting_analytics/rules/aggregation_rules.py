"""
Reporting & Analytics Engine - Aggregation Rules

Business logic for aggregating and analyzing exam data.
All operations are deterministic and based on factual data only.
"""

from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID


class AggregationRules:
    """
    Defines rules for aggregating exam data into insights.
    
    All aggregations are:
    - Deterministic (same input → same output)
    - Data-driven (no inference or prediction)
    - Auditable (clear calculation methods)
    """
    
    # Thresholds for categorization
    STRONG_THRESHOLD = 75.0  # >= 75% is considered strong
    SATISFACTORY_THRESHOLD = 50.0  # >= 50% is satisfactory
    # Below 50% needs attention
    
    DIFFICULTY_THRESHOLDS = {
        "easy": 80.0,  # If cohort avg >= 80%, topic is easy
        "moderate": 60.0,  # If cohort avg >= 60%, topic is moderate
        # Below 60% is challenging
    }
    
    def __init__(self, trace_id: UUID):
        """
        Initialize aggregation rules.
        
        Args:
            trace_id: Trace ID for audit logging
        """
        self.trace_id = trace_id
    
    def aggregate_topic_performance(
        self,
        question_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Aggregate question-level results by topic.
        
        Args:
            question_results: List of question results, each containing:
                - topic: str
                - marks_awarded: float
                - marks_available: float
                
        Returns:
            List of topic performance dictionaries containing:
                - topic_name: str
                - questions_attempted: int
                - marks_earned: float
                - marks_available: float
                - percentage: float
        """
        topic_aggregates: Dict[str, Dict[str, Any]] = {}
        
        for result in question_results:
            topic = result.get("topic", "Unknown")
            marks_awarded = result.get("marks_awarded", 0.0)
            marks_available = result.get("marks_available", 0.0)
            
            if topic not in topic_aggregates:
                topic_aggregates[topic] = {
                    "topic_name": topic,
                    "questions_attempted": 0,
                    "marks_earned": 0.0,
                    "marks_available": 0.0,
                }
            
            topic_aggregates[topic]["questions_attempted"] += 1
            topic_aggregates[topic]["marks_earned"] += marks_awarded
            topic_aggregates[topic]["marks_available"] += marks_available
        
        # Calculate percentages
        for topic_data in topic_aggregates.values():
            if topic_data["marks_available"] > 0:
                topic_data["percentage"] = (
                    topic_data["marks_earned"] / topic_data["marks_available"]
                ) * 100
            else:
                topic_data["percentage"] = 0.0
        
        return list(topic_aggregates.values())
    
    def calculate_historical_trends(
        self,
        historical_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate trends from historical performance data.
        
        Args:
            historical_results: List of past results, each containing:
                - exam_session_id: UUID
                - exam_date: datetime
                - percentage: float
                - grade: str
                
        Returns:
            Dictionary containing:
                - trend: str (improving, stable, declining)
                - average_score: float
                - data_points: List of formatted data points
        """
        if not historical_results:
            return {
                "trend": "stable",
                "average_score": 0.0,
                "data_points": [],
            }
        
        # Sort by date
        sorted_results = sorted(
            historical_results,
            key=lambda x: x.get("exam_date", datetime.min),
        )
        
        # Calculate average
        scores = [r.get("percentage", 0.0) for r in sorted_results]
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # Determine trend (simple: compare first half to second half)
        if len(scores) >= 4:
            midpoint = len(scores) // 2
            first_half_avg = sum(scores[:midpoint]) / midpoint
            second_half_avg = sum(scores[midpoint:]) / (len(scores) - midpoint)
            
            if second_half_avg > first_half_avg + 5:  # 5% improvement
                trend = "improving"
            elif second_half_avg < first_half_avg - 5:  # 5% decline
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"  # Not enough data
        
        return {
            "trend": trend,
            "average_score": average_score,
            "data_points": sorted_results,
        }
    
    def compute_cohort_statistics(
        self,
        student_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compute statistical measures for a cohort.
        
        Args:
            student_results: List of student results, each containing:
                - student_id: UUID
                - percentage: float
                - grade: str
                
        Returns:
            Dictionary containing:
                - total_students: int
                - average_score: float
                - median_score: float
                - std_deviation: float
                - highest_score: float
                - lowest_score: float
                - grade_distribution: Dict[str, int]
        """
        if not student_results:
            return {
                "total_students": 0,
                "average_score": 0.0,
                "median_score": 0.0,
                "std_deviation": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "grade_distribution": {},
            }
        
        scores = [r.get("percentage", 0.0) for r in student_results]
        grades = [r.get("grade", "U") for r in student_results]
        
        # Calculate statistics
        total_students = len(scores)
        average_score = sum(scores) / total_students
        median_score = sorted(scores)[total_students // 2]
        highest_score = max(scores)
        lowest_score = min(scores)
        
        # Calculate standard deviation
        variance = sum((x - average_score) ** 2 for x in scores) / total_students
        std_deviation = variance ** 0.5
        
        # Grade distribution
        grade_distribution: Dict[str, int] = {}
        for grade in grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "total_students": total_students,
            "average_score": average_score,
            "median_score": median_score,
            "std_deviation": std_deviation,
            "highest_score": highest_score,
            "lowest_score": lowest_score,
            "grade_distribution": grade_distribution,
        }
    
    def categorize_performance(self, percentage: float) -> str:
        """
        Categorize performance level.
        
        Args:
            percentage: Percentage score
            
        Returns:
            Performance level (strong, satisfactory, needs_attention)
        """
        if percentage >= self.STRONG_THRESHOLD:
            return "strong"
        elif percentage >= self.SATISFACTORY_THRESHOLD:
            return "satisfactory"
        else:
            return "needs_attention"
    
    def assess_topic_difficulty(self, cohort_average: float) -> str:
        """
        Assess topic difficulty based on cohort performance.
        
        Args:
            cohort_average: Average cohort score for the topic
            
        Returns:
            Difficulty level (easy, moderate, challenging)
        """
        if cohort_average >= self.DIFFICULTY_THRESHOLDS["easy"]:
            return "easy"
        elif cohort_average >= self.DIFFICULTY_THRESHOLDS["moderate"]:
            return "moderate"
        else:
            return "challenging"
    
    def identify_strengths_and_weaknesses(
        self,
        topic_performance: List[Dict[str, Any]],
        threshold: float = STRONG_THRESHOLD,
    ) -> tuple[List[str], List[str]]:
        """
        Identify strong and weak topics.
        
        Args:
            topic_performance: List of topic performance data
            threshold: Threshold for considering a topic as strength
            
        Returns:
            Tuple of (strengths, weaknesses) - both lists of topic names
        """
        strengths = []
        weaknesses = []
        
        for topic in topic_performance:
            topic_name = topic.get("topic_name", "Unknown")
            percentage = topic.get("percentage", 0.0)
            
            if percentage >= threshold:
                strengths.append(topic_name)
            elif percentage < self.SATISFACTORY_THRESHOLD:
                weaknesses.append(topic_name)
        
        return strengths, weaknesses
