"""MongoDB repository for answer buffers.

PHASE SIX: Manages the answer_buffers collection with strict immutability.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)


class BufferRepository:
    """Repository for managing buffered answers in MongoDB.
    
    Collection: answer_buffers
    Immutability: ALL writes are append-only
    """
    
    def __init__(self):
        """Initialize repository with MongoDB connection."""
        from app.config.settings import settings
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]  # Explicit database name
        self.collection = self.db.answer_buffers
        
    async def create_buffer(
        self,
        buffer_id: str,
        session_id: str,
        student_id: str,
        device_id: str,
        question_id: str,
        buffered_payload_hash: str,
        encrypted_payload: str,
        client_timestamp: datetime,
        trace_id: str
    ) -> Dict[str, Any]:
        """Create a new answer buffer record.
        
        CRITICAL: This is append-only. No updates allowed.
        
        Args:
            buffer_id: Unique buffer identifier
            session_id: Session ID
            student_id: Student ID
            device_id: Device ID
            question_id: Question ID
            buffered_payload_hash: SHA256 hash for deduplication
            encrypted_payload: AES-256 encrypted answer content
            client_timestamp: Client timestamp (advisory)
            trace_id: Trace ID for audit
            
        Returns:
            Created buffer document
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)  # 24-hour expiry
        
        buffer_doc = {
            "buffer_id": buffer_id,
            "session_id": session_id,
            "student_id": student_id,
            "device_id": device_id,
            "question_id": question_id,
            "buffered_payload_hash": buffered_payload_hash,
            "encrypted_payload": encrypted_payload,
            "buffered_at": now,  # Server timestamp (canonical)
            "client_timestamp": client_timestamp,  # Advisory
            "expires_at": expires_at,
            "synced_at": None,
            "sync_status": "pending",
            "trace_id": trace_id,
            "_immutable": True,
            "_created_at": now,
            "_version": 1
        }
        
        await self.collection.insert_one(buffer_doc)
        logger.info(
            f"Buffer created: {buffer_id}",
            extra={"trace_id": trace_id, "session_id": session_id}
        )
        
        return buffer_doc
    
    async def get_pending_buffers(
        self,
        session_id: str,
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Get all pending buffers for a session.
        
        Args:
            session_id: Session ID
            trace_id: Trace ID
            
        Returns:
            List of pending buffer documents
        """
        cursor = self.collection.find({
            "session_id": session_id,
            "sync_status": "pending",
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("buffered_at", 1)  # Order by server timestamp
        
        buffers = await cursor.to_list(length=100)  # Max 100 buffers
        
        logger.debug(
            f"Retrieved {len(buffers)} pending buffers",
            extra={"trace_id": trace_id, "session_id": session_id}
        )
        
        return buffers
    
    async def check_duplicate(
        self,
        buffered_payload_hash: str,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a buffer with this hash already exists.
        
        Args:
            buffered_payload_hash: SHA256 hash to check
            trace_id: Trace ID
            
        Returns:
            Existing buffer document or None
        """
        existing = await self.collection.find_one({
            "buffered_payload_hash": buffered_payload_hash
        })
        
        if existing:
            logger.warning(
                f"Duplicate buffer detected: {buffered_payload_hash}",
                extra={"trace_id": trace_id}
            )
        
        return existing
    
    async def mark_synced(
        self,
        buffer_id: str,
        trace_id: str
    ) -> None:
        """Mark a buffer as successfully synced.
        
        NOTE: This is one of the few allowed updates (status only).
        
        Args:
            buffer_id: Buffer ID to mark
            trace_id: Trace ID
        """
        await self.collection.update_one(
            {"buffer_id": buffer_id},
            {
                "$set": {
                    "sync_status": "synced",
                    "synced_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(
            f"Buffer marked as synced: {buffer_id}",
            extra={"trace_id": trace_id}
        )
    
    async def count_session_buffers(
        self,
        session_id: str,
        trace_id: str
    ) -> int:
        """Count pending buffers for a session.
        
        Args:
            session_id: Session ID
            trace_id: Trace ID
            
        Returns:
            Count of pending buffers
        """
        count = await self.collection.count_documents({
            "session_id": session_id,
            "sync_status": "pending"
        })
        
        return count
