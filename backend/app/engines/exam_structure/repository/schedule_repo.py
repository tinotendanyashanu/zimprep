"""Exam Schedule Repository.

Handles retrieval of scheduled exams from MongoDB.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ScheduleRepository:
    """Repository for exam schedule operations.
    
    Responsibilities:
    - Fetch upcoming scheduled exams
    - Filter by candidate, cohort, or school
    - Timezone-safe datetime handling (all UTC)
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository with MongoDB connection.
        
        Args:
            mongo_client: Optional MongoDB client (for testing)
        """
        if mongo_client is None:
            self.client = MongoClient(settings.MONGODB_URI)
        else:
            self.client = mongo_client
        
        self.db = self.client[settings.MONGODB_DB]
        self.collection = self.db["exam_schedules"]
    
    async def get_upcoming_exams(
        self,
        candidate_id: str,
        limit: int = 10,
        cohort_id: Optional[str] = None,
        school_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch upcoming scheduled exams for a candidate.
        
        Filters:
        - scheduled_date > now() (UTC)
        - status = "scheduled"
        - Matches candidate_id OR cohort_id OR school_id
        
        Args:
            candidate_id: Student candidate ID
            limit: Maximum number of exams to return (default 10)
            cohort_id: Optional cohort ID for cohort-based filtering
            school_id: Optional school ID for school-based filtering
            
        Returns:
            List of exam schedule documents, sorted by scheduled_date ASC
            
        Edge Cases:
        - No upcoming exams → Returns empty list
        - Invalid candidate_id → Returns empty list
        - Database error → Logs error, returns empty list
        """
        # Try cache first
        try:
            from app.services.exam_cache_service import ExamCacheService
            
            cached = ExamCacheService.get_upcoming_exams_cached(
                candidate_id=candidate_id,
                cohort_id=cohort_id,
                school_id=school_id
            )
            
            if cached is not None:
                return cached  # Cache HIT
        except Exception as cache_err:
            logger.warning(f"Cache retrieval error (continuing without cache): {cache_err}")
        
        # Cache MISS or cache error - query database
        try:
            # Current time in UTC
            now_utc = datetime.utcnow()
            
            # Build filter query
            # Match exams that are:
            # 1. In the future
            # 2. Status = scheduled
            # 3. Assigned to this candidate (directly, via cohort, or via school)
            filter_query = {
                "scheduled_date": {"$gt": now_utc},
                "status": "scheduled",
                "$or": [
                    {"candidate_ids": candidate_id},
                ]
            }
            
            # Add cohort filter if provided
            if cohort_id:
                filter_query["$or"].append({"cohort_id": cohort_id})
            
            # Add school filter if provided
            if school_id:
                filter_query["$or"].append({"school_id": school_id})
            
            # Execute query
            cursor = self.collection.find(filter_query).sort(
                "scheduled_date", ASCENDING
            ).limit(limit)
            
            # Convert to list
            schedules = list(cursor)
            
            # Convert ObjectId to string if present
            for schedule in schedules:
                if "_id" in schedule:
                    schedule["_id"] = str(schedule["_id"])
            
            logger.info(
                f"Retrieved {len(schedules)} upcoming exams for candidate {candidate_id}",
                extra={
                    "candidate_id": candidate_id,
                    "num_exams": len(schedules),
                    "cohort_id": cohort_id,
                    "school_id": school_id,
                }
            )
            
            # Cache the result for future requests
            try:
                from app.services.exam_cache_service import ExamCacheService
                ExamCacheService.set_upcoming_exams_cache(
                    candidate_id=candidate_id,
                    cohort_id=cohort_id,
                    school_id=school_id,
                    exams=schedules
                )
            except Exception as cache_err:
                logger.warning(f"Cache storage error (continuing without cache): {cache_err}")
            
            return schedules
        
        except PyMongoError as e:
            logger.error(
                f"Database error fetching upcoming exams: {e}",
                extra={
                    "candidate_id": candidate_id,
                    "error": str(e),
                },
                exc_info=True
            )
            return []
        
        except Exception as e:
            logger.error(
                f"Unexpected error fetching upcoming exams: {e}",
                extra={
                    "candidate_id": candidate_id,
                    "error": str(e),
                },
                exc_info=True
            )
            return []
    
    async def get_upcoming_exams_by_cohort(
        self,
        cohort_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch upcoming exams for an entire cohort.
        
        Used by institutional users (teachers, admins).
        
        Args:
            cohort_id: Cohort identifier
            limit: Maximum number of exams to return (default 50)
            
        Returns:
            List of exam schedule documents
        """
        try:
            now_utc = datetime.utcnow()
            
            filter_query = {
                "scheduled_date": {"$gt": now_utc},
                "status": "scheduled",
                "cohort_id": cohort_id,
            }
            
            cursor = self.collection.find(filter_query).sort(
                "scheduled_date", ASCENDING
            ).limit(limit)
            
            schedules = list(cursor)
            
            # Convert ObjectId to string
            for schedule in schedules:
                if "_id" in schedule:
                    schedule["_id"] = str(schedule["_id"])
            
            logger.info(
                f"Retrieved {len(schedules)} upcoming exams for cohort {cohort_id}",
                extra={
                    "cohort_id": cohort_id,
                    "num_exams": len(schedules),
                }
            )
            
            return schedules
        
        except Exception as e:
            logger.error(
                f"Error fetching cohort exams: {e}",
                extra={"cohort_id": cohort_id, "error": str(e)},
                exc_info=True
            )
            return []
    
    async def get_exam_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific exam schedule by ID.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Exam schedule document or None if not found
        """
        try:
            schedule = self.collection.find_one({"schedule_id": schedule_id})
            
            if schedule and "_id" in schedule:
                schedule["_id"] = str(schedule["_id"])
            
            return schedule
        
        except Exception as e:
            logger.error(
                f"Error fetching exam schedule: {e}",
                extra={"schedule_id": schedule_id, "error": str(e)},
                exc_info=True
            )
            return None
