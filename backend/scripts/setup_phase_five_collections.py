"""Setup MongoDB collections for Phase Five: External Integrations.

Creates collections and indexes for:
1. external_access_keys - API key storage and management
2. external_api_audit_logs - Immutable external request audit logs
"""

import asyncio
import logging
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app.config.settings import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_phase_five_collections():
    """Create Phase Five MongoDB collections with validation and indexes."""
    
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DATABASE]
    
    logger.info("Setting up Phase Five collections...")
    
    # =========================================================================
    # Collection 1: external_access_keys
    # =========================================================================
    
    try:
        # Define JSON schema validation for external_access_keys
        external_access_keys_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "key_id",
                    "partner_id",
                    "key_hash",
                    "scopes",
                    "rate_limits",
                    "status",
                    "issued_at"
                ],
                "properties": {
                    "key_id": {
                        "bsonType": "string",
                        "description": "Unique API key identifier - required"
                    },
                    "partner_id": {
                        "bsonType": "string",
                        "description": "Partner identifier - required"
                    },
                    "key_hash": {
                        "bsonType": "string",
                        "description": "Hashed API key (SHA-256) - required"
                    },
                    "scopes": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "string",
                            "enum": [
                                "read:results",
                                "read:analytics",
                                "read:governance",
                                "read:metadata"
                            ]
                        },
                        "description": "Granted scopes - required"
                    },
                    "rate_limits": {
                        "bsonType": "object",
                        "required": ["requests_per_hour", "requests_per_minute", "burst_limit"],
                        "properties": {
                            "requests_per_hour": {"bsonType": "int"},
                            "requests_per_minute": {"bsonType": "int"},
                            "burst_limit": {"bsonType": "int"}
                        },
                        "description": "Rate limit configuration - required"
                    },
                    "status": {
                        "bsonType": "string",
                        "enum": ["active", "revoked", "suspended", "expired"],
                        "description": "API key status - required"
                    },
                    "issued_at": {
                        "bsonType": "date",
                        "description": "Key issuance timestamp - required"
                    },
                    "rotated_at": {
                        "bsonType": ["date", "null"],
                        "description": "Last rotation timestamp"
                    },
                    "revoked_at": {
                        "bsonType": ["date", "null"],
                        "description": "Revocation timestamp"
                    },
                    "expires_at": {
                        "bsonType": ["date", "null"],
                        "description": "Expiration timestamp"
                    },
                    "partner_metadata": {
                        "bsonType": "object",
                        "description": "Partner-specific metadata"
                    }
                }
            }
        }
        
        # Create collection with validation
        await db.create_collection(
            "external_access_keys",
            validator=external_access_keys_schema
        )
        logger.info("✓ Created collection: external_access_keys")
        
    except CollectionInvalid:
        logger.info("Collection external_access_keys already exists")
    
    # Create indexes for external_access_keys
    keys_collection = db["external_access_keys"]
    
    await keys_collection.create_index("key_id", unique=True)
    logger.info("✓ Created unique index on key_id")
    
    await keys_collection.create_index("key_hash", unique=True)
    logger.info("✓ Created unique index on key_hash")
    
    await keys_collection.create_index("partner_id")
    logger.info("✓ Created index on partner_id")
    
    await keys_collection.create_index("status")
    logger.info("✓ Created index on status")
    
    # =========================================================================
    # Collection 2: external_api_audit_logs
    # =========================================================================
    
    try:
        # Define JSON schema validation for external_api_audit_logs
        external_audit_schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "audit_id",
                    "trace_id",
                    "partner_id",
                    "api_key_id",
                    "endpoint",
                    "response_status",
                    "timestamp",
                    "immutable"
                ],
                "properties": {
                    "audit_id": {
                        "bsonType": "string",
                        "description": "Unique audit log identifier - required"
                    },
                    "trace_id": {
                        "bsonType": "string",
                        "description": "Links to pipeline execution - required"
                    },
                    "partner_id": {
                        "bsonType": "string",
                        "description": "Partner identifier - required"
                    },
                    "api_key_id": {
                        "bsonType": "string",
                        "description": "API key used - required"
                    },
                    "endpoint": {
                        "bsonType": "string",
                        "description": "Endpoint accessed - required"
                    },
                    "pipeline": {
                        "bsonType": ["string", "null"],
                        "description": "Pipeline executed (if any)"
                    },
                    "response_status": {
                        "bsonType": "string",
                        "enum": ["success", "denied", "rate_limited"],
                        "description": "Response status - required"
                    },
                    "request_metadata": {
                        "bsonType": "object",
                        "description": "Request context (IP, user-agent, etc.)"
                    },
                    "timestamp": {
                        "bsonType": "date",
                        "description": "Request timestamp - required"
                    },
                    "immutable": {
                        "bsonType": "bool",
                        "description": "Write-once enforcement flag - required"
                    }
                }
            }
        }
        
        # Create collection with validation
        await db.create_collection(
            "external_api_audit_logs",
            validator=external_audit_schema
        )
        logger.info("✓ Created collection: external_api_audit_logs")
        
    except CollectionInvalid:
        logger.info("Collection external_api_audit_logs already exists")
    
    # Create indexes for external_api_audit_logs
    audit_collection = db["external_api_audit_logs"]
    
    await audit_collection.create_index("audit_id", unique=True)
    logger.info("✓ Created unique index on audit_id")
    
    await audit_collection.create_index("trace_id")
    logger.info("✓ Created index on trace_id")
    
    await audit_collection.create_index("partner_id")
    logger.info("✓ Created index on partner_id")
    
    await audit_collection.create_index("timestamp")
    logger.info("✓ Created index on timestamp")
    
    await audit_collection.create_index("endpoint")
    logger.info("✓ Created index on endpoint")
    
    # =========================================================================
    # Phase Five Setup Complete
    # =========================================================================
    
    logger.info("\n✅ Phase Five collections setup complete!")
    logger.info("  - external_access_keys (with 4 indexes)")
    logger.info("  - external_api_audit_logs (with 5 indexes)")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(setup_phase_five_collections())
