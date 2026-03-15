"""
Papers router — public read-only endpoints for subjects, papers, and questions.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from db.client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/subjects")
def list_subjects() -> list[dict[str, Any]]:
    """List all subjects with a count of available (ready) papers."""
    supabase = get_supabase()
    subjects = supabase.table("subject").select("id, name, level").order("name").execute()

    # Count ready papers per subject
    ready_papers = (
        supabase.table("paper").select("subject_id").eq("status", "ready").execute()
    )
    counts: dict[str, int] = {}
    for p in ready_papers.data:
        sid = p["subject_id"]
        counts[sid] = counts.get(sid, 0) + 1

    return [
        {**s, "paper_count": counts.get(s["id"], 0)}
        for s in subjects.data
    ]


@router.get("/subjects/{subject_id}/papers")
def list_papers_for_subject(subject_id: str) -> list[dict[str, Any]]:
    """List ready papers for a given subject, newest first."""
    supabase = get_supabase()
    result = (
        supabase.table("paper")
        .select("id, year, paper_number, status")
        .eq("subject_id", subject_id)
        .eq("status", "ready")
        .order("year", desc=True)
        .execute()
    )
    return result.data


@router.get("/{paper_id}/questions")
def list_questions_for_paper(paper_id: str) -> list[dict[str, Any]]:
    """List all questions for a paper, with mcq_answer attached where applicable."""
    supabase = get_supabase()

    questions_result = (
        supabase.table("question")
        .select("*")
        .eq("paper_id", paper_id)
        .order("question_number")
        .execute()
    )
    if not questions_result.data:
        # Check if paper exists at all
        paper = supabase.table("paper").select("id").eq("id", paper_id).single().execute()
        if not paper.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        return []

    questions = questions_result.data

    # Attach correct_option for MCQ questions
    mcq_ids = [q["id"] for q in questions if q.get("question_type") == "mcq"]
    mcq_map: dict[str, str] = {}
    if mcq_ids:
        mcq_result = (
            supabase.table("mcq_answer")
            .select("question_id, correct_option")
            .in_("question_id", mcq_ids)
            .execute()
        )
        mcq_map = {row["question_id"]: row["correct_option"] for row in mcq_result.data}

    for q in questions:
        q["mcq_answer"] = mcq_map.get(q["id"])

    return questions
