"""
Marking Service — AI-powered answer marking using Claude.
Stub for Week 1. Full implementation in Week 2.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def mark_attempt(attempt_id: str) -> None:
    """
    Mark a student's attempt using Claude.

    Steps (Week 2):
    1. Fetch attempt + question from DB
    2. Build marking prompt with question text, mark scheme, student answer
    3. Call Claude with structured output for score + feedback
    4. Update attempt row with ai_score, ai_feedback, ai_references, marked_at
    5. Update weak_topic and syllabus_coverage accordingly
    """
    # TODO Week 2
    logger.info("mark_attempt called for %s (not yet implemented)", attempt_id)
