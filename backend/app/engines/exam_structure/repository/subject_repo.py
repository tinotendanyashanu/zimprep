"""Subject repository for read-only MongoDB access.

Retrieves subject definitions from the subjects collection.
"""

import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.engines.exam_structure.errors import (
    SubjectNotFoundError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class SubjectRepository:
    """Read-only repository for subject definitions.
    
    All operations are read-only. No database writes allowed.
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance (if None, creates default)
        """
        self.mongo_client = mongo_client
        self._db_name = "zimprep"
        self._collection_name = "subjects"
    
    async def get_subject(
        self,
        subject_code: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """Retrieve subject definition by code.
        
        Args:
            subject_code: ZIMSEC subject code (e.g., "4008")
            trace_id: Request trace ID for logging
            
        Returns:
            Subject definition document
            
        Raises:
            SubjectNotFoundError: Subject not found
            DatabaseError: Database connection or query error
        """
        try:
            logger.info(
                "Fetching subject",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                }
            )
            
            if not self.mongo_client:
                # For now, fail fast if no MongoDB connection
                # In production, this would connect to real MongoDB
                raise DatabaseError(
                    message=f"MongoDB client not initialized",
                    trace_id=trace_id,
                    metadata={"subject_code": subject_code},
                )
            
            db = self.mongo_client[self._db_name]
            collection = db[self._collection_name]
            
            # Query for subject by code
            subject = collection.find_one({"code": subject_code})
            
            if not subject:
                logger.warning(
                    "Subject not found",
                    extra={
                        "trace_id": trace_id,
                        "subject_code": subject_code,
                    }
                )
                raise SubjectNotFoundError(
                    message=f"Subject '{subject_code}' not found in database",
                    trace_id=trace_id,
                    metadata={"subject_code": subject_code},
                )
            
            logger.info(
                "Subject retrieved successfully",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "subject_name": subject.get("name"),
                }
            )
            
            return subject
            
        except SubjectNotFoundError:
            # Re-raise specific errors
            raise
        except PyMongoError as e:
            logger.error(
                "Database error while fetching subject",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Database error: {str(e)}",
                trace_id=trace_id,
                metadata={"subject_code": subject_code, "error_type": type(e).__name__},
            )
        except Exception as e:
            logger.error(
                "Unexpected error while fetching subject",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Unexpected database error: {str(e)}",
                trace_id=trace_id,
                metadata={"subject_code": subject_code, "error_type": type(e).__name__},
            )
