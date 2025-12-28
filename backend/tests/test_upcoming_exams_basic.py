"""Basic test for upcoming exams integration.

Run with: pytest tests/test_upcoming_exams_basic.py -v
"""

import pytest
from datetime import datetime, timedelta


def test_upcoming_exams_schema_structure():
    """Test that upcoming exam schema has required fields."""
    # Sample upcoming exam object
    upcoming_exam = {
        "exam_id": "zimsec_biology_p2_2025_may",
        "subject": "Biology",
        "paper": "Paper 2",
        "scheduled_date": "2025-05-14T09:00:00Z",
        "duration_minutes": 150,
        "status": "scheduled"
    }
    
    # Verify required fields exist
    assert "exam_id" in upcoming_exam
    assert "subject" in upcoming_exam
    assert "paper" in upcoming_exam
    assert "scheduled_date" in upcoming_exam
    assert "duration_minutes" in upcoming_exam
    assert "status" in upcoming_exam
    
    # Verify types
    assert isinstance(upcoming_exam["exam_id"], str)
    assert isinstance(upcoming_exam["subject"], str)
    assert isinstance(upcoming_exam["paper"], str)
    assert isinstance(upcoming_exam["scheduled_date"], str)
    assert isinstance(upcoming_exam["duration_minutes"], int)
    assert upcoming_exam["duration_minutes"] > 0
    assert upcoming_exam["status"] in ["scheduled", "in_progress", "completed", "cancelled"]


def test_upcoming_exams_list_can_be_empty():
    """Test that upcoming_exams can be empty list."""
    upcoming_exams = []
    assert isinstance(upcoming_exams, list)
    assert len(upcoming_exams) == 0


def test_upcoming_exams_multiple_items():
    """Test that upcoming_exams can contain multiple items."""
    upcoming_exams = [
        {
            "exam_id": "zimsec_math_p1_2025",
            "subject": "Mathematics",
            "paper": "Paper 1",
            "scheduled_date": "2025-05-15T09:00:00Z",
            "duration_minutes": 120,
            "status": "scheduled"
        },
        {
            "exam_id": "zimsec_bio_p2_2025",
            "subject": "Biology",
            "paper": "Paper 2",
            "scheduled_date": "2025-05-20T09:00:00Z",
            "duration_minutes": 150,
            "status": "scheduled"
        }
    ]
    
    assert len(upcoming_exams) == 2
    # Should be in chronological order
    date1 = datetime.fromisoformat(upcoming_exams[0]["scheduled_date"].replace("Z", "+00:00"))
    date2 = datetime.fromisoformat(upcoming_exams[1]["scheduled_date"].replace("Z", "+00:00"))
    assert date1 < date2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
