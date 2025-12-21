"""Paper repository for read-only MongoDB access.

Retrieves paper definitions and section layouts.
"""

import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.engines.exam_structure.errors import (
    PaperNotFoundError,
    SectionDefinitionError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class PaperRepository:
    """Read-only repository for paper and section definitions."""
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self._db_name = "zimprep"
        self._papers_collection = "papers"
        self._sections_collection = "sections"
    
    async def get_paper(
        self,
        subject_code: str,
        syllabus_version: str,
        paper_code: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """Retrieve paper definition.
        
        Args:
            subject_code: ZIMSEC subject code
            syllabus_version: Syllabus version
            paper_code: Paper identifier
            trace_id: Request trace ID
            
        Returns:
            Paper definition document
            
        Raises:
            PaperNotFoundError: Paper not found
            DatabaseError: Database error
        """
        try:
            logger.info(
                "Fetching paper",
                extra={
                    "trace_id": trace_id,
                    "subject_code": subject_code,
                    "syllabus_version": syllabus_version,
                    "paper_code": paper_code,
                }
            )
            
            if not self.mongo_client:
                raise DatabaseError(
                    message="MongoDB client not initialized",
                    trace_id=trace_id,
                    metadata={
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                        "paper_code": paper_code,
                    },
                )
            
            db = self.mongo_client[self._db_name]
            collection = db[self._papers_collection]
            
            # Query for exact match
            paper = collection.find_one({
                "subject_code": subject_code,
                "syllabus_version": syllabus_version,
                "paper_code": paper_code,
            })
            
            if not paper:
                logger.warning(
                    "Paper not found",
                    extra={
                        "trace_id": trace_id,
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                        "paper_code": paper_code,
                    }
                )
                raise PaperNotFoundError(
                    message=f"Paper '{paper_code}' not found for subject '{subject_code}' version '{syllabus_version}'",
                    trace_id=trace_id,
                    metadata={
                        "subject_code": subject_code,
                        "syllabus_version": syllabus_version,
                        "paper_code": paper_code,
                    },
                )
            
            logger.info(
                "Paper retrieved successfully",
                extra={
                    "trace_id": trace_id,
                    "paper_id": str(paper.get("_id")),
                    "paper_name": paper.get("paper_name"),
                }
            )
            
            return paper
            
        except PaperNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(
                "Database error while fetching paper",
                extra={
                    "trace_id": trace_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Database error: {str(e)}",
                trace_id=trace_id,
                metadata={"error_type": type(e).__name__},
            )
        except Exception as e:
            logger.error(
                "Unexpected error while fetching paper",
                extra={
                    "trace_id": trace_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Unexpected database error: {str(e)}",
                trace_id=trace_id,
                metadata={"error_type": type(e).__name__},
            )
    
    async def get_sections(
        self,
        paper_id: str,
        trace_id: str,
    ) -> List[Dict[str, Any]]:
        """Retrieve all sections for a paper.
        
        Args:
            paper_id: Paper document ID
            trace_id: Request trace ID
            
        Returns:
            List of section definition documents
            
        Raises:
            SectionDefinitionError: Invalid or missing sections
            DatabaseError: Database error
        """
        try:
            logger.info(
                "Fetching sections",
                extra={
                    "trace_id": trace_id,
                    "paper_id": paper_id,
                }
            )
            
            if not self.mongo_client:
                raise DatabaseError(
                    message="MongoDB client not initialized",
                    trace_id=trace_id,
                    metadata={"paper_id": paper_id},
                )
            
            db = self.mongo_client[self._db_name]
            collection = db[self._sections_collection]
            
            # Query all sections for this paper
            sections = list(collection.find({"paper_id": paper_id}))
            
            if not sections:
                logger.error(
                    "No sections found for paper",
                    extra={
                        "trace_id": trace_id,
                        "paper_id": paper_id,
                    }
                )
                raise SectionDefinitionError(
                    message=f"No sections found for paper '{paper_id}'",
                    trace_id=trace_id,
                    metadata={"paper_id": paper_id},
                )
            
            logger.info(
                "Sections retrieved successfully",
                extra={
                    "trace_id": trace_id,
                    "paper_id": paper_id,
                    "num_sections": len(sections),
                }
            )
            
            return sections
            
        except SectionDefinitionError:
            raise
        except PyMongoError as e:
            logger.error(
                "Database error while fetching sections",
                extra={
                    "trace_id": trace_id,
                    "paper_id": paper_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Database error: {str(e)}",
                trace_id=trace_id,
                metadata={"paper_id": paper_id, "error_type": type(e).__name__},
            )
        except Exception as e:
            logger.error(
                "Unexpected error while fetching sections",
                extra={
                    "trace_id": trace_id,
                    "paper_id": paper_id,
                    "error": str(e),
                },
                exc_info=True
            )
            raise DatabaseError(
                message=f"Unexpected database error: {str(e)}",
                trace_id=trace_id,
                metadata={"paper_id": paper_id, "error_type": type(e).__name__},
            )
