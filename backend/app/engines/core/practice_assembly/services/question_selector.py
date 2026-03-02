"""Question selection service for practice sessions.

Selects questions from MongoDB based on topics, filters, and recency.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Set, Optional

from app.config.database import get_database
from app.config.knowledge_contract import CANONICAL_QUESTIONS
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
            mongodb_client: MongoDB client (optional, uses shared DB if None)
        """
        self.mongodb_client = mongodb_client
        self.db = None
    
    def _get_db(self):
        """Get database handle."""
        if self.db is None:
            if self.mongodb_client:
                # For testing with injected client
                from app.config.settings import settings
                self.db = self.mongodb_client[settings.MONGODB_DB]
            else:
                # Use shared database
                self.db = get_database()
        return self.db
    
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
        
        # Query canonical_questions collection
        db = self._get_db()
        collection = db[CANONICAL_QUESTIONS]
        
        # Build query filter
        query_filter = {
            "subject": subject,
            "level": syllabus_version,
        }
        
        # Exclude recently attempted questions
        if recent_question_ids:
            query_filter["canonical_question_id"] = {"$nin": list(recent_question_ids)}
        
        logger.info(f"[{trace_id}] Querying {CANONICAL_QUESTIONS} with filter: {query_filter}")
        
        # Execute query
        cursor = collection.find(query_filter).limit(100)
        raw_questions = list(cursor)
        
        logger.info(f"[{trace_id}] Found {len(raw_questions)} questions from database")
        
        # Map to QuestionItem schema
        questions = []
        for idx, q in enumerate(raw_questions):
            try:
                question_item = self._map_to_question_item(q, idx, topic_ids)
                
                # Filter by preferred types if specified
                if preferred_question_types and question_item.question_type not in preferred_question_types:
                    continue
                
                questions.append(question_item)
            except Exception as e:
                logger.warning(
                    f"[{trace_id}] Failed to map question {q.get('canonical_question_id')}: {e}"
                )
                continue
        
        logger.info(f"[{trace_id}] Mapped {len(questions)} questions successfully")
        
        # FAIL-FAST: Ensure we have questions from canonical_questions
        if len(questions) == 0:
            error_msg = (
                f"No questions found in {CANONICAL_QUESTIONS} collection for "
                f"subject={subject}, level={syllabus_version}. "
                f"Verify ingestion data exists."
            )
            logger.error(f"[{trace_id}] {error_msg}")
            raise InsufficientQuestionsError(
                message=error_msg,
                trace_id=trace_id,
                metadata={
                    "subject": subject,
                    "syllabus_version": syllabus_version,
                    "topic_ids": topic_ids,
                }
            )
        
        return questions
    
    def _map_to_question_item(
        self,
        raw_question: dict,
        index: int,
        topic_ids: List[str]
    ) -> QuestionItem:
        """Map ingestion schema to QuestionItem schema.
        
        Ingestion schema:
        - canonical_question_id: str
        - text: str
        - subject: str
        - level: str
        - has_graph: bool
        - graph_refs: list[str]
        - marking_scheme: dict (optional)
        
        Runtime schema:
        - question_id: str
        - question_text: str
        - question_type: str
        - topic_id: str
        - topic_name: str
        - difficulty: str
        - max_marks: int
        - estimated_minutes: int
        """
        question_id = raw_question.get("canonical_question_id", str(raw_question.get("_id")))
        question_text = raw_question.get("text", "")
        
        # Infer question type from metadata or default
        has_graph = raw_question.get("has_graph", False)
        question_type = "graph" if has_graph else "calculation"
        
        # Extract marks from marking scheme if available
        marking_scheme = raw_question.get("marking_scheme", {})
        max_marks = marking_scheme.get("total_marks", 5)
        
        # Estimate difficulty and time based on marks
        if max_marks <= 2:
            difficulty = "easy"
            estimated_minutes = 3
        elif max_marks <= 5:
            difficulty = "medium"
            estimated_minutes = 8
        else:
            difficulty = "hard"
            estimated_minutes = 15
        
        # Use first topic_id or derive from metadata
        topic_id = topic_ids[0] if topic_ids else raw_question.get("topic_id", "unknown")
        topic_name = raw_question.get("topic", raw_question.get("subject", "General"))
        
        return QuestionItem(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            topic_id=topic_id,
            topic_name=topic_name,
            difficulty=difficulty,
            max_marks=max_marks,
            estimated_minutes=estimated_minutes,
            order_index=index
        )
    
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
        
        # TODO: Query user_question_history or submissions collection
        # For now, return empty set (no recency filtering)
        logger.debug(f"[{trace_id}] Recency filtering not yet implemented")
        return set()
