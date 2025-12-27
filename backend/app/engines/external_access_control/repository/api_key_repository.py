"""Repository for managing external API keys.

Handles CRUD operations for the external_access_keys MongoDB collection.
"""

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.engines.external_access_control.schemas import (
    APIKeyRecord,
    AccessScope,
    AccessStatus,
    RateLimits
)


logger = logging.getLogger(__name__)


class APIKeyRepository:
    """Repository for external API key management."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db["external_access_keys"]
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key using SHA-256.
        
        Args:
            api_key: Plaintext API key
            
        Returns:
            Hashed API key (hex digest)
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a cryptographically secure API key.
        
        Returns:
            Random API key (64 characters, hex)
        """
        return secrets.token_hex(32)
    
    async def create_api_key(
        self,
        partner_id: str,
        scopes: list[AccessScope],
        rate_limits: Optional[RateLimits] = None,
        expires_at: Optional[datetime] = None,
        partner_metadata: Optional[dict] = None
    ) -> tuple[str, APIKeyRecord]:
        """Create a new API key.
        
        Args:
            partner_id: Partner identifier
            scopes: List of granted scopes
            rate_limits: Rate limit configuration (defaults to standard limits)
            expires_at: Optional expiration timestamp
            partner_metadata: Optional partner-specific metadata
            
        Returns:
            Tuple of (plaintext_api_key, APIKeyRecord)
            
        Raises:
            DuplicateKeyError: If key_id or key_hash already exists
        """
        # Generate plaintext API key
        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)
        
        # Generate unique key ID
        key_id = f"key_{secrets.token_hex(16)}"
        
        # Use default rate limits if not provided
        if rate_limits is None:
            rate_limits = RateLimits()
        
        # Create record
        record = APIKeyRecord(
            key_id=key_id,
            partner_id=partner_id,
            key_hash=key_hash,
            scopes=scopes,
            rate_limits=rate_limits,
            status=AccessStatus.ACTIVE,
            issued_at=datetime.utcnow(),
            expires_at=expires_at,
            partner_metadata=partner_metadata or {}
        )
        
        # Insert into MongoDB
        await self.collection.insert_one(record.dict())
        
        logger.info(
            f"Created API key for partner {partner_id}: {key_id} "
            f"with scopes {[s.value for s in scopes]}"
        )
        
        return api_key, record
    
    async def get_by_api_key(self, api_key: str) -> Optional[APIKeyRecord]:
        """Retrieve API key record by plaintext key.
        
        Args:
            api_key: Plaintext API key
            
        Returns:
            APIKeyRecord or None if not found
        """
        key_hash = self.hash_api_key(api_key)
        doc = await self.collection.find_one({"key_hash": key_hash})
        
        if doc:
            return APIKeyRecord(**doc)
        return None
    
    async def get_by_key_id(self, key_id: str) -> Optional[APIKeyRecord]:
        """Retrieve API key record by key ID.
        
        Args:
            key_id: API key ID
            
        Returns:
            APIKeyRecord or None if not found
        """
        doc = await self.collection.find_one({"key_id": key_id})
        
        if doc:
            return APIKeyRecord(**doc)
        return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key.
        
        Args:
            key_id: API key ID to revoke
            
        Returns:
            True if revoked, False if not found
        """
        result = await self.collection.update_one(
            {"key_id": key_id},
            {
                "$set": {
                    "status": AccessStatus.REVOKED.value,
                    "revoked_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.warning(f"Revoked API key: {key_id}")
            return True
        
        return False
    
    async def suspend_api_key(self, key_id: str) -> bool:
        """Suspend an API key (can be reactivated later).
        
        Args:
            key_id: API key ID to suspend
            
        Returns:
            True if suspended, False if not found
        """
        result = await self.collection.update_one(
            {"key_id": key_id},
            {"$set": {"status": AccessStatus.SUSPENDED.value}}
        )
        
        if result.modified_count > 0:
            logger.warning(f"Suspended API key: {key_id}")
            return True
        
        return False
    
    async def reactivate_api_key(self, key_id: str) -> bool:
        """Reactivate a suspended API key.
        
        Args:
            key_id: API key ID to reactivate
            
        Returns:
            True if reactivated, False if not found or revoked
        """
        # Only reactivate if currently suspended
        result = await self.collection.update_one(
            {
                "key_id": key_id,
                "status": AccessStatus.SUSPENDED.value
            },
            {"$set": {"status": AccessStatus.ACTIVE.value}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Reactivated API key: {key_id}")
            return True
        
        return False
    
    async def rotate_api_key(self, key_id: str) -> Optional[tuple[str, APIKeyRecord]]:
        """Rotate an API key (generate new key, keep same key_id).
        
        Args:
            key_id: API key ID to rotate
            
        Returns:
            Tuple of (new_plaintext_key, updated_record) or None if not found
        """
        # Get existing record
        existing = await self.get_by_key_id(key_id)
        if not existing:
            return None
        
        # Generate new API key
        new_api_key = self.generate_api_key()
        new_key_hash = self.hash_api_key(new_api_key)
        
        # Update record
        result = await self.collection.update_one(
            {"key_id": key_id},
            {
                "$set": {
                    "key_hash": new_key_hash,
                    "rotated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            updated = await self.get_by_key_id(key_id)
            logger.info(f"Rotated API key: {key_id}")
            return new_api_key, updated
        
        return None
    
    async def list_by_partner(self, partner_id: str) -> list[APIKeyRecord]:
        """List all API keys for a partner.
        
        Args:
            partner_id: Partner identifier
            
        Returns:
            List of APIKeyRecord
        """
        cursor = self.collection.find({"partner_id": partner_id})
        docs = await cursor.to_list(length=1000)
        
        return [APIKeyRecord(**doc) for doc in docs]
