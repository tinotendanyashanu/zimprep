"""
Email service — Welcome, report ready, and weekly digest emails via Resend.
Falls back to console logging when RESEND_API_KEY is not set (dev mode).
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "ZimPrep <noreply@zimprep.com>")
RESEND_URL = "https://api.resend.com/emails"
APP_URL = os.getenv("APP_URL", "http://localhost:3000").rstrip("/")


def _send(to: str, subject: str, html: str) -> None:
    """Send an email via Resend, or log it to console in dev mode."""
    if not RESEND_API_KEY:
        logger.info(
            "[DEV EMAIL] To: %s | Subject: %s\n%s",
            to,
            subject,
            html,
        )
        return

    try:
        resp = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)


def send_welcome_email(email: str, name: str, role: str = "student") -> None:
    """Send welcome email on registration."""
    if role == "parent":
        body = f"""
        <h2>Welcome to ZimPrep, {name}!</h2>
        <p>Your Parent Account is ready. You can link your child's account to track
        their exam preparation progress in real time.</p>
        <p><a href="{APP_URL}/parent/dashboard">Go to Parent Dashboard →</a></p>
        <p>— The ZimPrep Team</p>
        """
        subject = "Welcome to ZimPrep — Parent Account Ready"
    else:
        body = f"""
        <h2>Welcome to ZimPrep, {name}!</h2>
        <p>You're all set to start mastering your ZIMSEC exams. Practice with real
        past papers and get instant AI feedback on every answer.</p>
        <p><a href="{APP_URL}/dashboard">Start Practising →</a></p>
        <p>— The ZimPrep Team</p>
        """
        subject = "Welcome to ZimPrep — Let's get started!"

    _send(email, subject, body)


def send_report_ready_email(
    email: str,
    name: str,
    session_id: str,
    score: int,
    total_marks: int,
) -> None:
    """Send report-ready email after exam marking completes."""
    percentage = round(score / total_marks * 100) if total_marks else 0
    results_url = f"{APP_URL}/exam/{session_id}/results"
    body = f"""
    <h2>Your results are in, {name}!</h2>
    <table style="border-collapse:collapse;margin:16px 0;">
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Score</td>
        <td style="padding:8px 16px;">{score} / {total_marks}</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Percentage</td>
        <td style="padding:8px 16px;">{percentage}%</td>
      </tr>
    </table>
    <p><a href="{results_url}">View Full Results &amp; Feedback →</a></p>
    <p>— The ZimPrep Team</p>
    """
    _send(email, f"Your ZimPrep Results: {percentage}%", body)


def send_weekly_digest_email(email: str, name: str, stats: dict[str, Any]) -> None:
    """Send weekly digest with performance summary."""
    ri = stats.get("readiness_index", 0)
    accuracy = stats.get("accuracy", 0)
    streak = stats.get("streak", 0)
    coverage = stats.get("coverage", 0)
    questions_attempted = stats.get("questions_attempted", 0)
    weak_topics: list[str] = stats.get("weak_topics", [])

    weak_list_html = ""
    if weak_topics:
        items = "".join(f"<li>{t}</li>" for t in weak_topics[:5])
        weak_list_html = f"<p><strong>Topics to focus on:</strong></p><ul>{items}</ul>"

    body = f"""
    <h2>Your ZimPrep Weekly Digest</h2>
    <p>Hi {name}, here's how you did this week:</p>
    <table style="border-collapse:collapse;margin:16px 0;">
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Readiness Index</td>
        <td style="padding:8px 16px;">{ri}%</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Accuracy</td>
        <td style="padding:8px 16px;">{accuracy}%</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Questions Attempted</td>
        <td style="padding:8px 16px;">{questions_attempted}</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Streak</td>
        <td style="padding:8px 16px;">{streak} day(s)</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Syllabus Coverage</td>
        <td style="padding:8px 16px;">{coverage}%</td>
      </tr>
    </table>
    {weak_list_html}
    <p><a href="{APP_URL}/dashboard">Keep Practising →</a></p>
    <p>— The ZimPrep Team</p>
    """
    _send(email, "Your ZimPrep Weekly Digest", body)


def send_waitlist_notification(
    email: str,
    phone_number: str,
    source_page: str,
    already_joined: bool = False,
) -> None:
    """Notify the team when a visitor joins or updates the waitlist."""
    notify_email = os.getenv("WAITLIST_NOTIFY_EMAIL", "").strip()
    if not notify_email:
        logger.info(
            "[WAITLIST] email=%s phone=%s source=%s already_joined=%s",
            email,
            phone_number,
            source_page,
            already_joined,
        )
        return

    status = "updated an existing waitlist entry" if already_joined else "joined the waitlist"
    body = f"""
    <h2>New waitlist activity</h2>
    <p>A visitor {status}.</p>
    <table style="border-collapse:collapse;margin:16px 0;">
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Email</td>
        <td style="padding:8px 16px;">{email}</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Phone</td>
        <td style="padding:8px 16px;">{phone_number}</td>
      </tr>
      <tr>
        <td style="padding:8px 16px;background:#f3f4f6;font-weight:bold;">Source page</td>
        <td style="padding:8px 16px;">{source_page}</td>
      </tr>
    </table>
    """
    _send(notify_email, "ZimPrep waitlist signup", body)
