"""
Parent Service — family dashboard aggregation, weekly report generation,
and human-readable parent advice.

Uses only existing data pipelines (attempts, sessions, weak_topics, syllabus_coverage).
No new complex pipelines.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from db.client import get_supabase
from services import dashboard as svc

logger = logging.getLogger(__name__)

# ── Status classification ─────────────────────────────────────────────────────

def _classify_status(
    avg_score_last7: float | None,
    avg_score_prev7: float | None,
    days_since_last_session: int | None,
    streak: int,
) -> str:
    """Return 'Improving' | 'Stable' | 'At Risk'."""
    if days_since_last_session is None or days_since_last_session >= 3:
        return "At Risk"
    if avg_score_last7 is not None and avg_score_last7 < 40:
        return "At Risk"
    if (
        avg_score_last7 is not None
        and avg_score_prev7 is not None
        and avg_score_last7 > avg_score_prev7 + 5
    ):
        return "Improving"
    if streak >= 5:
        return "Improving"
    return "Stable"


# ── Session-window helpers ────────────────────────────────────────────────────

def _get_sessions_in_window(
    student_id: str, from_dt: datetime, to_dt: datetime
) -> list[dict[str, Any]]:
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("id, completed_at, status")
        .eq("student_id", student_id)
        .in_("status", ["submitted", "completed", "marked"])
        .gte("completed_at", from_dt.isoformat())
        .lte("completed_at", to_dt.isoformat())
        .execute()
    )
    return result.data or []


def _avg_score_for_sessions(session_ids: list[str]) -> float | None:
    """Return average score percentage across the given sessions."""
    if not session_ids:
        return None
    supabase = get_supabase()
    attempts = (
        supabase.table("attempt")
        .select("ai_score, question_id")
        .in_("session_id", session_ids)
        .not_.is_("marked_at", "null")
        .execute()
    ).data or []

    if not attempts:
        return None

    q_ids = [a["question_id"] for a in attempts]
    qs = (
        supabase.table("question")
        .select("id, marks")
        .in_("id", q_ids)
        .execute()
    ).data or []
    marks_map = {q["id"]: q["marks"] for q in qs}

    total_score = 0.0
    total_marks = 0
    for a in attempts:
        m = marks_map.get(a["question_id"], 0)
        if m > 0:
            total_score += a["ai_score"] or 0
            total_marks += m

    return round(total_score / total_marks * 100, 1) if total_marks > 0 else None


def _count_attempts_in_window(student_id: str, from_dt: datetime, to_dt: datetime) -> int:
    """Count distinct attempts in a time window for a student."""
    sessions = _get_sessions_in_window(student_id, from_dt, to_dt)
    if not sessions:
        return 0
    session_ids = [s["id"] for s in sessions]
    supabase = get_supabase()
    result = (
        supabase.table("attempt")
        .select("id", count="exact")
        .in_("session_id", session_ids)
        .execute()
    )
    return result.count or 0


def _study_hours_in_window(sessions: list[dict[str, Any]]) -> float:
    """Estimate study hours: each session ≈ 30 min."""
    return round(len(sessions) * 0.5, 1)


def _days_since_last_session(student_id: str) -> int | None:
    """Days since the student last completed a session."""
    supabase = get_supabase()
    result = (
        supabase.table("session")
        .select("completed_at")
        .eq("student_id", student_id)
        .in_("status", ["submitted", "completed", "marked"])
        .not_.is_("completed_at", "null")
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows or not rows[0].get("completed_at"):
        return None
    last = datetime.fromisoformat(rows[0]["completed_at"].replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - last
    return delta.days


# ── Per-child summary ─────────────────────────────────────────────────────────

def _build_child_summary(child: dict[str, Any]) -> dict[str, Any]:
    """Build a rich summary for a single child."""
    student_id = child["id"]
    now = datetime.now(timezone.utc)
    last7_start = now - timedelta(days=7)
    prev7_start = now - timedelta(days=14)
    prev7_end = now - timedelta(days=7)

    dashboard = svc.get_dashboard_data(student_id)
    streak_data = dashboard.get("streak", {"current": 0, "longest": 0})
    weak_topics = dashboard.get("weak_topics", [])
    subjects = dashboard.get("subjects", [])

    sessions_last7 = _get_sessions_in_window(student_id, last7_start, now)
    sessions_prev7 = _get_sessions_in_window(student_id, prev7_start, prev7_end)

    avg_last7 = _avg_score_for_sessions([s["id"] for s in sessions_last7])
    avg_prev7 = _avg_score_for_sessions([s["id"] for s in sessions_prev7])
    days_inactive = _days_since_last_session(student_id)
    study_hours_this_week = _study_hours_in_window(sessions_last7)
    questions_this_week = _count_attempts_in_window(student_id, last7_start, now)

    ri = dashboard.get("readiness") or {}
    avg_score = avg_last7 or ri.get("accuracy", 0)

    status = _classify_status(avg_last7, avg_prev7, days_inactive, streak_data["current"])

    # Strong = low fail_ratio topics with attempts; Weak = high fail_ratio
    strong_subjects = [t["topic"] for t in weak_topics if t["fail_ratio"] < 0.3][:3]
    weak_subjects = [t["topic"] for t in weak_topics if t["fail_ratio"] >= 0.5][:3]

    return {
        "student_id": student_id,
        "name": child.get("name", ""),
        "level": child.get("level", ""),
        "avg_score": avg_score,
        "study_hours_this_week": study_hours_this_week,
        "questions_this_week": questions_this_week,
        "streak": streak_data["current"],
        "status": status,
        "strong_subjects": strong_subjects,
        "weak_subjects": weak_subjects,
        "subjects": [s.get("name", "") for s in subjects],
        "days_inactive": days_inactive,
        "avg_last7": avg_last7,
        "avg_prev7": avg_prev7,
        "readiness_index": ri.get("readiness_index", 0),
        "coverage": ri.get("coverage", 0),
        "consistency": ri.get("consistency", 0),
    }


# ── Main service functions ────────────────────────────────────────────────────

def get_parent_dashboard(parent_id: str) -> dict[str, Any]:
    """Aggregate family dashboard: summary + per-child cards."""
    supabase = get_supabase()
    result = (
        supabase.table("student")
        .select("id, name, email, level, created_at")
        .eq("parent_id", parent_id)
        .execute()
    )
    children = result.data or []

    child_summaries = []
    for child in children:
        try:
            summary = _build_child_summary(child)
            child_summaries.append(summary)
        except Exception as exc:
            logger.warning("Could not build summary for %s: %s", child.get("id"), exc)
            child_summaries.append({
                "student_id": child["id"],
                "name": child.get("name", ""),
                "level": child.get("level", ""),
                "avg_score": 0,
                "study_hours_this_week": 0,
                "questions_this_week": 0,
                "streak": 0,
                "status": "At Risk",
                "strong_subjects": [],
                "weak_subjects": [],
                "subjects": [],
                "days_inactive": None,
                "avg_last7": None,
                "avg_prev7": None,
                "readiness_index": 0,
                "coverage": 0,
                "consistency": 0,
            })

    # Family-level aggregates
    total_study_hours = sum(c["study_hours_this_week"] for c in child_summaries)
    total_questions = sum(c["questions_this_week"] for c in child_summaries)
    scores = [c["avg_score"] for c in child_summaries if c["avg_score"] > 0]
    avg_family_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    needs_attention = sum(1 for c in child_summaries if c["status"] == "At Risk")

    top_child = None
    if child_summaries:
        top_child = max(child_summaries, key=lambda c: c["readiness_index"])["name"]

    return {
        "total_children": len(children),
        "family_summary": {
            "total_study_hours": total_study_hours,
            "total_questions_attempted": total_questions,
            "avg_family_score": avg_family_score,
            "children_needing_attention": needs_attention,
            "top_performing_child": top_child,
        },
        "children": child_summaries,
    }


def generate_parent_advice(child_metrics: dict[str, Any]) -> str:
    """
    Generate short, human-readable advice for a parent about one child.
    Written as a teacher speaking — no technical language.
    """
    name = child_metrics.get("name", "Your child")
    status = child_metrics.get("status", "Stable")
    streak = child_metrics.get("streak", 0)
    avg = child_metrics.get("avg_score", 0)
    days_inactive = child_metrics.get("days_inactive")
    weak = child_metrics.get("weak_subjects", [])
    strong = child_metrics.get("strong_subjects", [])

    parts: list[str] = []

    if days_inactive is not None and days_inactive >= 3:
        parts.append(
            f"{name} hasn't studied in {days_inactive} day{'s' if days_inactive != 1 else ''}. "
            "A gentle reminder to open the app — even 15 minutes a day makes a difference."
        )
    elif status == "Improving":
        if streak >= 5:
            parts.append(
                f"{name} is on a {streak}-day streak — that's excellent consistency! "
                "Keep encouraging this habit."
            )
        else:
            parts.append(
                f"{name} is improving. Acknowledge their progress — it builds confidence."
            )
    elif status == "At Risk":
        if avg < 40:
            weak_str = f", especially {weak[0]}" if weak else ""
            parts.append(
                f"{name} is finding things difficult right now{weak_str}. "
                "Try reviewing together and make sure they have a quiet place to study."
            )
        else:
            parts.append(
                f"{name} needs more consistency. Encourage a short daily study session "
                "at the same time each day."
            )
    else:
        parts.append(
            f"{name} is doing steadily. Encourage them to push a bit harder on "
            f"{weak[0] if weak else 'the topics they find tricky'}."
        )

    if strong:
        parts.append(
            f"They are doing well in {', '.join(strong[:2])} — praise that."
        )

    return " ".join(parts)


def generate_weekly_family_report(parent_id: str) -> dict[str, Any]:
    """
    Build a full weekly family report with per-child sections,
    parent insights, and actionable recommendations.
    Stores the result in the parent_report table.
    """
    dashboard = get_parent_dashboard(parent_id)
    children = dashboard["children"]
    summary = dashboard["family_summary"]

    child_reports: list[dict[str, Any]] = []
    for child in children:
        advice = generate_parent_advice(child)

        # Determine trend label
        avg_l = child.get("avg_last7")
        avg_p = child.get("avg_prev7")
        if avg_l is not None and avg_p is not None:
            diff = avg_l - avg_p
            if diff > 5:
                trend = "Trending up"
            elif diff < -5:
                trend = "Trending down"
            else:
                trend = "Stable"
        else:
            trend = "Not enough data"

        # Recommendations
        recommendations_for_child: list[str] = []
        recommendations_for_parent: list[str] = []

        weak = child.get("weak_subjects", [])
        if weak:
            recommendations_for_child.append(
                f"Spend extra time on {', '.join(weak[:2])} this week."
            )
        if child.get("streak", 0) == 0:
            recommendations_for_child.append(
                "Try to study at least once today to start a new streak."
            )
        if child.get("coverage", 0) < 50:
            recommendations_for_child.append(
                "Work on uncovered syllabus topics — variety matters."
            )

        recommendations_for_parent.append(advice)
        if child.get("status") == "At Risk":
            recommendations_for_parent.append(
                f"Check in with {child['name']} today — ask how they are feeling about their studies."
            )

        child_reports.append({
            "name": child["name"],
            "status": child["status"],
            "avg_score": child["avg_score"],
            "study_hours": child["study_hours_this_week"],
            "questions_attempted": child["questions_this_week"],
            "streak": child["streak"],
            "strong_areas": child.get("strong_subjects", []),
            "weak_areas": child.get("weak_subjects", []),
            "performance_trend": trend,
            "readiness_index": child.get("readiness_index", 0),
            "recommendations_for_child": recommendations_for_child,
            "recommendations_for_parent": recommendations_for_parent,
        })

    # Parent insight section
    improving = [c["name"] for c in children if c["status"] == "Improving"]
    at_risk = [c["name"] for c in children if c["status"] == "At Risk"]

    parent_insights: list[str] = []
    if improving:
        parent_insights.append(
            f"{', '.join(improving)} {'is' if len(improving) == 1 else 'are'} making great progress this week."
        )
    if at_risk:
        parent_insights.append(
            f"{', '.join(at_risk)} {'needs' if len(at_risk) == 1 else 'need'} extra support right now."
        )
    if not improving and not at_risk:
        parent_insights.append("All children are maintaining steady progress.")

    report = {
        "week_ending": datetime.now(timezone.utc).isoformat(),
        "family_summary": summary,
        "parent_insights": parent_insights,
        "children": child_reports,
        "total_children": dashboard["total_children"],
    }

    # Persist report
    try:
        supabase = get_supabase()
        supabase.table("parent_report").insert({
            "parent_id": parent_id,
            "report_data": report,
        }).execute()
    except Exception as exc:
        logger.warning("Could not persist parent report: %s", exc)

    return report


def get_latest_report(parent_id: str) -> dict[str, Any] | None:
    """Return the most recently generated report for this parent."""
    supabase = get_supabase()
    result = (
        supabase.table("parent_report")
        .select("id, report_data, generated_at")
        .eq("parent_id", parent_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    row = rows[0]
    return {
        "report_id": row["id"],
        "generated_at": row["generated_at"],
        **row["report_data"],
    }
