from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class Subject(BaseModel):
    id: str
    name: str
    level: str  # 'Grade7' | 'O' | 'A'
    created_at: datetime


class Paper(BaseModel):
    id: str
    subject_id: str
    year: int
    paper_number: int
    pdf_url: str
    status: str  # 'processing' | 'ready' | 'error'
    created_at: datetime


class Question(BaseModel):
    id: str
    paper_id: str
    subject_id: str
    question_number: str
    sub_question: Optional[str] = None
    section: Optional[str] = None
    marks: int
    text: str
    has_image: bool
    image_url: Optional[str] = None
    topic_tags: list[str]
    question_type: str  # 'written' | 'mcq'
    created_at: datetime


class MCQAnswer(BaseModel):
    id: str
    question_id: str
    correct_option: str  # 'A' | 'B' | 'C' | 'D'


class SyllabusChunk(BaseModel):
    id: str
    subject_id: str
    topic_name: str
    content: str
    level: str
    created_at: datetime


class Student(BaseModel):
    id: str
    email: str
    name: str
    level: str
    subscription_tier: str  # 'starter' | 'standard' | 'prestige'
    created_at: datetime


class Parent(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


class Session(BaseModel):
    id: str
    student_id: str
    paper_id: str
    mode: str  # 'exam' | 'practice'
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str


class Attempt(BaseModel):
    id: str
    session_id: str
    question_id: str
    student_answer: Optional[str] = None
    answer_image_url: Optional[str] = None
    extracted_text: Optional[str] = None
    ai_score: Optional[int] = None
    ai_feedback: Optional[Any] = None
    ai_references: Optional[Any] = None
    marked_at: Optional[datetime] = None
    flagged: bool = False
    flag_resolved: bool = False


class WeakTopic(BaseModel):
    id: str
    student_id: str
    subject_id: str
    topic_name: str
    attempt_count: int = 0
    fail_count: int = 0
    last_attempted: datetime


class SyllabusCoverage(BaseModel):
    id: str
    student_id: str
    subject_id: str
    topic_name: str
    attempted: bool = False
    last_attempted: Optional[datetime] = None
