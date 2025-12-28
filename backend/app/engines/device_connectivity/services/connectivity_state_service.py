"""Connectivity State Service for determining device connectivity state.

PHASE SIX: Server-authoritative connectivity assessment.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional

from app.engines.device_connectivity.schemas.output import ConnectivityState
from app.engines.device_connectivity.repository.connectivity_repo import ConnectivityRepository

logger = logging.getLogger(__name__)


class ConnectivityStateService:
    """Service for calculating connectivity state based on heartbeat timing.
    
    CRITICAL RULES:
    - Server time is ALWAYS authoritative
    - Client timestamps are advisory only
    - Disconnect thresholds are server-configured
    """
    
    # Disconnect thresholds (seconds)
    SHORT_DISCONNECT_THRESHOLD = 30  # <30s
    MEDIUM_DISCONNECT_THRESHOLD = 120  # <2min
    # >2min = LONG_DISCONNECT
    
    def __init__(self):
        """Initialize connectivity state service."""
        self.repository = ConnectivityRepository()
    
    def calculate_disconnect_duration(
        self,
        last_heartbeat_time: Optional[datetime],
        current_server_time: datetime
    ) -> int:
        """Calculate disconnect duration in seconds.
        
        Args:
            last_heartbeat_time: Last heartbeat timestamp (server)
            current_server_time: Current server time
            
        Returns:
            Disconnect duration in seconds
        """
        if not last_heartbeat_time:
            return 0  # First heartbeat
        
        delta = current_server_time - last_heartbeat_time
        return int(delta.total_seconds())
    
    def determine_connectivity_state(
        self,
        disconnect_duration_seconds: int
    ) -> ConnectivityState:
        """Determine connectivity state based on disconnect duration.
        
        Args:
            disconnect_duration_seconds: Seconds since last heartbeat
            
        Returns:
            ConnectivityState enum value
        """
        if disconnect_duration_seconds == 0:
            return ConnectivityState.CONNECTED
        elif disconnect_duration_seconds < self.SHORT_DISCONNECT_THRESHOLD:
            return ConnectivityState.SHORT_DISCONNECT
        elif disconnect_duration_seconds < self.MEDIUM_DISCONNECT_THRESHOLD:
            return ConnectivityState.MEDIUM_DISCONNECT
        else:
            return ConnectivityState.LONG_DISCONNECT
    
    def should_pause_session(
        self,
        connectivity_state: ConnectivityState
    ) -> bool:
        """Determine if session should be paused server-side.
        
        Args:
            connectivity_state: Current connectivity state
            
        Returns:
            True if session should be paused
        """
        return connectivity_state == ConnectivityState.LONG_DISCONNECT
    
    def determine_client_behavior(
        self,
        connectivity_state: ConnectivityState,
        session_status: str
    ) -> Tuple[bool, bool, bool]:
        """Determine what the client should do.
        
        Args:
            connectivity_state: Current connectivity state
            session_status: Current session status (active/paused/closed)
            
        Returns:
            Tuple of (should_buffer, should_warn, should_pause)
        """
        # If session is already paused or closed, client should pause
        if session_status in ["paused", "closed"]:
            return False, True, True
        
        if connectivity_state == ConnectivityState.CONNECTED:
            return False, False, False  # Normal operation
        
        elif connectivity_state == ConnectivityState.SHORT_DISCONNECT:
            return True, False, False  # Buffer, no warning
        
        elif connectivity_state == ConnectivityState.MEDIUM_DISCONNECT:
            return True, True, False  # Buffer + warn
        
        else:  # LONG_DISCONNECT
            return False, True, True  # Stop buffering, warn, pause
    
    async def check_for_abuse(
        self,
        session_id: str,
        device_id: str,
        trace_id: str
    ) -> bool:
        """Check for repeated disconnect abuse pattern.
        
        Args:
            session_id: Session ID
            device_id: Device ID
            trace_id: Trace ID
            
        Returns:
            True if abuse pattern detected
        """
        # Count disconnects in last hour
        since = datetime.utcnow() - timedelta(hours=1)
        disconnect_count = await self.repository.count_disconnects(
            session_id=session_id,
            device_id=device_id,
            since=since,
            trace_id=trace_id
        )
        
        # Flag if >10 disconnects/hour
        ABUSE_THRESHOLD = 10
        
        if disconnect_count > ABUSE_THRESHOLD:
            logger.warning(
                f"Potential disconnect abuse detected: {disconnect_count} disconnects in 1 hour",
                extra={
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "device_id": device_id,
                    "disconnect_count": disconnect_count
                }
            )
            return True
        
        return False
