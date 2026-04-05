"""
Adaptive question selection — weighted random pick based on topic weakness.
"""
from __future__ import annotations

import random
from typing import Any

from db.client import get_supabase


def _topic_weight(fail_ratio: float | None) -> float:
    """Return priority weight for a topic based on fail ratio."""
    if fail_ratio is None:
        return 3.0  # Never attempted
    if fail_ratio > 0.6:
        return 2.5
    if fail_ratio >= 0.3:
        return 1.5
    return 1.0


def pick_next_question(
    subject_id: str,
    student_id: str,
    topic: str | None = None,
    paper_number: int | None = None,
) -> dict[str, Any] | None:
    """
    Return the next question for a student using the adaptive algorithm.

    Steps:
    1. Verify the subject belongs to the student's exam_board + level.
    2. Fetch all ready questions for the subject (filtered by topic if given).
    3. Fetch student's recent attempt question IDs (last 20) to penalise.
    4. Compute per-topic fail ratios from past marked attempts.
    5. Score each question; pick via weighted random.
    """
    supabase = get_supabase()

    # 1. Verify subject matches the student's board + level
    student_row = (
        supabase.table("student")
        .select("exam_board, level")
        .eq("id", student_id)
        .maybe_single()
        .execute()
    )
    if student_row and student_row.data:
        student_board = student_row.data.get("exam_board")
        student_level = student_row.data.get("level")
        subject_row = (
            supabase.table("subject")
            .select("exam_board, level")
            .eq("id", subject_id)
            .maybe_single()
            .execute()
        )
        if subject_row and subject_row.data:
            if student_board and subject_row.data.get("exam_board") != student_board:
                return None
            if student_level and subject_row.data.get("level") != student_level:
                return None

    # 2. Get all ready papers for this subject (optionally filtered by paper_number)
    papers_query = (
        supabase.table("paper")
        .select("id")
        .eq("subject_id", subject_id)
        .eq("status", "ready")
    )
    if paper_number is not None:
        papers_query = papers_query.eq("paper_number", paper_number)
    papers = papers_query.execute()
    paper_ids = [p["id"] for p in papers.data]
    if not paper_ids:
        return None

    # 2. Fetch questions (optionally filtered by topic tag)
    query = supabase.table("question").select("*").in_("paper_id", paper_ids)
    if topic:
        query = query.contains("topic_tags", [topic])
    questions = query.execute().data
    if not questions:
        return None

    # Attach mcq_answer for MCQ questions
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

    # 3. Fetch questions (optionally filtered by topic tag) — already done above as step 2
    # 4. Recently attempted question IDs (penalise to reduce repetition)
    recent_result = (
        supabase.table("attempt")
        .select("question_id, session!inner(student_id)")
        .eq("session.student_id", student_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    recent_qids = {a["question_id"] for a in (recent_result.data or [])}

    # 5. Per-topic fail ratios from all marked attempts on these questions
    all_topics = {tag for q in questions for tag in (q.get("topic_tags") or [])}
    topic_fail: dict[str, float | None] = {t: None for t in all_topics}

    if all_topics:
        all_q_ids = [q["id"] for q in questions]
        attempts_data = (
            supabase.table("attempt")
            .select("question_id, ai_score, session!inner(student_id)")
            .eq("session.student_id", student_id)
            .in_("question_id", all_q_ids)
            .not_.is_("ai_score", "null")
            .execute()
        )
        q_topics = {q["id"]: (q.get("topic_tags") or []) for q in questions}
        max_marks = {q["id"]: (q.get("marks") or 1) for q in questions}
        topic_scores: dict[str, list[float]] = {t: [] for t in all_topics}

        for attempt in (attempts_data.data or []):
            qid = attempt["question_id"]
            score = attempt.get("ai_score") or 0
            marks = max_marks.get(qid, 1) or 1
            ratio = score / marks
            for t in q_topics.get(qid, []):
                topic_scores[t].append(ratio)

        for t, scores in topic_scores.items():
            if scores:
                topic_fail[t] = 1.0 - (sum(scores) / len(scores))

    # 6. Score each question and pick via weighted random
    def question_weight(q: dict[str, Any]) -> float:
        tags = q.get("topic_tags") or []
        w = max((_topic_weight(topic_fail.get(t)) for t in tags), default=1.0)
        if q["id"] in recent_qids:
            w *= 0.3
        return w

    weights = [question_weight(q) for q in questions]
    total = sum(weights)
    if total == 0:
        return random.choice(questions)

    r = random.uniform(0, total)
    cumulative = 0.0
    for q, w in zip(questions, weights):
        cumulative += w
        if r <= cumulative:
            return q
    return questions[-1]


def get_weak_topics(subject_id: str, student_id: str) -> list[dict[str, Any]]:
    """
    Return topics for this subject sorted by fail ratio (worst first).
    Only includes topics with at least one marked attempt by this student.
    """
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

    questions_result = (
        supabase.table("question")
        .select("id, marks, topic_tags")
        .in_("paper_id", paper_ids)
        .execute()
    )
    questions = questions_result.data
    if not questions:
        return []

    all_q_ids = [q["id"] for q in questions]
    attempts_data = (
        supabase.table("attempt")
        .select("question_id, ai_score, session!inner(student_id)")
        .eq("session.student_id", student_id)
        .in_("question_id", all_q_ids)
        .not_.is_("ai_score", "null")
        .execute()
    )

    q_topics = {q["id"]: (q.get("topic_tags") or []) for q in questions}
    max_marks = {q["id"]: (q.get("marks") or 1) for q in questions}
    topic_scores: dict[str, list[float]] = {}
    topic_count: dict[str, int] = {}

    for attempt in (attempts_data.data or []):
        qid = attempt["question_id"]
        score = attempt.get("ai_score") or 0
        marks = max_marks.get(qid, 1) or 1
        ratio = score / marks
        for t in q_topics.get(qid, []):
            topic_scores.setdefault(t, []).append(ratio)
            topic_count[t] = topic_count.get(t, 0) + 1

    results = [
        {
            "topic": topic,
            "fail_ratio": round(1.0 - sum(scores) / len(scores), 3),
            "attempt_count": topic_count[topic],
        }
        for topic, scores in topic_scores.items()
    ]
    results.sort(key=lambda x: x["fail_ratio"], reverse=True)
    return results
