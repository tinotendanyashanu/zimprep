"""Tests for Reporting & Analytics Engine Performance Metrics.

Tests the PerformanceCalculator service to ensure all metrics are:
- Data-driven (no hardcoded values)
- Deterministic (same input = same output)
- Handle edge cases correctly (0 exams, 1 exam, etc.)

Run: pytest tests/test_reporting_performance_metrics.py -v
"""

import pytest
from datetime import datetime, timedelta
from app.engines.reporting_analytics.services.performance_calculator import PerformanceCalculator


class TestAverageGradeCalculation:
    """Test average grade calculation from exam results."""
    
    def test_no_exams_returns_none(self):
        """With 0 exams, average_grade should return None."""
        # Given: empty results list
        results = []
        
        # When: calculate average grade
        grade = PerformanceCalculator.calculate_average_grade(results)
        
        # Then: returns None
        assert grade is None
    
    def test_single_exam_returns_correct_grade(self):
        """With 1 exam, should return that exam's grade."""
        # Given: single exam with 75%
        results = [
            {"percentage": 75.0, "grade": "B"}
        ]
        
        # When: calculate average
        grade = PerformanceCalculator.calculate_average_grade(results)
        
        # Then: returns B (70-79.99 range)
        assert grade == "B"
    
    def test_multiple_exams_averages_correctly(self):
        """With multiple exams, should calculate correct average."""
        # Given: exams with [60%, 70%, 80%] → avg = 70%
        results = [
            {"percentage": 60.0},
            {"percentage": 70.0},
            {"percentage": 80.0}
        ]
        
        # When: calculate average
        grade = PerformanceCalculator.calculate_average_grade(results)
        
        # Then: returns B (average 70%)
        assert grade == "B"
    
    def test_grade_boundaries_are_correct(self):
        """Test all grade boundaries resolve correctly."""
        test_cases = [
            (95.0, "A*"),  # 90-100
            (85.0, "A"),   # 80-89.99
            (75.0, "B"),   # 70-79.99
            (65.0, "C"),   # 60-69.99
            (55.0, "D"),   # 50-59.99
            (45.0, "E"),   # 40-49.99
            (35.0, "U"),   # 0-39.99
        ]
        
        for percentage, expected_grade in test_cases:
            results = [{"percentage": percentage}]
            grade = PerformanceCalculator.calculate_average_grade(results)
            assert grade == expected_grade, f"Expected {expected_grade} for {percentage}%"
    
    def test_handles_missing_percentage_field(self):
        """Should skip results without percentage field."""
        # Given: mix of valid and invalid results
        results = [
            {"percentage": 80.0},
            {"grade": "B"},  # Missing percentage
            {"percentage": 60.0},
        ]
        
        # When: calculate average
        grade = PerformanceCalculator.calculate_average_grade(results)
        
        # Then: calculates from valid results only (80 + 60) / 2 = 70 → B
        assert grade == "B"


