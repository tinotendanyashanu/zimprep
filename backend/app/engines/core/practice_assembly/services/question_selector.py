"""Question selection service for practice sessions.

Selects questions from MongoDB based on topics, filters, and recency.
"""

import logging
from datetime import datetime, timedelta
from typing import Literal

from app.engines.core.practice_assembly.schemas.session import QuestionItem
from app.engines.core.practice_assembly.errors import InsufficientQuestionsError

logger = logging.getLogger(__name__)


class QuestionSelector:
    """Service for selecting questions from MongoDB.
    
    Handles:
    - Topic-based filtering
    - Recency filtering (avoid recently seen questions)
    - Question type filtering
    - Subject and syllabus filtering
    """
    
    def __init__(self, mongodb_client=None):
        """Initialize selector with MongoDB client.
        
        Args:
            mongodb_client: MongoDB client (optional, uses sample data if None)
        """
        self.mongodb_client = mongodb_client
    
    async def select_questions(
        self,
        topic_ids: list[str],
        subject: str,
        syllabus_version: str,
        user_id: str,
        exclude_recent_days: int = 7,
        preferred_question_types: list[str] | None = None,
        trace_id: str = "unknown"
    ) -> list[QuestionItem]:
        """Select questions matching criteria.
        
        Args:
            topic_ids: Topics to select from
            subject: Subject filter
            syllabus_version: Syllabus version filter
            user_id: User ID for recency filtering
            exclude_recent_days: Exclude questions attempted in last N days
            preferred_question_types: Filter by question types (None = all)
            trace_id: Trace ID for logging
            
        Returns:
            List of available questions (not yet balanced by difficulty)
        """
        logger.info(
            f"[{trace_id}] Selecting questions for topics: {topic_ids}, "
            f"subject: {subject}, exclude_recent: {exclude_recent_days} days"
        )
        
        # Get recently attempted question IDs
        recent_question_ids = await self._get_recent_questions(
            user_id, exclude_recent_days, trace_id
        )
        
        # Query MongoDB (placeholder)
        # In production, would query:
        # - questions collection
        # - filter by topic_ids, subject, syllabus_version
        # - exclude recent_question_ids
        # - filter by preferred_question_types if specified
        
        # For now, return sample questions
        questions = self._get_sample_questions(
            topic_ids, subject, recent_question_ids, preferred_question_types
        )
        
        logger.info(f"[{trace_id}] Found {len(questions)} questions")
        
        return questions
    
    async def _get_recent_questions(
        self,
        user_id: str,
        days: int,
        trace_id: str
    ) -> set[str]:
        """Get question IDs attempted recently by user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            trace_id: Trace ID for logging
            
        Returns:
            Set of question IDs
        """
        if days == 0:
            return set()
        
        # Placeholder: In production, would query user_question_history
        # cutoff_date = datetime.utcnow() - timedelta(days=days)
        # recent = await self.mongodb_client.user_question_history.find({
        #     "user_id": user_id,
        #     "attempted_at": {"$gte": cutoff_date}
        # }).to_list(1000)
        # return {r["question_id"] for r in recent}
        
        logger.debug(f"[{trace_id}] Excluding questions from last {days} days")
        return set()  # Placeholder
    
    def _get_sample_questions(
        self,
        topic_ids: list[str],
        subject: str,
        exclude_ids: set[str],
        preferred_types: list[str] | None
    ) -> list[QuestionItem]:
        """Get sample questions (placeholder for MongoDB query).
        
        In production, this would be replaced with actual MongoDB query.
        """
        # Sample questions for demonstration
        sample_questions = [
            # Easy questions
            QuestionItem(
                question_id="q001",
                question_text="Solve for x: 2x + 3 = 7",
                question_type="calculation",
                topic_id=topic_ids[0] if topic_ids else "topic_001",
                topic_name="Algebra",
                difficulty="easy",
                max_marks=2,
                estimated_minutes=3,
                order_index=0
            ),
            QuestionItem(
                question_id="q002",
                question_text="What is the value of π (pi)?",
                question_type="multiple_choice",
                topic_id=topic_ids[0] if topic_ids else "topic_001",
                topic_name="Algebra",
                difficulty="easy",
                max_marks=1,
                estimated_minutes=2,
                order_index=1
            ),
            # Medium questions
            QuestionItem(
                question_id="q003",
                question_text="Solve the quadratic equation: x² + 5x + 6 = 0",
                question_type="calculation",
                topic_id=topic_ids[0] if topic_ids else "topic_002",
                topic_name="Quadratic Equations",
                difficulty="medium",
                max_marks=5,
                estimated_minutes=8,
                order_index=2
            ),
            QuestionItem(
                question_id="q004",
                question_text="Factorize: x² - 9",
                question_type="calculation",
                topic_id=topic_ids[0] if topic_ids else "topic_001",
                topic_name="Algebra",
                difficulty="medium",
                max_marks=3,
                estimated_minutes=5,
                order_index=3
            ),
            # Hard questions
            QuestionItem(
                question_id="q005",
                question_text="Prove that √2 is irrational",
                question_type="essay",
                topic_id=topic_ids[0] if topic_ids else "topic_003",
                topic_name="Number Theory",
                difficulty="hard",
                max_marks=10,
                estimated_minutes=15,
                order_index=4
            ),
        ]
        
        # Filter by preferred types
        if preferred_types:
            sample_questions = [
                q for q in sample_questions
                if q.question_type in preferred_types
            ]
        
        # Filter by exclude_ids
        sample_questions = [
            q for q in sample_questions
            if q.question_id not in exclude_ids
        ]
        
        # Duplicate to have more questions
        # In production, MongoDB would return many questions
        extended_questions = []
        for i in range(5):  # Create 5x duplicates
            for q in sample_questions:
                q_copy = q.model_copy()
                q_copy.question_id = f"{q.question_id}_v{i}"
                extended_questions.append(q_copy)
        
        return extended_questions
