"""
Public catalog routes — subjects, papers, questions.
No auth required; data is filtered to 'ready'/'approved' status only.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException
from supabase import create_client

from core.config import settings

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _sb():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.get("/subjects")
def list_subjects(name: Optional[str] = None, level: Optional[str] = None):
    """List all subjects. Optionally filter by name (partial match) or level."""
    q = _sb().table("subject").select("id, name, level")
    if name:
        q = q.ilike("name", f"%{name}%")
    if level:
        q = q.eq("level", level)
    return q.order("name").execute().data


@router.get("/subjects/{subject_id}/papers")
def list_subject_papers(subject_id: str):
    """List available (ready) papers for a subject, grouped by year."""
    rows = (
        _sb()
        .table("paper")
        .select("id, year, paper_number, status")
        .eq("subject_id", subject_id)
        .eq("status", "ready")
        .order("year", desc=True)
        .order("paper_number")
        .execute()
        .data
    )
    return rows


@router.get("/papers")
def find_paper(subject_id: str, year: int, paper_number: int):
    """Look up the UUID of a specific paper by subject + year + paper_number."""
    try:
        row = (
            _sb()
            .table("paper")
            .select("id, year, paper_number, status")
            .eq("subject_id", subject_id)
            .eq("year", year)
            .eq("paper_number", paper_number)
            .single()
            .execute()
            .data
        )
    except Exception:
        row = None
    if not row:
        raise HTTPException(404, "Paper not found")
    return row


@router.get("/papers/{paper_id}")
def get_paper(paper_id: str):
    """
    Return full paper metadata + approved questions (with MCQ answers).
    Students call this to load the question list before starting an exam.
    """
    try:
        paper = (
            _sb()
            .table("paper")
            .select("*, subject(id, name, level)")
            .eq("id", paper_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        paper = None
    if not paper:
        raise HTTPException(404, "Paper not found")

    questions = (
        _sb()
        .table("question")
        .select("*, mcq_answer(*)")
        .eq("paper_id", paper_id)
        .eq("qa_status", "approved")
        .order("question_number")
        .execute()
        .data
    )

    subject = paper.pop("subject", {}) or {}
    return {
        **paper,
        "subject_name": subject.get("name", ""),
        "subject_level": subject.get("level", "O"),
        "questions": questions,
    }
