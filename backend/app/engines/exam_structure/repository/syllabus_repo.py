"""Syllabus repository for read-only MongoDB access.

Retrieves versioned syllabus definitions.
"""

import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.engines.exam_structure.errors import (
    InvalidSyllabusVersionError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class SyllabusRepository:
    """Read-only repository for syllabus definitions.
    
    Handles versioned syllabus retrieval.
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self._db_name = "zimprep"
        self._collection_name = "syllabuses"
    
    async def get_syllabus(
        self,
        subject_code: str,
        syllabus_version: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """Retrieve syllabus definition by subject and version.
        
        Args:
            subject_code: ZIMSEC subject code
            syllabus_version: Syllabus version (e.g., "2023-2027")
            trace_id: Request trace ID
            
        Returns:
            Syllabus definition document
            
        Raises:
            InvalidSyllabusVersionError: Syllabus version not found or invalid
            DatabaseError: Database error
        """
        try:
            logger.info(
                "Fetching syllabus",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                }
            )
            
            if not self.mongo_client:
                raise DatabaseError(
                    message="MongoDB client not initialized",
                    trace_id=trace_id,
                    metadata={
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                    },
                )
            
            db = self.mongo_client[self._db_name]
            collection = db[self._collection_name]
            
            # Query for exact subject and version match
            syllabus = collection.find_one({
                "subject_code": subject_code,
                "version": syllabus_version,
            })
            
            if not syllabus:
                logger.warning(
                    "Syllabus version not found",
                    extra={
                        "trace_id": trace_id,
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                    }
                )
                raise InvalidSyllabusVersionError(
                    message=f"Syllabus version '{syllabus_version}' not found for subject '{subject_code}'",
                    trace_id=trace_id,
                    metadata={
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                    },
                )
            
            logger.info(
                "Syllabus retrieved successfully",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                }
            )
            
            return syllabus
            
        except InvalidSyllabusVersionError:
            raise
        except PyMongoError as e:
            logger.error(
                "Database error while fetching syllabus",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Database error: {str(e)}",
                trace_id=trace_id,
                metadata={
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            logger.error(
                "Unexpected error while fetching syllabus",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Unexpected database error: {str(e)}",
                trace_id=trace_id,
                metadata={
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                    "error_type": type(e).__name__,
                },
            )