class TestImprovementTrend:
    """Test improvement trend calculation."""
    
    def test_no_exams_returns_insufficient_data(self):
        """With 0 exams, trend should be insufficient_data."""
        results = []
        trend = PerformanceCalculator.calculate_improvement_trend(results)
        assert trend == "insufficient_data"
    
    def test_single_exam_returns_insufficient_data(self):
        """With 1 exam, cannot calculate trend."""
        results = [
            {"percentage": 75.0, "issued_at": datetime.now()}
        ]
        trend = PerformanceCalculator.calculate_improvement_trend(results)
        assert trend == "insufficient_data"
    
    def test_improving_scores_returns_improving(self):
        """Scores going up should return 'improving'."""
        # Given: scores [60%, 70%, 80%] over time
        base_time = datetime.now()
        results = [
            {"percentage": 60.0, "issued_at": base_time - timedelta(days=20)},
            {"percentage": 70.0, "issued_at": base_time - timedelta(days=10)},
            {"percentage": 80.0, "issued_at": base_time},
        ]
        
        # When: calculate trend
        trend = PerformanceCalculator.calculate_improvement_trend(results)
        
        # Then: returns improving (delta = +20%)
        assert trend == "improving"
    
    def test_declining_scores_returns_declining(self):
        """Scores going down should return 'declining'."""
        # Given: scores [80%, 70%, 60%]
        base_time = datetime.now()
        results = [
            {"percentage": 80.0, "issued_at": base_time - timedelta(days=20)},
            {"percentage": 70.0, "issued_at": base_time - timedelta(days=10)},
            {"percentage": 60.0, "issued_at": base_time},
        ]
        
        # When: calculate trend
        trend = PerformanceCalculator.calculate_improvement_trend(results)
        
        # Then: returns declining (delta = -20%)
        assert trend == "declining"
    
    def test_stable_scores_returns_stable(self):
        """Scores with minimal change should return 'stable'."""
        # Given: scores [75%, 74%, 76%] (within 5% threshold)
        base_time = datetime.now()
        results = [
            {"percentage": 75.0, "issued_at": base_time - timedelta(days=20)},
            {"percentage": 74.0, "issued_at": base_time - timedelta(days=10)},
            {"percentage": 76.0, "issued_at": base_time},
        ]
        
        # When: calculate trend (default threshold = 5%)
        trend = PerformanceCalculator.calculate_improvement_trend(results)
        
        # Then: returns stable (delta = +1%, < 5%)
        assert trend == "stable"
    
    def test_uses_recent_window_only(self):
        """Should only analyze last N attempts (window_size)."""
        # Given: old declining trend, but recent improving
        base_time = datetime.now()
        results = [
            {"percentage": 90.0, "issued_at": base_time - timedelta(days=40)},  # Old
            {"percentage": 50.0, "issued_at": base_time - timedelta(days=30)},  # Old
            {"percentage": 60.0, "issued_at": base_time - timedelta(days=20)},  # Recent
            {"percentage": 70.0, "issued_at": base_time - timedelta(days=10)},  # Recent
            {"percentage": 80.0, "issued_at": base_time},                       # Recent
        ]
        
        # When: calculate with window_size=3
        trend = PerformanceCalculator.calculate_improvement_trend(results, window_size=3)
        
        # Then: uses last 3 only [60, 70, 80] → improving
        assert trend == "improving"


class TestStrengthsIdentification:
    """Test topic strengths identification."""
    
    def test_no_exams_returns_empty_list(self):
        """With 0 exams, strengths should be empty."""
        results = []
        strengths = PerformanceCalculator.identify_strengths(results)
        assert strengths == []
    
    def test_no_topic_breakdown_returns_empty(self):
        """Exams without topic_breakdown should return empty."""
        results = [
            {"percentage": 75.0},  # No topic_breakdown
            {"percentage": 80.0},
        ]
        strengths = PerformanceCalculator.identify_strengths(results)
        assert strengths == []
    
    def test_identifies_top_performing_topics(self):
        """Should return topics with highest average scores."""
        # Given: Math (85%), Physics (65%), Chemistry (75%)
        results = [
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 90.0},
                    {"topic_name": "Physics", "percentage": 60.0},
                    {"topic_name": "Chemistry", "percentage": 70.0},
                ]
            },
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 80.0},
                    {"topic_name": "Physics", "percentage": 70.0},
                    {"topic_name": "Chemistry", "percentage": 80.0},
                ]
            }
        ]
        
        # When: identify strengths (top 3)
        strengths = PerformanceCalculator.identify_strengths(results, top_n=3)
        
        # Then: Math (85%), Chemistry (75%), Physics (65%)
        assert strengths == ["Mathematics", "Chemistry", "Physics"]
    
    def test_respects_top_n_parameter(self):
        """Should only return top N topics."""
        results = [
            {
                "topic_breakdown": [
                    {"topic_name": "Math", "percentage": 90.0},
                    {"topic_name": "Physics", "percentage": 80.0},
                    {"topic_name": "Chemistry", "percentage": 70.0},
                    {"topic_name": "Biology", "percentage": 60.0},
                ]
            }
        ]
        
        # When: request top 2
        strengths = PerformanceCalculator.identify_strengths(results, top_n=2)
        
        # Then: returns only top 2
        assert len(strengths) == 2
        assert strengths == ["Math", "Physics"]


