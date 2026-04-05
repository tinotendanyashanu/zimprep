"""
Notification Service — alert generation and email delivery for parents.

Alerts fire when:
  - A child has no activity for 3+ days (inactivity)
  - A child's average score drops by 10+ points week-over-week (performance_drop)
  - A child misses their weekly study-hours goal (goal_not_met)
  - A child's score improves by 10+ points week-over-week (improving)

Notifications are stored in parent_alert and optionally emailed.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from db.client import get_supabase
from services import email as email_svc

logger = logging.getLogger(__name__)

INACTIVITY_THRESHOLD_DAYS = 3


# ── Alert helpers ─────────────────────────────────────────────────────────────

def _create_alert(
    parent_id: str,
    student_id: str,
    alert_type: str,
    message: str,
) -> dict[str, Any]:
    supabase = get_supabase()
    result = (
        supabase.table("parent_alert")
        .insert({
            "parent_id": parent_id,
            "student_id": student_id,
            "alert_type": alert_type,
            "message": message,
        })
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else {}


def _recent_alert_exists(parent_id: str, student_id: str, alert_type: str) -> bool:
    """Avoid duplicate alerts of the same type within 24 hours."""
    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    result = (
        supabase.table("parent_alert")
        .select("id")
        .eq("parent_id", parent_id)
        .eq("student_id", student_id)
        .eq("alert_type", alert_type)
        .gte("created_at", cutoff)
        .limit(1)
        .execute()
    )
    return bool(result.data)


# ── Core check functions ──────────────────────────────────────────────────────

def check_inactivity(
    parent_id: str, child: dict[str, Any], days_inactive: int | None
) -> dict[str, Any] | None:
    """Create alert if child has been inactive for threshold days."""
    if days_inactive is None or days_inactive < INACTIVITY_THRESHOLD_DAYS:
        return None
    if _recent_alert_exists(parent_id, child["id"], "inactivity"):
        return None

    day_word = "day" if days_inactive == 1 else "days"
    message = (
        f"{child['name']} has not studied for {days_inactive} {day_word}. "
        "A gentle nudge can make all the difference."
    )
    return _create_alert(parent_id, child["id"], "inactivity", message)


def check_performance_drop(
    parent_id: str,
    child: dict[str, Any],
    avg_last7: float | None,
    avg_prev7: float | None,
) -> dict[str, Any] | None:
    """Create alert if avg score dropped by 10+ points."""
    if avg_last7 is None or avg_prev7 is None:
        return None
    if avg_last7 >= avg_prev7 - 10:
        return None
    if _recent_alert_exists(parent_id, child["id"], "performance_drop"):
        return None

    drop = round(avg_prev7 - avg_last7, 1)
    message = (
        f"{child['name']}'s average score has dropped by {drop}% this week "
        f"(from {avg_prev7}% to {avg_last7}%). It may be worth checking in."
    )
    return _create_alert(parent_id, child["id"], "performance_drop", message)


def check_improvement(
    parent_id: str,
    child: dict[str, Any],
    avg_last7: float | None,
    avg_prev7: float | None,
) -> dict[str, Any] | None:
    """Create a positive alert if score improved by 10+ points."""
    if avg_last7 is None or avg_prev7 is None:
        return None
    if avg_last7 <= avg_prev7 + 10:
        return None
    if _recent_alert_exists(parent_id, child["id"], "improving"):
        return None

    gain = round(avg_last7 - avg_prev7, 1)
    message = (
        f"{child['name']}'s performance is improving — up {gain}% this week "
        f"(now at {avg_last7}%). Let them know you noticed!"
    )
    return _create_alert(parent_id, child["id"], "improving", message)


def check_goal_not_met(
    parent_id: str,
    child: dict[str, Any],
    study_hours_this_week: float,
    goal_hours: float,
) -> dict[str, Any] | None:
    """Create alert if weekly study-hours goal was not met."""
    if study_hours_this_week >= goal_hours:
        return None
    if _recent_alert_exists(parent_id, child["id"], "goal_not_met"):
        return None

    shortfall = round(goal_hours - study_hours_this_week, 1)
    message = (
        f"{child['name']} studied {study_hours_this_week}h this week but the goal is "
        f"{goal_hours}h — {shortfall}h short. Encourage an extra session."
    )
    return _create_alert(parent_id, child["id"], "goal_not_met", message)


# ── Main entry point ─────────────────────────────────────────────────────────

def check_and_create_alerts(
    parent_id: str,
    child_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Run all alert checks for all children and return newly created alerts.
    child_summaries should come from parent_service._build_child_summary().
    """
    supabase = get_supabase()

    # Load goals for this parent
    goals_result = (
        supabase.table("parent_goals")
        .select("student_id, weekly_hours_target, target_grade_percent")
        .eq("parent_id", parent_id)
        .execute()
    )
    goals_map: dict[str, dict[str, Any]] = {
        g["student_id"]: g for g in (goals_result.data or [])
    }

    new_alerts: list[dict[str, Any]] = []

    for child in child_summaries:
        student_id = child["student_id"]
        goals = goals_map.get(student_id, {})
        goal_hours = float(goals.get("weekly_hours_target", 5))

        alert = check_inactivity(parent_id, child, child.get("days_inactive"))
        if alert:
            new_alerts.append(alert)

        alert = check_performance_drop(
            parent_id, child, child.get("avg_last7"), child.get("avg_prev7")
        )
        if alert:
            new_alerts.append(alert)

        alert = check_improvement(
            parent_id, child, child.get("avg_last7"), child.get("avg_prev7")
        )
        if alert:
            new_alerts.append(alert)

        alert = check_goal_not_met(
            parent_id, child, child.get("study_hours_this_week", 0), goal_hours
        )
        if alert:
            new_alerts.append(alert)

    return new_alerts


