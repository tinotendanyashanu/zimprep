"""Difficulty balancer service for practice sessions.

Balances question selection according to target difficulty distribution.
"""

import logging
import random
from typing import Literal

from app.engines.core.practice_assembly.schemas.session import QuestionItem
from app.engines.core.practice_assembly.errors import InsufficientQuestionsError

logger = logging.getLogger(__name__)


class DifficultyBalancer:
    """Service for balancing question difficulty distribution.
    
    Ensures practice sessions have the right mix of easy, medium, and hard questions.
    Default: 40% easy, 40% medium, 20% hard
    """
    
    def balance_questions(
        self,
        available_questions: list[QuestionItem],
        target_distribution: dict[str, float],
        max_questions: int,
        trace_id: str = "unknown"
    ) -> list[QuestionItem]:
        """Balance questions according to difficulty distribution.
        
        Args:
            available_questions: Pool of questions to select from
            target_distribution: Target distribution (e.g., {"easy": 0.4, "medium": 0.4, "hard": 0.2})
            max_questions: Maximum number of questions to select
            trace_id: Trace ID for logging
            
        Returns:
            Balanced list of questions
            
        Raises:
            InsufficientQuestionsError: If not enough questions available
        """
        logger.info(
            f"[{trace_id}] Balancing {len(available_questions)} questions "
            f"to {max_questions} with distribution {target_distribution}"
        )
        
        # Group questions by difficulty
        by_difficulty: dict[str, list[QuestionItem]] = {
            "easy": [],
            "medium": [],
            "hard": []
        }
        
        for question in available_questions:
            if question.difficulty in by_difficulty:
                by_difficulty[question.difficulty].append(question)
        
        # Calculate target counts
        target_counts = {
            difficulty: int(max_questions * proportion)
            for difficulty, proportion in target_distribution.items()
        }
        
        # Adjust for rounding (ensure total equals max_questions)
        total_allocated = sum(target_counts.values())
        if total_allocated < max_questions:
            # Add remaining to medium difficulty
            target_counts["medium"] += (max_questions - total_allocated)
        
        logger.info(f"[{trace_id}] Target counts: {target_counts}")
        
        # Select questions for each difficulty
        selected_questions: list[QuestionItem] = []
        
        for difficulty in ["easy", "medium", "hard"]:
            target_count = target_counts[difficulty]
            available = by_difficulty[difficulty]
            
            if len(available) < target_count:
                logger.warning(
                    f"[{trace_id}] Insufficient {difficulty} questions: "
                    f"need {target_count}, have {len(available)}"
                )
                # Take all available
                selected = available
            else:
                # Randomly select target_count questions
                selected = random.sample(available, target_count)
            
            selected_questions.extend(selected)
        
        # Check if we have enough total questions
        if len(selected_questions) < max_questions * 0.7:  # At least 70%
            raise InsufficientQuestionsError(
                requested=max_questions,
                available=len(selected_questions),
                topics=list(set(q.topic_name for q in available_questions))
            )
        
        logger.info(
            f"[{trace_id}] Selected {len(selected_questions)} questions "
            f"(easy: {sum(1 for q in selected_questions if q.difficulty == 'easy')}, "
            f"medium: {sum(1 for q in selected_questions if q.difficulty == 'medium')}, "
            f"hard: {sum(1 for q in selected_questions if q.difficulty == 'hard')})"
        )
        
        return selected_questions
    
    def get_difficulty_breakdown(
        self,
        questions: list[QuestionItem]
    ) -> dict[str, int]:
        """Get count of questions per difficulty level.
        
        Args:
            questions: List of questions
            
        Returns:
            Dict with counts per difficulty
        """
        breakdown = {"easy": 0, "medium": 0, "hard": 0}
        
        for question in questions:
            if question.difficulty in breakdown:
                breakdown[question.difficulty] += 1
        
        return breakdown
