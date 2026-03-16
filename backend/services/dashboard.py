"""
Dashboard service — Readiness Index, syllabus coverage, streaks, session history.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from db.client import get_supabase


def get_streak(student_id: str) -> dict[str, int]:
    """Compute current and longest streak from completed/submitted sessions."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("completed_at")
        .eq("student_id", student_id)
        .in_("status", ["submitted", "completed"])
        .not_.is_("completed_at", "null")
        .order("completed_at", desc=True)
        .execute()
    )
    sessions = result.data or []

    # Collect unique calendar dates (UTC)
    dates: set[str] = set()
    for s in sessions:
        if s.get("completed_at"):
            dt = s["completed_at"][:10]  # YYYY-MM-DD
            dates.add(dt)

    if not dates:
        return {"current": 0, "longest": 0}

    sorted_dates = sorted(dates, reverse=True)
    today = datetime.now(timezone.utc).date()

    # Current streak — must include today or yesterday to be active
    current = 0
    check = today
    for date_str in sorted_dates:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        if d == check or d == check - timedelta(days=1):
            if d < check:
                check = d
            current += 1
            check -= timedelta(days=1) if d == check else timedelta(days=0)
        else:
            break

    # Longest streak
    longest = 0
    run = 1
    sorted_asc = sorted(dates)
    for i in range(1, len(sorted_asc)):
        prev = datetime.strptime(sorted_asc[i - 1], "%Y-%m-%d").date()
        curr = datetime.strptime(sorted_asc[i], "%Y-%m-%d").date()
        if (curr - prev).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    longest = max(longest, run, current)

    return {"current": current, "longest": longest}


def get_accuracy(student_id: str, subject_id: str) -> float:
    """Average score percentage across all marked attempts for a subject."""
    supabase = get_supabase()

    # Get all marked attempts for sessions in this subject
    attempts_result = (
        supabase.table("attempt")
        .select("ai_score, question_id")
        .not_.is_("marked_at", "null")
        .not_.is_("ai_score", "null")
        .execute()
    )
    attempts = attempts_result.data or []
    if not attempts:
        return 0.0

    # Filter to the subject via question→paper→subject join
    # Fetch question→subject mapping for relevant questions
    question_ids = [a["question_id"] for a in attempts]
    if not question_ids:
        return 0.0

    questions_result = (
        supabase.table("question")
        .select("id, marks, subject_id")
        .in_("id", question_ids)
        .eq("subject_id", subject_id)
        .execute()
    )
    questions = {q["id"]: q for q in (questions_result.data or [])}

    total_score = 0
    total_marks = 0
    for a in attempts:
        q = questions.get(a["question_id"])
        if q and q["marks"] > 0:
            total_score += a["ai_score"] or 0
            total_marks += q["marks"]

    return round((total_score / total_marks) * 100, 1) if total_marks > 0 else 0.0


