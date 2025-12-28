"""MongoDB schema setup for Phase Six collections.

PHASE SIX: Mobile & Low-Connectivity Resilience

Creates and validates the following collections:
- answer_buffers
- device_connectivity_events
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_phase_six_schemas():
    """Set up MongoDB schemas for Phase Six collections."""
    
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://zimprep:zimprep@localhost:27017/zimprep?authSource=admin")
    client = AsyncIOMotorClient(mongodb_uri)
    db = client.get_database()
    
    logger.info("Setting up Phase Six MongoDB schemas...")
    
    # =============================================================================
    # Collection 1: answer_buffers
    # =============================================================================
    
    logger.info("Creating answer_buffers collection...")
    
    answer_buffers_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "buffer_id",
                "session_id",
                "student_id",
                "device_id",
                "question_id",
                "buffered_payload_hash",
                "encrypted_payload",
                "buffered_at",
                "client_timestamp",
                "expires_at",
                "sync_status",
                "trace_id",
                "_immutable",
                "_created_at",
                "_version"
            ],
            "properties": {
                "buffer_id": {"bsonType": "string"},
                "session_id": {"bsonType": "string"},
                "student_id": {"bsonType": "string"},
                "device_id": {"bsonType": "string"},
                "question_id": {"bsonType": "string"},
                "buffered_payload_hash": {
                    "bsonType": "string",
                    "minLength": 64,
                    "maxLength": 64,
                    "description": "SHA256 hash for deduplication"
                },
                "encrypted_payload": {
                    "bsonType": "string",
                    "description": "AES-256 encrypted answer content"
                },
                "buffered_at": {
                    "bsonType": "date",
                    "description": "Server timestamp (canonical)"
                },
                "client_timestamp": {
                    "bsonType": "date",
                    "description": "Client timestamp (advisory)"
                },
                "expires_at": {
                    "bsonType": "date",
                    "description": "Buffer expiry time (24h default)"
                },
                "synced_at": {
                    "bsonType": ["date", "null"],
                    "description": "Server timestamp when synced"
                },
                "sync_status": {
                    "enum": ["pending", "syncing", "synced", "failed"],
                    "description": "Current sync status"
                },
                "trace_id": {
                    "bsonType": "string",
                    "description": "Trace ID for audit continuity"
                },
                "_immutable": {
                    "bsonType": "bool",
                    "enum": [True],
                    "description": "Immutability marker"
                },
                "_created_at": {
                    "bsonType": "date",
                    "description": "Record creation timestamp"
                },
                "_version": {
                    "bsonType": "int",
                    "minimum": 1,
                    "description": "Schema version"
                }
            }
        }
    }
    
    # Drop collection if it exists (dev/test only)
    await db.answer_buffers.drop()
    
    # Create collection with schema validation
    await db.create_collection(
        "answer_buffers",
        validator=answer_buffers_schema
    )
    
    # Create indexes
    await db.answer_buffers.create_index([("session_id", 1), ("sync_status", 1)])
    await db.answer_buffers.create_index([("student_id", 1), ("buffered_at", -1)])
    await db.answer_buffers.create_index([("buffered_payload_hash", 1)], unique=True)
    await db.answer_buffers.create_index([("trace_id", 1)])
    await db.answer_buffers.create_index([("expires_at", 1)])  # For TTL cleanup
    
    logger.info("✓ answer_buffers collection created with schema validation and indexes")
    
    # =============================================================================
    # Collection 2: device_connectivity_events
    # =============================================================================
    
    logger.info("Creating device_connectivity_events collection...")
    
    connectivity_events_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "event_id",
                "session_id",
                "student_id",
                "device_id",
                "connectivity_state",
                "disconnect_duration_seconds",
                "event_timestamp",
                "network_type",
                "trace_id",
                "_immutable",
                "_created_at"
            ],
            "properties": {
                "event_id": {"bsonType": "string"},
                "session_id": {"bsonType": "string"},
                "student_id": {"bsonType": "string"},
                "device_id": {"bsonType": "string"},
                "connectivity_state": {
                    "enum": ["connected", "short_disconnect", "medium_disconnect", "long_disconnect"],
                    "description": "Connectivity state enum"
                },
                "disconnect_duration_seconds": {
                    "bsonType": "int",
                    "minimum": 0,
                    "description": "Seconds since last heartbeat"
                },
                "event_timestamp": {
                    "bsonType": "date",
                    "description": "Server timestamp (canonical)"
                },
                "network_type": {
                    "enum": ["wifi", "cellular", "ethernet", "unknown"],
                    "description": "Network connection type"
                },
                "signal_strength": {
                    "bsonType": ["int", "null"],
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Signal strength percentage"
                },
                "trace_id": {
                    "bsonType": "string",
                    "description": "Trace ID for audit"
                },
                "_immutable": {
                    "bsonType": "bool",
                    "enum": [True],
                    "description": "Immutability marker"
                },
                "_created_at": {
                    "bsonType": "date",
                    "description": "Record creation timestamp"
                }
            }
        }
    }
    
    # Drop collection if it exists (dev/test only)
    await db.device_connectivity_events.drop()
    
    # Create collection with schema validation
    await db.create_collection(
        "device_connectivity_events",
        validator=connectivity_events_schema
    )
    
    # Create indexes
    await db.device_connectivity_events.create_index([("session_id", 1), ("event_timestamp", -1)])
    await db.device_connectivity_events.create_index([("student_id", 1), ("event_timestamp", -1)])
    await db.device_connectivity_events.create_index([("device_id", 1)])
    await db.device_connectivity_events.create_index([("trace_id", 1)])
    
    logger.info("✓ device_connectivity_events collection created with schema validation and indexes")
    
    logger.info("✓ Phase Six schema setup complete")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(setup_phase_six_schemas())