def get_parent_alerts(
    parent_id: str, unread_only: bool = False, limit: int = 20
) -> list[dict[str, Any]]:
    """Return alerts for a parent, newest first."""
    supabase = get_supabase()
    query = (
        supabase.table("parent_alert")
        .select("id, student_id, alert_type, message, is_read, created_at")
        .eq("parent_id", parent_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if unread_only:
        query = query.eq("is_read", False)
    return query.execute().data or []


def mark_alert_read(parent_id: str, alert_id: str) -> None:
    """Mark a specific alert as read."""
    supabase = get_supabase()
    supabase.table("parent_alert").update({"is_read": True}).eq("id", alert_id).eq(
        "parent_id", parent_id
    ).execute()


def mark_all_alerts_read(parent_id: str) -> None:
    """Mark all alerts for this parent as read."""
    supabase = get_supabase()
    supabase.table("parent_alert").update({"is_read": True}).eq(
        "parent_id", parent_id
    ).execute()


# ── Email notifications ───────────────────────────────────────────────────────

def send_weekly_report_email(
    parent_email: str, parent_name: str, report: dict[str, Any]
) -> None:
    """Email the weekly family report to the parent."""
    children = report.get("children", [])
    summary = report.get("family_summary", {})

    child_rows = ""
    for c in children:
        status_color = {
            "Improving": "#16a34a",
            "Stable": "#2563eb",
            "At Risk": "#dc2626",
        }.get(c["status"], "#6b7280")

        weak = ", ".join(c.get("weak_areas", [])[:3]) or "—"
        strong = ", ".join(c.get("strong_areas", [])[:3]) or "—"
        recs = " ".join(c.get("recommendations_for_parent", []))

        child_rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;font-weight:bold;">{c['name']}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;">{c.get('avg_score', 0):.0f}%</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;">{c.get('study_hours', 0)}h</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;color:{status_color};font-weight:bold;">{c['status']}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;">{strong}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;">{weak}</td>
        </tr>
        <tr>
          <td colspan="6" style="padding:8px 16px 16px;border-bottom:2px solid #e5e7eb;background:#f9fafb;font-size:13px;color:#374151;">
            <strong>For you:</strong> {recs}
          </td>
        </tr>
        """

    insights_html = "".join(
        f"<li>{i}</li>" for i in report.get("parent_insights", [])
    )

    html = f"""
    <div style="font-family:sans-serif;max-width:640px;margin:auto;color:#111827;">
      <h2 style="color:#111827;">Your ZimPrep Weekly Family Report</h2>
      <p>Hi {parent_name}, here is how your family did this week:</p>

      <table style="border-collapse:collapse;width:100%;margin:16px 0;background:#f3f4f6;border-radius:8px;">
        <tr>
          <td style="padding:12px 16px;">
            <p style="margin:0;font-size:12px;color:#6b7280;">Total Study Time</p>
            <p style="margin:4px 0 0;font-size:22px;font-weight:bold;">{summary.get('total_study_hours', 0)}h</p>
          </td>
          <td style="padding:12px 16px;">
            <p style="margin:0;font-size:12px;color:#6b7280;">Questions Attempted</p>
            <p style="margin:4px 0 0;font-size:22px;font-weight:bold;">{summary.get('total_questions_attempted', 0)}</p>
          </td>
          <td style="padding:12px 16px;">
            <p style="margin:0;font-size:12px;color:#6b7280;">Family Average</p>
            <p style="margin:4px 0 0;font-size:22px;font-weight:bold;">{summary.get('avg_family_score', 0):.0f}%</p>
          </td>
          <td style="padding:12px 16px;">
            <p style="margin:0;font-size:12px;color:#6b7280;">Need Attention</p>
            <p style="margin:4px 0 0;font-size:22px;font-weight:bold;color:#dc2626;">{summary.get('children_needing_attention', 0)}</p>
          </td>
        </tr>
      </table>

      <h3>What You Should Know</h3>
      <ul style="padding-left:20px;line-height:1.7;">{insights_html}</ul>

      <h3>Each Child This Week</h3>
      <table style="border-collapse:collapse;width:100%;margin:16px 0;">
        <thead>
          <tr style="background:#f9fafb;font-size:12px;color:#6b7280;text-align:left;">
            <th style="padding:8px 16px;">Name</th>
            <th style="padding:8px 16px;">Avg Score</th>
            <th style="padding:8px 16px;">Study Time</th>
            <th style="padding:8px 16px;">Status</th>
            <th style="padding:8px 16px;">Strong</th>
            <th style="padding:8px 16px;">Needs Work</th>
          </tr>
        </thead>
        <tbody>{child_rows}</tbody>
      </table>

      <p style="margin-top:24px;">
        <a href="https://zimprep.com/parent/dashboard"
           style="background:#111827;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">
          View Full Dashboard →
        </a>
      </p>
      <p style="color:#6b7280;font-size:13px;">— The ZimPrep Team</p>
    </div>
    """

    email_svc._send(parent_email, "Your ZimPrep Weekly Family Report", html)


def send_alert_email(
    parent_email: str, parent_name: str, alert: dict[str, Any]
) -> None:
    """Send an immediate alert email to the parent."""
    alert_type = alert.get("alert_type", "")
    message = alert.get("message", "")

    emoji_map = {
        "inactivity": "⏰",
        "performance_drop": "⚠️",
        "improving": "🎉",
        "goal_not_met": "🎯",
    }
    emoji = emoji_map.get(alert_type, "📌")

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:auto;color:#111827;">
      <h2>{emoji} ZimPrep Alert</h2>
      <p>Hi {parent_name},</p>
      <p style="font-size:16px;line-height:1.6;background:#f3f4f6;padding:16px;border-radius:8px;">{message}</p>
      <p>
        <a href="https://zimprep.com/parent/dashboard"
           style="background:#111827;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">
          View Dashboard →
        </a>
      </p>
      <p style="color:#6b7280;font-size:13px;">— The ZimPrep Team</p>
    </div>
    """
    subject_map = {
        "inactivity": "Reminder: Study time for your child",
        "performance_drop": "Heads up: Performance change noticed",
        "improving": "Great news about your child's progress",
        "goal_not_met": "Study goal update for your child",
    }
    subject = subject_map.get(alert_type, "ZimPrep Parent Alert")
    email_svc._send(parent_email, subject, html)