def get_coverage_ratio(student_id: str, subject_id: str) -> float:
    """Fraction of syllabus topics attempted at least once."""
    supabase = get_supabase()
    result = (
        supabase.table("syllabus_coverage")
        .select("attempted")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return 0.0
    attempted = sum(1 for r in rows if r.get("attempted"))
    return round(attempted / len(rows), 4)


def get_readiness_index(student_id: str, subject_id: str) -> dict[str, float]:
    """
    Compute Readiness Index and its three components.
    RI = accuracy×0.40 + coverage×0.35 + consistency×0.25
    Returns scores as percentages (0–100).
    """
    accuracy = get_accuracy(student_id, subject_id)  # 0–100
    coverage = get_coverage_ratio(student_id, subject_id) * 100  # 0–100
    streak_data = get_streak(student_id)
    streak_days = streak_data["current"]

    streak_bonus = min(streak_days / 7 * 70, 70)

    # Recency bonus: 30 pts if student attempted in last 3 days
    supabase = get_supabase()
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    recent = (
        supabase.table("session")
        .select("id")
        .eq("student_id", student_id)
        .gte("completed_at", three_days_ago)
        .limit(1)
        .execute()
    )
    recency_bonus = 30.0 if recent.data else 0.0
    consistency = streak_bonus + recency_bonus  # 0–100

    ri = accuracy * 0.40 + coverage * 0.35 + consistency * 0.25

    return {
        "readiness_index": round(ri, 1),
        "accuracy": round(accuracy, 1),
        "coverage": round(coverage, 1),
        "consistency": round(consistency, 1),
    }


def get_syllabus_coverage(student_id: str, subject_id: str) -> dict[str, Any]:
    """Return covered and uncovered topic lists with attempt counts."""
    supabase = get_supabase()
    result = (
        supabase.table("syllabus_coverage")
        .select("topic_name, attempted, last_attempted")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    rows = result.data or []

    # Attempt counts from weak_topic table
    wt_result = (
        supabase.table("weak_topic")
        .select("topic_name, attempt_count, fail_count")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
    )
    wt_map = {w["topic_name"]: w for w in (wt_result.data or [])}

    covered = []
    uncovered = []
    for r in rows:
        topic = r["topic_name"]
        wt = wt_map.get(topic, {})
        entry = {
            "topic": topic,
            "attempt_count": wt.get("attempt_count", 0),
            "last_attempted": r.get("last_attempted"),
        }
        if r.get("attempted"):
            covered.append(entry)
        else:
            uncovered.append(entry)

    return {
        "covered": covered,
        "uncovered": uncovered,
        "covered_count": len(covered),
        "total_count": len(rows),
    }


def get_weak_topics(student_id: str, subject_id: str) -> list[dict[str, Any]]:
    """Return topics sorted by fail ratio (descending), with at least 1 attempt."""
    supabase = get_supabase()
    result = (
        supabase.table("weak_topic")
        .select("topic_name, attempt_count, fail_count")
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .gt("attempt_count", 0)
        .execute()
    )
    rows = result.data or []
    topics = [
        {
            "topic": r["topic_name"],
            "attempt_count": r["attempt_count"],
            "fail_ratio": round(r["fail_count"] / r["attempt_count"], 3) if r["attempt_count"] else 0,
        }
        for r in rows
    ]
    return sorted(topics, key=lambda t: t["fail_ratio"], reverse=True)


def get_recent_sessions(student_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return recent completed sessions with scores."""
    supabase = get_supabase()
    sessions_result = (
        supabase.table("session")
        .select("id, paper_id, mode, completed_at, status, paper!inner(year, paper_number, subject!inner(name))")
        .eq("student_id", student_id)
        .in_("status", ["submitted", "completed", "marked"])
        .order("completed_at", desc=True)
        .limit(limit)
        .execute()
    )
    sessions = sessions_result.data or []

    output = []
    for s in sessions:
        # Get score for this session
        attempts_result = (
            supabase.table("attempt")
            .select("ai_score, question_id")
            .eq("session_id", s["id"])
            .not_.is_("marked_at", "null")
            .execute()
        )
        attempts = attempts_result.data or []

        # Get total marks possible
        q_ids = [a["question_id"] for a in attempts]
        total_marks = 0
        if q_ids:
            qs = supabase.table("question").select("marks").in_("id", q_ids).execute()
            total_marks = sum(q["marks"] for q in (qs.data or []))

        total_score = sum(a["ai_score"] or 0 for a in attempts)
        paper = s.get("paper", {})
        subject = paper.get("subject", {}) if paper else {}

        output.append({
            "session_id": s["id"],
            "mode": s["mode"],
            "completed_at": s.get("completed_at"),
            "paper_year": paper.get("year"),
            "paper_number": paper.get("paper_number"),
            "subject_name": subject.get("name"),
            "score": total_score,
            "total_marks": total_marks,
            "percentage": round(total_score / total_marks * 100, 1) if total_marks else None,
        })
    return output


def get_student_subjects(student_id: str) -> list[dict[str, Any]]:
    """Return distinct subjects the student has attempted sessions for."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("paper!inner(subject!inner(id, name, level))")
        .eq("student_id", student_id)
        .execute()
    )
    rows = result.data or []
    seen: dict[str, dict] = {}
    for r in rows:
        paper = r.get("paper", {})
        subject = paper.get("subject", {}) if paper else {}
        if subject and subject.get("id") and subject["id"] not in seen:
            seen[subject["id"]] = subject
    return list(seen.values())


def get_dashboard_data(student_id: str, subject_id: Optional[str] = None) -> dict[str, Any]:
    """Aggregate all dashboard data for a student, optionally filtered by subject."""
    supabase = get_supabase()

    # If no subject_id provided, use the first subject with sessions
    if not subject_id:
        subjects = get_student_subjects(student_id)
        if subjects:
            subject_id = subjects[0]["id"]

    if not subject_id:
        return {
            "has_data": False,
            "subjects": [],
            "readiness": None,
            "streak": get_streak(student_id),
            "coverage": None,
            "weak_topics": [],
            "recent_sessions": [],
        }

    readiness = get_readiness_index(student_id, subject_id)
    coverage = get_syllabus_coverage(student_id, subject_id)
    weak_topics = get_weak_topics(student_id, subject_id)
    recent_sessions = get_recent_sessions(student_id)
    streak = get_streak(student_id)
    subjects = get_student_subjects(student_id)

    return {
        "has_data": True,
        "subject_id": subject_id,
        "subjects": subjects,
        "readiness": readiness,
        "streak": streak,
        "coverage": coverage,
        "weak_topics": weak_topics,
        "recent_sessions": recent_sessions,
    }