class TestWeaknessesIdentification:
    """Test topic weaknesses identification."""
    
    def test_no_exams_returns_empty_list(self):
        """With 0 exams, weaknesses should be empty."""
        results = []
        weaknesses = PerformanceCalculator.identify_weaknesses(results)
        assert weaknesses == []
    
    def test_identifies_lowest_performing_topics(self):
        """Should return topics with lowest average scores."""
        # Given: Math (85%), Physics (45%), Chemistry (65%)
        results = [
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 90.0},
                    {"topic_name": "Physics", "percentage": 40.0},
                    {"topic_name": "Chemistry", "percentage": 60.0},
                ]
            },
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 80.0},
                    {"topic_name": "Physics", "percentage": 50.0},
                    {"topic_name": "Chemistry", "percentage": 70.0},
                ]
            }
        ]
        
        # When: identify weaknesses
        weaknesses = PerformanceCalculator.identify_weaknesses(results, bottom_n=3)
        
        # Then: Physics (45%), Chemistry (65%), Math (85%)
        assert weaknesses == ["Physics", "Chemistry", "Mathematics"]
    
    def test_filters_topics_with_insufficient_attempts(self):
        """Should exclude topics with < min_attempts."""
        # Given: Math (2 attempts), Physics (1 attempt)
        results = [
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 40.0},
                    {"topic_name": "Physics", "percentage": 30.0},
                ]
            },
            {
                "topic_breakdown": [
                    {"topic_name": "Mathematics", "percentage": 40.0},
                    # Physics not attempted in second exam
                ]
            }
        ]
        
        # When: identify weaknesses (min_attempts=2)
        weaknesses = PerformanceCalculator.identify_weaknesses(results, min_attempts=2)
        
        # Then: only Math included (Physics excluded, only 1 attempt)
        assert weaknesses == ["Mathematics"]
        assert "Physics" not in weaknesses
    
    def test_respects_bottom_n_parameter(self):
        """Should only return bottom N topics."""
        results = [
            {
                "topic_breakdown": [
                    {"topic_name": "Math", "percentage": 90.0},
                    {"topic_name": "Physics", "percentage": 80.0},
                    {"topic_name": "Chemistry", "percentage": 40.0},
                    {"topic_name": "Biology", "percentage": 30.0},
                ]
            },
            {
                "topic_breakdown": [
                    {"topic_name": "Math", "percentage": 90.0},
                    {"topic_name": "Physics", "percentage": 80.0},
                    {"topic_name": "Chemistry", "percentage": 40.0},
                    {"topic_name": "Biology", "percentage": 30.0},
                ]
            }
        ]
        
        # When: request bottom 2
        weaknesses = PerformanceCalculator.identify_weaknesses(results, bottom_n=2)
        
        # Then: returns only bottom 2
        assert len(weaknesses) == 2
        assert weaknesses == ["Biology", "Chemistry"]


class TestDeterminism:
    """Test that calculations are deterministic."""
    
    def test_same_input_produces_same_output(self):
        """Same exam data should always produce identical metrics."""
        # Given: identical result sets
        base_time = datetime.now()
        results = [
            {
                "percentage": 75.0,
                "issued_at": base_time - timedelta(days=10),
                "topic_breakdown": [
                    {"topic_name": "Math", "percentage": 80.0}
                ]
            },
            {
                "percentage": 85.0,
                "issued_at": base_time,
                "topic_breakdown": [
                    {"topic_name": "Math", "percentage": 90.0}
                ]
            }
        ]
        
        # When: calculate metrics multiple times
        grades = [PerformanceCalculator.calculate_average_grade(results) for _ in range(10)]
        trends = [PerformanceCalculator.calculate_improvement_trend(results) for _ in range(10)]
        strengths_list = [PerformanceCalculator.identify_strengths(results) for _ in range(10)]
        
        # Then: all results are identical
        assert len(set(grades)) == 1
        assert len(set(trends)) == 1
        assert all(s == strengths_list[0] for s in strengths_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
