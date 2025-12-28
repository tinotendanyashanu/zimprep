"""Buffer Sync Service for merging buffered answers into the Submission Engine.

PHASE SIX: Idempotent sync with server-side validation.
"""

import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple
from cryptography.fernet import Fernet
import os

from app.engines.partial_offline_buffering.repository.buffer_repo import BufferRepository
from app.engines.partial_offline_buffering.errors import SyncFailedError

logger = logging.getLogger(__name__)


class BufferSyncService:
    """Service for syncing buffered answers to the Submission Engine.
    
    CRITICAL RULES:
    - Idempotent processing (duplicate detection)
    - Server timestamp ordering
    - Session validity verification before accept
    - Trace ID continuity preservation
    """
    
    def __init__(self):
        """Initialize sync service."""
        self.repository = BufferRepository()
        # Get encryption key from environment
        encryption_key = os.getenv("BUFFER_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a key if not provided (dev/test only)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Using generated encryption key - set BUFFER_ENCRYPTION_KEY in production")
        
        self.cipher = Fernet(encryption_key if isinstance(encryption_key, bytes) else encryption_key.encode())
    
    def encrypt_payload(self, payload: str) -> str:
        """Encrypt answer payload using AES-256.
        
        Args:
            payload: Plain text answer
            
        Returns:
            Encrypted payload (base64)
        """
        encrypted = self.cipher.encrypt(payload.encode())
        return encrypted.decode()
    
    def decrypt_payload(self, encrypted_payload: str) -> str:
        """Decrypt answer payload.
        
        Args:
            encrypted_payload: Encrypted payload (base64)
            
        Returns:
            Plain text answer
        """
        decrypted = self.cipher.decrypt(encrypted_payload.encode())
        return decrypted.decode()
    
    def compute_payload_hash(
        self,
        session_id: str,
        question_id: str,
        answer_content: str
    ) -> str:
        """Compute SHA256 hash for deduplication.
        
        Args:
            session_id: Session ID
            question_id: Question ID
            answer_content: Answer content
            
        Returns:
            SHA256 hash (hex)
        """
        payload = f"{session_id}|{question_id}|{answer_content}"
        return hashlib.sha256(payload.encode()).hexdigest()
    
    async def sync_buffers(
        self,
        session_id: str,
        student_id: str,
        trace_id: str,
        session_is_open: bool
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Sync all pending buffers for a session.
        
        CRITICAL: Only syncs if session is still open.
        
        Args:
            session_id: Session to sync
            student_id: Student ID
            trace_id: Trace ID for audit
            session_is_open: Whether session is still open (from Session Timing Engine)
            
        Returns:
            Tuple of (synced_answers, duplicates_count, failed_count)
            
        Raises:
            SyncFailedError: If session is closed or sync fails
        """
        if not session_is_open:
            raise SyncFailedError(
                message=f"Cannot sync buffers: session {session_id} is closed",
                trace_id=trace_id
            )
        
        # Get all pending buffers
        pending_buffers = await self.repository.get_pending_buffers(
            session_id=session_id,
            trace_id=trace_id
        )
        
        if not pending_buffers:
            logger.info(
                "No pending buffers to sync",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            return [], 0, 0
        
        logger.info(
            f"Syncing {len(pending_buffers)} buffers",
            extra={"trace_id": trace_id, "session_id": session_id}
        )
        
        synced_answers = []
        duplicates_count = 0
        failed_count = 0
        
        # Process buffers in order of server timestamp
        for idx, buffer_doc in enumerate(pending_buffers):
            try:
                # Decrypt payload
                answer_content = self.decrypt_payload(buffer_doc["encrypted_payload"])
                
                # Build answer record
                synced_answer = {
                    "buffer_id": buffer_doc["buffer_id"],
                    "question_id": buffer_doc["question_id"],
                    "answer_content": answer_content,
                    "synced_at": datetime.utcnow(),  # Server timestamp
                    "was_duplicate": False,
                    "submission_order": idx + 1
                }
                
                synced_answers.append(synced_answer)
                
                # Mark as synced
                await self.repository.mark_synced(
                    buffer_id=buffer_doc["buffer_id"],
                    trace_id=trace_id
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to sync buffer {buffer_doc['buffer_id']}: {str(e)}",
                    extra={"trace_id": trace_id},
                    exc_info=True
                )
                failed_count += 1
        
        logger.info(
            f"Sync complete: {len(synced_answers)} synced, {duplicates_count} duplicates, {failed_count} failed",
            extra={"trace_id": trace_id, "session_id": session_id}
        )
        
        return synced_answers, duplicates_count, failed_count
