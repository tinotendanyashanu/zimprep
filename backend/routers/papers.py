"""
Papers router — public read-only endpoints for subjects, papers, and questions.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from db.client import get_supabase
from services.adaptive import get_weak_topics, pick_next_question

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/subjects")
def list_subjects(
    exam_board: Optional[str] = Query(default=None),
    level: Optional[str] = Query(default=None),
) -> list[dict[str, Any]]:
    """List subjects, optionally filtered by exam_board and/or level."""
    supabase = get_supabase()
    query = supabase.table("subject").select("id, name, level, exam_board").order("name")
    if exam_board:
        query = query.eq("exam_board", exam_board)
    if level:
        query = query.eq("level", level)
    subjects = query.execute()

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
        .neq("diagram_status", "failed")   # hide questions pending diagram review
        .order("question_number")
        .execute()
    )
    if not questions_result.data:
        # Check if paper exists at all
        paper = supabase.table("paper").select("id").eq("id", paper_id).maybe_single().execute()
        if not paper or not paper.data:
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


@router.get("/questions/next")
def next_question(
    subject_id: str = Query(...),
    student_id: str = Query(...),
    topic: Optional[str] = Query(None),
    paper_number: Optional[int] = Query(None),
) -> dict[str, Any]:
    """Return the next adaptively selected question for a student."""
    question = pick_next_question(subject_id, student_id, topic, paper_number)
    if question is None:
        raise HTTPException(status_code=404, detail="No questions available")
    return question


@router.get("/subjects/{subject_id}/topics")
def list_topics_for_subject(subject_id: str) -> list[str]:
    """Return distinct topic tags across all ready papers for a subject."""
    supabase = get_supabase()
    papers = (
        supabase.table("paper")
        .select("id")
        .eq("subject_id", subject_id)
        .eq("status", "ready")
        .execute()
    )
    paper_ids = [p["id"] for p in papers.data]
    if not paper_ids:
        return []

    questions = (
        supabase.table("question")
        .select("topic_tags")
        .in_("paper_id", paper_ids)
        .execute()
    )
    topics: set[str] = set()
    for q in questions.data:
        for tag in (q.get("topic_tags") or []):
            topics.add(tag)
    return sorted(topics)


@router.get("/subjects/{subject_id}/weak-topics")
def weak_topics_for_subject(
    subject_id: str,
    student_id: str = Query(...),
) -> list[dict[str, Any]]:
    """Return weak topic stats for a student within a subject."""
    return get_weak_topics(subject_id, student_id)
