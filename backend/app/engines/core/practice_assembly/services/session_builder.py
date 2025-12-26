"""Session builder service for assembling practice sessions.

Builds PracticeSession objects with proper ordering and metadata.
"""

import logging
import random
import uuid
from datetime import datetime
from typing import Literal

from app.engines.core.practice_assembly.schemas.session import PracticeSession, QuestionItem

logger = logging.getLogger(__name__)


class SessionBuilder:
    """Service for building practice sessions.
    
    Handles:
    - Question ordering (progressive, random, exam-style)
    - Session ID generation
    - Metadata calculation (duration, topic list)
    """
    
    def build_session(
        self,
        user_id: str,
        session_type: Literal["targeted", "mixed", "exam_simulation"],
        subject: str,
        topics: list[str],
        questions: list[QuestionItem],
        time_limit_minutes: int | None,
        trace_id: str = "unknown"
    ) -> PracticeSession:
        """Build a practice session.
        
        Args:
            user_id: User ID
            session_type: Type of session
            subject: Subject
            topics: All topics included
            questions: Selected questions (unordered)
            time_limit_minutes: Time limit (None = untimed)
            trace_id: Trace ID for logging
            
        Returns:
            Complete PracticeSession
        """
        logger.info(
            f"[{trace_id}] Building {session_type} session with {len(questions)} questions"
        )
        
        # Order questions based on session type
        ordered_questions = self._order_questions(questions, session_type, trace_id)
        
        # Update order_index
        for i, question in enumerate(ordered_questions):
            question.order_index = i
        
        # Calculate estimated duration
        estimated_duration = sum(q.estimated_minutes for q in ordered_questions)
        
        # Generate session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # Build session
        session = PracticeSession(
            session_id=session_id,
            session_type=session_type,
            user_id=user_id,
            subject=subject,
            topics=topics,
            questions=ordered_questions,
            total_questions=len(ordered_questions),
            time_limit_minutes=time_limit_minutes,
            estimated_duration_minutes=estimated_duration,
            created_at=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"[{trace_id}] Built session {session_id}: "
            f"{len(ordered_questions)} questions, ~{estimated_duration} min"
        )
        
        return session
    
    def _order_questions(
        self,
        questions: list[QuestionItem],
        session_type: Literal["targeted", "mixed", "exam_simulation"],
        trace_id: str
    ) -> list[QuestionItem]:
        """Order questions based on session type.
        
        Args:
            questions: Unordered questions
            session_type: Type of session
            trace_id: Trace ID for logging
            
        Returns:
            Ordered questions
        """
        if session_type == "targeted":
            # Progressive: easy → medium → hard
            return self._order_progressive(questions, trace_id)
        
        elif session_type == "mixed":
            # Random shuffle
            return self._order_random(questions, trace_id)
        
        elif session_type == "exam_simulation":
            # Exam-style: match real exam ordering (progressive, but balanced)
            return self._order_exam_style(questions, trace_id)
        
        else:
            # Default: random
            return self._order_random(questions, trace_id)
    
    def _order_progressive(
        self,
        questions: list[QuestionItem],
        trace_id: str
    ) -> list[QuestionItem]:
        """Order questions progressively (easy → medium → hard).
        
        This builds confidence by starting with easier questions.
        """
        logger.debug(f"[{trace_id}] Ordering questions progressively")
        
        # Group by difficulty
        easy = [q for q in questions if q.difficulty == "easy"]
        medium = [q for q in questions if q.difficulty == "medium"]
        hard = [q for q in questions if q.difficulty == "hard"]
        
        # Shuffle within each tier
        random.shuffle(easy)
        random.shuffle(medium)
        random.shuffle(hard)
        
        # Concatenate: easy first, then medium, then hard
        return easy + medium + hard
    
    def _order_random(
        self,
        questions: list[QuestionItem],
        trace_id: str
    ) -> list[QuestionItem]:
        """Order questions randomly."""
        logger.debug(f"[{trace_id}] Ordering questions randomly")
        
        shuffled = questions.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def _order_exam_style(
        self,
        questions: list[QuestionItem],
        trace_id: str
    ) -> list[QuestionItem]:
        """Order questions in exam style.
        
        Exam style: Start with easier questions, gradually increase difficulty,
        but with some mixing to keep it interesting.
        """
        logger.debug(f"[{trace_id}] Ordering questions in exam style")
        
        # Group by difficulty
        easy = [q for q in questions if q.difficulty == "easy"]
        medium = [q for q in questions if q.difficulty == "medium"]
        hard = [q for q in questions if q.difficulty == "hard"]
        
        # Shuffle within each tier
        random.shuffle(easy)
        random.shuffle(medium)
        random.shuffle(hard)
        
        # Interleave: mostly progressive, but with some mixing
        # Pattern: E E M E M H M H H (example for 9 questions)
        ordered = []
        
        # Start with easy questions (build confidence)
        ordered.extend(easy[:2] if len(easy) >= 2 else easy)
        
        # Mix medium and remaining easy
        remaining_easy = easy[2:]
        for i in range(max(len(remaining_easy), len(medium))):
            if i < len(remaining_easy):
                ordered.append(remaining_easy[i])
            if i < len(medium):
                ordered.append(medium[i])
        
        # End with hard questions (challenge)
        ordered.extend(hard)
        
        return ordered
