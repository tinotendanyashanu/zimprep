"""
Adaptive question selection — intelligent practice engine.

Keeps students in the "zone of proximal development" (~60-75% success rate)
using four question phases:

  CHALLENGE  (50%) — Weak topics with spaced repetition scheduling.
  DISCOVERY  (20%) — Untouched topics to grow syllabus coverage.
  REVIEW     (15%) — Passed topics due for reinforcement.
  CONFIDENCE (15%) — Strong topics for momentum / streak protection.

Within each phase the algorithm applies:
  - Spaced repetition intervals (exponential back-off on consecutive correct)
  - Difficulty matching via question marks vs. student ability band
  - Topic rotation — avoids repeating the same topic back-to-back
  - Recency penalty — deprioritises questions attempted in the last N
  - Session momentum — starts easier, ramps up after a few correct answers
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from db.client import get_supabase
from services.content_formatting import normalize_render_payload

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Phase selection weights
PHASE_CHALLENGE = 0.50
PHASE_DISCOVERY = 0.20
PHASE_REVIEW = 0.15
PHASE_CONFIDENCE = 0.15

# Spaced repetition — interval multiplier per consecutive-correct count
# After N consecutive correct answers on a topic, wait N * BASE_INTERVAL_HOURS
SR_BASE_INTERVAL_HOURS = 4
SR_MAX_INTERVAL_HOURS = 168  # 7 days cap

# Recency
RECENT_WINDOW = 30  # last N attempts to penalise
RECENT_PENALTY = 0.1  # weight multiplier for recently-seen questions
TOPIC_COOLDOWN = 3  # don't repeat same topic within last N questions

# Difficulty
EASY_MARKS_CEIL = 2
HARD_MARKS_FLOOR = 5

# Session momentum — first N questions are biased easier
WARMUP_QUESTIONS = 3


# ── Topic analysis ────────────────────────────────────────────────────────────

def _build_topic_stats(
    questions: list[dict],
    student_id: str,
) -> dict[str, dict[str, Any]]:
    """
    Build per-topic stats from the student's attempt history.

    Returns: {topic_name: {
        fail_ratio, avg_score_pct, attempt_count, consecutive_correct,
        last_attempted_at, is_due_for_review
    }}
    """
    supabase = get_supabase()

    all_topics: set[str] = set()
    q_topics: dict[str, list[str]] = {}
    q_marks: dict[str, int] = {}
    for q in questions:
        tags = q.get("topic_tags") or []
        q_topics[q["id"]] = tags
        q_marks[q["id"]] = q.get("marks") or 1
        all_topics.update(tags)

    if not all_topics:
        return {}

    all_q_ids = [q["id"] for q in questions]
    attempts_data = (
        supabase.table("attempt")
        .select("question_id, ai_score, marked_at, session!inner(student_id)")
        .eq("session.student_id", student_id)
        .in_("question_id", all_q_ids)
        .not_.is_("ai_score", "null")
        .order("marked_at", desc=False)
        .execute()
    )

    # Per-topic accumulation
    topic_scores: dict[str, list[float]] = {t: [] for t in all_topics}
    topic_last_at: dict[str, datetime | None] = {t: None for t in all_topics}
    # Track consecutive correct per topic (reset on fail)
    topic_consec: dict[str, int] = {t: 0 for t in all_topics}

    for attempt in (attempts_data.data or []):
        qid = attempt["question_id"]
        score = attempt.get("ai_score") or 0
        marks = q_marks.get(qid, 1) or 1
        ratio = score / marks
        marked_at = attempt.get("marked_at")

        for t in q_topics.get(qid, []):
            topic_scores[t].append(ratio)
            if marked_at:
                try:
                    dt = datetime.fromisoformat(marked_at.replace("Z", "+00:00"))
                    topic_last_at[t] = dt
                except (ValueError, TypeError):
                    pass

            # Consecutive correct: >= 70% of marks = "correct"
            if ratio >= 0.7:
                topic_consec[t] = topic_consec.get(t, 0) + 1
            else:
                topic_consec[t] = 0

    now = datetime.now(timezone.utc)
    stats: dict[str, dict[str, Any]] = {}

    for t in all_topics:
        scores = topic_scores[t]
        attempt_count = len(scores)
        if attempt_count == 0:
            stats[t] = {
                "fail_ratio": None,
                "avg_score_pct": None,
                "attempt_count": 0,
                "consecutive_correct": 0,
                "last_attempted_at": None,
                "is_due_for_review": True,  # never attempted = always due
                "hours_since_last": None,
            }
            continue

        avg_score = sum(scores) / len(scores)
        fail_ratio = 1.0 - avg_score
        consec = topic_consec[t]
        last_at = topic_last_at[t]

        # Spaced repetition: interval grows with consecutive correct answers
        sr_interval_h = min(
            SR_BASE_INTERVAL_HOURS * (2 ** max(consec - 1, 0)),
            SR_MAX_INTERVAL_HOURS,
        )
        hours_since = (
            (now - last_at).total_seconds() / 3600 if last_at else float("inf")
        )
        is_due = hours_since >= sr_interval_h

        stats[t] = {
            "fail_ratio": round(fail_ratio, 4),
            "avg_score_pct": round(avg_score * 100, 1),
            "attempt_count": attempt_count,
            "consecutive_correct": consec,
            "last_attempted_at": last_at,
            "is_due_for_review": is_due,
            "hours_since_last": round(hours_since, 1),
        }

    return stats


def _classify_topics(
    topic_stats: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    """
    Classify topics into buckets for phase selection.

    Returns: {
        "untouched": [...],   # never attempted
        "weak": [...],        # fail_ratio > 0.4
        "moderate": [...],    # 0.15 < fail_ratio <= 0.4
        "strong": [...],      # fail_ratio <= 0.15
        "due_for_review": [...],  # passed but interval elapsed
    }
    """
    untouched, weak, moderate, strong, due = [], [], [], [], []

    for topic, s in topic_stats.items():
        if s["attempt_count"] == 0:
            untouched.append(topic)
            continue

        fr = s["fail_ratio"]
        if fr > 0.4:
            weak.append(topic)
        elif fr > 0.15:
            moderate.append(topic)
        else:
            strong.append(topic)

        if s["is_due_for_review"] and fr <= 0.4:
            due.append(topic)

    return {
        "untouched": untouched,
        "weak": weak,
        "moderate": moderate,
        "strong": strong,
        "due_for_review": due,
    }


# ── Phase selection ───────────────────────────────────────────────────────────

def _select_phase(
    buckets: dict[str, list[str]],
    session_question_count: int,
    current_streak: int,
) -> str:
    """
    Choose which phase to use for the next question.
    Adapts weights based on available topics and session state.
    """
    weights = {
        "challenge": PHASE_CHALLENGE,
        "discovery": PHASE_DISCOVERY,
        "review": PHASE_REVIEW,
        "confidence": PHASE_CONFIDENCE,
    }

    # If no untouched topics, redistribute discovery weight to challenge
    if not buckets["untouched"]:
        weights["challenge"] += weights["discovery"]
        weights["discovery"] = 0

    # If no due-for-review topics, redistribute to challenge
    if not buckets["due_for_review"]:
        weights["challenge"] += weights["review"]
        weights["review"] = 0

    # If no strong topics, redistribute confidence to challenge
    if not buckets["strong"]:
        weights["challenge"] += weights["confidence"]
        weights["confidence"] = 0

    # If no weak/moderate topics, redistribute challenge to discovery + review
    if not buckets["weak"] and not buckets["moderate"]:
        extra = weights["challenge"]
        weights["challenge"] = 0
        if buckets["untouched"]:
            weights["discovery"] += extra * 0.6
            weights["review"] += extra * 0.4
        else:
            weights["review"] += extra

    # Session warmup: boost confidence in first few questions
    if session_question_count < WARMUP_QUESTIONS and buckets["strong"]:
        weights["confidence"] += 0.20
        weights["challenge"] = max(weights["challenge"] - 0.20, 0.05)

    # Streak protection: if streak >= 5, slightly boost confidence
    if current_streak >= 5 and buckets["strong"]:
        weights["confidence"] += 0.10
        weights["challenge"] = max(weights["challenge"] - 0.10, 0.05)

    # Normalize
    total = sum(weights.values())
    if total == 0:
        return "challenge"

    r = random.uniform(0, total)
    cumulative = 0.0
    for phase, w in weights.items():
        cumulative += w
        if r <= cumulative:
            return phase
    return "challenge"


# ── Question scoring ──────────────────────────────────────────────────────────

def _score_question(
    q: dict[str, Any],
    target_topics: list[str],
    topic_stats: dict[str, dict[str, Any]],
    recent_qids: set[str],
    recent_topics: list[str],
    student_ability_pct: float | None,
    phase: str,
) -> float:
    """
    Score a question for selection within a phase.
    Higher score = more likely to be picked.
    """
    tags = q.get("topic_tags") or []
    marks = q.get("marks") or 1

    # Base: does this question belong to one of the target topics?
    topic_match = any(t in target_topics for t in tags)
    if not topic_match:
        return 0.0

    score = 1.0

    # Topic strength weighting
    for t in tags:
        s = topic_stats.get(t, {})
        fr = s.get("fail_ratio")
        if phase == "challenge" and fr is not None:
            # Prefer topics with higher fail ratio
            score *= 1.0 + fr * 2.0
        elif phase == "discovery":
            # All untouched topics are equal
            score *= 1.0
        elif phase == "review" and s.get("is_due_for_review"):
            # Prefer topics that have been waiting longer
            hours = s.get("hours_since_last") or 0
            score *= 1.0 + min(hours / 24, 3.0)  # up to 3x for 3+ days overdue
        elif phase == "confidence" and fr is not None:
            # Prefer topics with lower fail ratio (student is strong)
            score *= 1.0 + (1.0 - fr) * 1.5

    # Difficulty matching — use marks as proxy
    if student_ability_pct is not None:
        if student_ability_pct >= 70:
            # Strong student: slight preference for harder questions
            if marks >= HARD_MARKS_FLOOR:
                score *= 1.3
        elif student_ability_pct < 40:
            # Struggling student: prefer easier questions
            if marks <= EASY_MARKS_CEIL:
                score *= 1.5
            elif marks >= HARD_MARKS_FLOOR:
                score *= 0.5

    # Recency penalty — don't repeat recently seen questions
    if q["id"] in recent_qids:
        score *= RECENT_PENALTY

    # Topic cooldown — avoid same topic as last N questions
    if recent_topics:
        last_topics = set(recent_topics[-TOPIC_COOLDOWN:])
        if any(t in last_topics for t in tags):
            score *= 0.3

    # Slight randomness to prevent deterministic loops
    score *= random.uniform(0.8, 1.2)

    return max(score, 0.001)


# ── Main entry point ──────────────────────────────────────────────────────────

def pick_next_question(
    subject_id: str,
    student_id: str,
    topic: str | None = None,
    paper_number: int | None = None,
) -> dict[str, Any] | None:
    """
    Return the next question for a student using the adaptive algorithm.

    The algorithm balances learning effectiveness with engagement:
    1. Analyses per-topic performance (fail ratios, spaced repetition intervals).
    2. Selects a question *phase* (challenge/discovery/review/confidence).
    3. Scores candidate questions within that phase.
    4. Picks via weighted random from top candidates.

    If a specific `topic` is given, only questions with that topic tag
    are considered (useful when student explicitly selects a topic filter).
    """
    supabase = get_supabase()

    # ── 1. Verify subject matches student's board + level ─────────────
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

    # ── 2. Fetch all candidate questions ──────────────────────────────
    papers_query = (
        supabase.table("paper")
        .select("id")
        .eq("subject_id", subject_id)
    )
    if paper_number is not None:
        papers_query = papers_query.eq("paper_number", paper_number)
    papers = papers_query.execute()
    paper_ids = [p["id"] for p in papers.data]
    if not paper_ids:
        return None

    query = (
        supabase.table("question")
        .select("*")
        .in_("paper_id", paper_ids)
        .neq("diagram_status", "failed")
        .eq("hidden", False)
    )
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

    # ── 3. Build topic stats & classify ───────────────────────────────
    topic_stats = _build_topic_stats(questions, student_id)
    buckets = _classify_topics(topic_stats)

    # If user filtered to a specific topic, constrain buckets
    if topic:
        for key in buckets:
            buckets[key] = [t for t in buckets[key] if t == topic]

    # ── 4. Fetch recent attempts for recency / cooldown ───────────────
    recent_result = (
        supabase.table("attempt")
        .select("question_id, session!inner(student_id)")
        .eq("session.student_id", student_id)
        .order("created_at", desc=True)
        .limit(RECENT_WINDOW)
        .execute()
    )
    recent_qids = {a["question_id"] for a in (recent_result.data or [])}

    # Build recent topic sequence for cooldown
    recent_q_ids_ordered = [a["question_id"] for a in (recent_result.data or [])]
    q_topic_map = {q["id"]: (q.get("topic_tags") or []) for q in questions}
    recent_topics: list[str] = []
    for qid in reversed(recent_q_ids_ordered):  # oldest first
        tags = q_topic_map.get(qid, [])
        if tags:
            recent_topics.append(tags[0])  # primary topic

    # ── 5. Compute student ability for difficulty matching ────────────
    student_ability_pct: float | None = None
    scored_topics = [s for s in topic_stats.values() if s["avg_score_pct"] is not None]
    if scored_topics:
        student_ability_pct = sum(s["avg_score_pct"] for s in scored_topics) / len(scored_topics)

    # Count how many questions this student has done in current session-like window
    session_question_count = len(recent_qids)

    # Current streak estimate (consecutive recent correct)
    current_streak = 0
    for qid in recent_q_ids_ordered:
        # We don't have scores here, so estimate from topic stats
        # Use session_question_count as proxy — not perfect but good enough
        break
    # Better: count from recent attempts with scores
    streak_result = (
        supabase.table("attempt")
        .select("ai_score, question_id, session!inner(student_id)")
        .eq("session.student_id", student_id)
        .not_.is_("ai_score", "null")
        .order("marked_at", desc=True)
        .limit(10)
        .execute()
    )
    for a in (streak_result.data or []):
        qid = a["question_id"]
        marks = next((q.get("marks", 1) for q in questions if q["id"] == qid), 1) or 1
        if (a.get("ai_score") or 0) / marks >= 0.7:
            current_streak += 1
        else:
            break

    # ── 6. Select phase ───────────────────────────────────────────────
    phase = _select_phase(buckets, session_question_count, current_streak)

    # Map phase to target topics
    target_topics: list[str]
    if phase == "challenge":
        target_topics = buckets["weak"] + buckets["moderate"]
    elif phase == "discovery":
        target_topics = buckets["untouched"]
    elif phase == "review":
        target_topics = buckets["due_for_review"]
    elif phase == "confidence":
        target_topics = buckets["strong"]
    else:
        target_topics = buckets["weak"] + buckets["moderate"] + buckets["strong"]

    # Fallback: if target is empty, open up to all topics
    if not target_topics:
        target_topics = list(topic_stats.keys())
    if not target_topics:
        # No topic info at all — use all questions equally
        return normalize_render_payload(random.choice(questions))

    # ── 7. Score & select ─────────────────────────────────────────────
    scored = []
    for q in questions:
        w = _score_question(
            q, target_topics, topic_stats, recent_qids,
            recent_topics, student_ability_pct, phase,
        )
        if w > 0:
            scored.append((q, w))

    if not scored:
        # Fallback: pick any non-recent question
        fallback = [q for q in questions if q["id"] not in recent_qids]
        if not fallback:
            fallback = questions
        return normalize_render_payload(random.choice(fallback))

    # Weighted random selection
    total_weight = sum(w for _, w in scored)
    r = random.uniform(0, total_weight)
    cumulative = 0.0
    for q, w in scored:
        cumulative += w
        if r <= cumulative:
            logger.debug(
                "Adaptive pick: phase=%s topic_targets=%d candidates=%d ability=%.0f%% streak=%d",
                phase, len(target_topics), len(scored),
                student_ability_pct or 0, current_streak,
            )
            return normalize_render_payload(q)

    return normalize_render_payload(scored[-1][0])


# ── Weak topics (used by dashboard & API) ─────────────────────────────────────

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
