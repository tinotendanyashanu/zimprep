"""
Student data routes — history, recommendations, subject progress.

student_id is the Supabase auth.users UUID, passed as a path param.
All reads go through service_role (RLS is enforced at the DB level for
direct client reads; here we trust the frontend to send the correct ID).
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException
from supabase import create_client

from core.config import settings

router = APIRouter(prefix="/students", tags=["students"])


def _sb():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ---------------------------------------------------------------------------
# Attempt history
# ---------------------------------------------------------------------------

@router.get("/{student_id}/history")
def get_history(student_id: str, limit: int = 30):
    """Return recent exam/practice sessions with scores."""
    sb = _sb()
    sessions = (
        sb.table("session")
        .select("id, mode, started_at, completed_at, status, paper(id, year, paper_number, subject(name, level))")
        .eq("student_id", student_id)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )

    result = []
    for s in sessions:
        attempts = (
            sb.table("attempt")
            .select("ai_score, question(marks)")
            .eq("session_id", s["id"])
            .execute()
            .data
        )
        total_score = sum((a.get("ai_score") or 0) for a in attempts)
        total_marks = sum(((a.get("question") or {}).get("marks") or 0) for a in attempts)

        paper = s.get("paper") or {}
        subject = paper.get("subject") or {}
        result.append({
            "attempt_id": s["id"],
            "subject": subject.get("name", "Unknown"),
            "paper": f"Paper {paper.get('paper_number', '?')}",
            "year": paper.get("year"),
            "score": total_score,
            "total": total_marks or 100,
            "date": ((s.get("completed_at") or s.get("started_at") or "")[:10]),
            "status": "Completed" if s.get("status") == "completed" else "In Progress",
            "mode": s.get("mode", "exam"),
        })
    return result


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@router.get("/{student_id}/recommendations")
def get_recommendations(student_id: str):
    """
    Generate recommendations from:
    1. weak_topic rows (high fail ratio) → TOPIC type
    2. syllabus_chunk rows not in syllabus_coverage → uncovered topics
    """
    sb = _sb()
    recs = []

    # 1. Weak topic recs
    weak = (
        sb.table("weak_topic")
        .select("id, topic_name, attempt_count, fail_count, subject_id, subject(name)")
        .eq("student_id", student_id)
        .gt("attempt_count", 0)
        .order("fail_count", desc=True)
        .limit(10)
        .execute()
        .data
    )
    for wt in weak:
        fail_ratio = wt["fail_count"] / max(wt["attempt_count"], 1)
        if fail_ratio < 0.3:
            continue
        subject_name = (wt.get("subject") or {}).get("name", "Unknown")
        recs.append({
            "id": wt["id"],
            "type": "TOPIC",
            "title": f"Revise {wt['topic_name']}",
            "explanation": (
                f"You answered {wt['fail_count']} of {wt['attempt_count']} "
                f"{wt['topic_name']} questions incorrectly."
            ),
            "evidence": {
                "attempts_considered": wt["attempt_count"],
                "related_subject": subject_name,
                "related_topic": wt["topic_name"],
                "reason": f"Fail rate {int(fail_ratio * 100)}% — needs revision.",
            },
            "action": {
                "label": "Practice This Topic",
                "route": f"/practice?subject_id={wt['subject_id']}&topic={wt['topic_name']}",
            },
        })

    # 2. Coverage gaps
    covered = (
        sb.table("syllabus_coverage")
        .select("topic_name, subject_id")
        .eq("student_id", student_id)
        .eq("attempted", True)
        .execute()
        .data
    )
    covered_keys = {(c["subject_id"], c["topic_name"]) for c in covered}

    chunks = (
        sb.table("syllabus_chunk")
        .select("topic_name, subject_id, subject(name)")
        .limit(60)
        .execute()
        .data
    )
    for chunk in chunks:
        if len(recs) >= 8:
            break
        key = (chunk["subject_id"], chunk["topic_name"])
        if key in covered_keys:
            continue
        subject_name = (chunk.get("subject") or {}).get("name", "Unknown")
        recs.append({
            "id": f"gap_{chunk['subject_id']}_{chunk['topic_name'][:16]}",
            "type": "TOPIC",
            "title": f"Uncovered: {chunk['topic_name']}",
            "explanation": f"You have not practiced any {chunk['topic_name']} questions yet.",
            "evidence": {
                "attempts_considered": 0,
                "related_subject": subject_name,
                "related_topic": chunk["topic_name"],
                "reason": "No attempts recorded for this syllabus area.",
            },
            "action": {
                "label": "Start Practice",
                "route": f"/practice?subject_id={chunk['subject_id']}&topic={chunk['topic_name']}",
            },
        })

    return recs[:8]


# ---------------------------------------------------------------------------
# Subject progress
# ---------------------------------------------------------------------------

@router.get("/{student_id}/progress/{subject_id}")
def get_subject_progress(student_id: str, subject_id: str):
    """Return attempt stats and weak topics for a student/subject pair."""
    sb = _sb()

    subject = None
    try:
        subject = (
            sb.table("subject").select("name, level").eq("id", subject_id).single().execute().data
        )
    except Exception:
        pass

    sessions = (
        sb.table("session")
        .select("id")
        .eq("student_id", student_id)
        .execute()
        .data
    )
    session_ids = [s["id"] for s in sessions]

    subject_attempts = []
    if session_ids:
        all_attempts = (
            sb.table("attempt")
            .select("ai_score, question(marks, subject_id)")
            .in_("session_id", session_ids)
            .execute()
            .data
        )
        subject_attempts = [
            a for a in all_attempts
            if (a.get("question") or {}).get("subject_id") == subject_id
        ]

    scores = [a.get("ai_score") or 0 for a in subject_attempts]
    max_scores = [(a.get("question") or {}).get("marks") or 1 for a in subject_attempts]
    pct = [s / m * 100 for s, m in zip(scores, max_scores)]

    weak = (
        sb.table("weak_topic")
        .select("topic_name")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .order("fail_count", desc=True)
        .limit(5)
        .execute()
        .data
    )

    return {
        "subject": (subject or {}).get("name", ""),
        "level": (subject or {}).get("level", ""),
        "attempts": len(subject_attempts),
        "average_score": int(sum(pct) / len(pct)) if pct else 0,
        "best_score": int(max(pct)) if pct else 0,
        "weak_topics": [w["topic_name"] for w in weak],
        "suggested_focus": [w["topic_name"] for w in weak[:3]],
    }


# ---------------------------------------------------------------------------
# Parent: overview of linked student
# ---------------------------------------------------------------------------

@router.get("/parent/{parent_id}/overview")
def get_parent_overview(parent_id: str):
    """Return overview data for a parent's linked student."""
    sb = _sb()

    try:
        student = (
            sb.table("student")
            .select("id, name, level, subscription_tier")
            .eq("parent_id", parent_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        raise HTTPException(404, "No linked student found for this parent")

    student_id = student["id"]

    # Count sessions
    sessions = (
        sb.table("session")
        .select("id, started_at, status")
        .eq("student_id", student_id)
        .order("started_at", desc=True)
        .execute()
        .data
    )
    total_attempts = len(sessions)
    last_activity = ""
    if sessions:
        last_activity = (sessions[0].get("started_at") or "")[:10]

    # Subjects attempted
    subject_ids = set()
    for s in sessions[:50]:
        pass  # would need join — skip for now

    # Weak topics count as engagement signal
    weak = sb.table("weak_topic").select("subject_id").eq("student_id", student_id).execute().data
    subject_ids = {w["subject_id"] for w in weak}

    subjects = []
    if subject_ids:
        rows = sb.table("subject").select("name").in_("id", list(subject_ids)).execute().data
        subjects = [r["name"] for r in rows]

    # Engagement status heuristic
    if total_attempts >= 20:
        engagement = "CONSISTENT"
    elif total_attempts >= 5:
        engagement = "ACTIVE"
    elif total_attempts >= 1:
        engagement = "GETTING STARTED"
    else:
        engagement = "NOT STARTED"

    level_labels = {"Grade7": "Grade 7", "O": "ZIMSEC O-Level", "A": "ZIMSEC A-Level"}

    return {
        "student_name": student.get("name", "Student"),
        "exam_level": level_labels.get(student.get("level", "O"), "ZIMSEC O-Level"),
        "subjects": subjects,
        "total_attempts": total_attempts,
        "last_activity": last_activity,
        "engagement_status": engagement,
    }
