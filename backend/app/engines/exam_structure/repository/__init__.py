"""Repository package for Exam Structure Engine.

ACTION 3: Phantom repositories removed.

ONLY ScheduleRepository remains (uses exam_schedules from runtime collections).
All exam structure is now DERIVED from canonical_questions.
"""

from app.engines.exam_structure.repository.schedule_repo import ScheduleRepository

__all__ = [
    "ScheduleRepository",
]
