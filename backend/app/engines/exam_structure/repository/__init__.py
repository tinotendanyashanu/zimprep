"""Repository package for Exam Structure Engine.

Provides read-only MongoDB access to exam structure data.
"""

from app.engines.exam_structure.repository.subject_repo import SubjectRepository
from app.engines.exam_structure.repository.syllabus_repo import SyllabusRepository
from app.engines.exam_structure.repository.paper_repo import PaperRepository
from app.engines.exam_structure.repository.schedule_repo import ScheduleRepository

__all__ = [
    "SubjectRepository",
    "SyllabusRepository",
    "PaperRepository",
    "ScheduleRepository",
]
