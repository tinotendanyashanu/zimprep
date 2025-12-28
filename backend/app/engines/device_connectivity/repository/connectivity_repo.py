"""MongoDB repository for device connectivity events.

PHASE SIX: Manages the device_connectivity_events collection for tracking heartbeats.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)


class ConnectivityRepository:
    """Repository for managing device connectivity events in MongoDB.
    
    Collection: device_connectivity_events
    Immutability: ALL writes are append-only
    """
    
    def __init__(self):
        """Initialize repository with MongoDB connection."""
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/zimprep")
        self.client = AsyncIOMotorClient(mongodb_uri)
        self.db = self.client.get_database()
        self.collection = self.db.device_connectivity_events
        
    async def log_heartbeat(
        self,
        event_id: str,
        session_id: str,
        student_id: str,
        device_id: str,
        connectivity_state: str,
        disconnect_duration_seconds: int,
        network_type: str,
        signal_strength: Optional[int],
        trace_id: str
    ) -> Dict[str, Any]:
        """Log a connectivity heartbeat event.
        
        CRITICAL: This is append-only. No updates allowed.
        
        Args:
            event_id: Unique event identifier
            session_id: Session ID
            student_id: Student ID
            device_id: Device ID
            connectivity_state: Connectivity state enum value
            disconnect_duration_seconds: Seconds since last heartbeat
            network_type: Network type (wifi, cellular, etc)
            signal_strength: Signal strength 0-100
            trace_id: Trace ID for audit
            
        Returns:
            Created event document
        """
        now = datetime.utcnow()
        
        event_doc = {
            "event_id": event_id,
            "session_id": session_id,
            "student_id": student_id,
            "device_id": device_id,
            "connectivity_state": connectivity_state,
            "disconnect_duration_seconds": disconnect_duration_seconds,
            "event_timestamp": now,  # Server timestamp (canonical)
            "network_type": network_type,
            "signal_strength": signal_strength,
            "trace_id": trace_id,
            "_immutable": True,
            "_created_at": now
        }
        
        await self.collection.insert_one(event_doc)
        logger.debug(
            f"Connectivity event logged: {event_id}",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "state": connectivity_state
            }
        )
        
        return event_doc
    
    async def get_last_heartbeat(
        self,
        session_id: str,
        device_id: str,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent heartbeat for a session+device.
        
        Args:
            session_id: Session ID
            device_id: Device ID
            trace_id: Trace ID
            
        Returns:
            Latest heartbeat document or None
        """
        latest = await self.collection.find_one(
            {"session_id": session_id, "device_id": device_id},
            sort=[("event_timestamp", -1)]
        )
        
        return latest
    
    async def count_disconnects(
        self,
        session_id: str,
        device_id: str,
        since: datetime,
        trace_id: str
    ) -> int:
        """Count disconnect events for abuse detection.
        
        Args:
            session_id: Session ID
            device_id: Device ID
            since: Count events since this time
            trace_id: Trace ID
            
        Returns:
            Count of disconnect events
        """
        count = await self.collection.count_documents({
            "session_id": session_id,
            "device_id": device_id,
            "event_timestamp": {"$gte": since},
            "connectivity_state": {"$in": ["short_disconnect", "medium_disconnect", "long_disconnect"]}
        })
        
        return count
