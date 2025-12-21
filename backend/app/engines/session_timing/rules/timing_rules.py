"""Timing rules for Session & Timing Engine.

Server-authoritative time calculations and state transition logic.
"""

from datetime import datetime
from typing import List, Tuple, Optional

from app.engines.session_timing.schemas import SessionStatus, SessionAction


class TimingRules:
    """Server-authoritative timing calculations.
    
    All time calculations use server timestamps exclusively.
    Client timestamps are never trusted.
    """
    
    # State transition matrix: {current_status: {allowed_actions}}
    ALLOWED_TRANSITIONS = {
        SessionStatus.CREATED: {
            SessionAction.START_SESSION,
            SessionAction.HEARTBEAT,
        },
        SessionStatus.RUNNING: {
            SessionAction.PAUSE_SESSION,
            SessionAction.END_SESSION,
            SessionAction.HEARTBEAT,
        },
        SessionStatus.PAUSED: {
            SessionAction.RESUME_SESSION,
            SessionAction.END_SESSION,
            SessionAction.HEARTBEAT,
        },
        SessionStatus.EXPIRED: {
            SessionAction.END_SESSION,  # Allow cleanup
            SessionAction.HEARTBEAT,
        },
        SessionStatus.ENDED: {
            SessionAction.HEARTBEAT,  # Read-only
        },
    }
    
    @staticmethod
    def is_transition_allowed(
        current_status: SessionStatus,
        action: SessionAction
    ) -> bool:
        """Validate if state transition is allowed.
        
        Args:
            current_status: Current session status
            action: Requested action
            
        Returns:
            True if transition is allowed, False otherwise
        """
        allowed_actions = TimingRules.ALLOWED_TRANSITIONS.get(current_status, set())
        return action in allowed_actions
    
    @staticmethod
    def calculate_elapsed_time(
        started_at: datetime,
        current_time: datetime,
        pause_periods: List[Tuple[datetime, Optional[datetime]]]
    ) -> int:
        """Calculate elapsed time excluding pauses.
        
        Formula: elapsed = (current_time - started_at) - total_pause_duration
        
        Args:
            started_at: When session started
            current_time: Current server time
            pause_periods: List of (paused_at, resumed_at) tuples
            
        Returns:
            Elapsed seconds (excluding pauses)
        """
        if started_at is None:
            return 0
        
        # Total wall clock time
        total_seconds = int((current_time - started_at).total_seconds())
        
        # Calculate total pause duration
        total_pause_seconds = TimingRules.calculate_pause_duration(
            pause_periods=pause_periods,
            current_time=current_time
        )
        
        # Elapsed = total - pauses
        elapsed = max(0, total_seconds - total_pause_seconds)
        return elapsed
    
    @staticmethod
    def calculate_pause_duration(
        pause_periods: List[Tuple[datetime, Optional[datetime]]],
        current_time: datetime
    ) -> int:
        """Calculate total pause duration.
        
        If currently paused (last period has no resume time),
        count up to current_time.
        
        Args:
            pause_periods: List of (paused_at, resumed_at) tuples
            current_time: Current server time
            
        Returns:
            Total pause duration in seconds
        """
        total_pause = 0
        
        for paused_at, resumed_at in pause_periods:
            if resumed_at is not None:
                # Completed pause period
                pause_duration = int((resumed_at - paused_at).total_seconds())
            else:
                # Currently paused - count up to current time
                pause_duration = int((current_time - paused_at).total_seconds())
            
            total_pause += pause_duration
        
        return total_pause
    
    @staticmethod
    def calculate_remaining_time(
        time_limit_seconds: int,
        elapsed_seconds: int
    ) -> int:
        """Calculate remaining time.
        
        Formula: remaining = max(0, time_limit - elapsed)
        
        Args:
            time_limit_seconds: Total allowed time
            elapsed_seconds: Time already elapsed
            
        Returns:
            Remaining seconds (0 if expired)
        """
        return max(0, time_limit_seconds - elapsed_seconds)
    
    @staticmethod
    def has_expired(
        elapsed_seconds: int,
        time_limit_seconds: int
    ) -> bool:
        """Check if session has exceeded time limit.
        
        Args:
            elapsed_seconds: Time elapsed
            time_limit_seconds: Time limit
            
        Returns:
            True if expired, False otherwise
        """
        return elapsed_seconds >= time_limit_seconds
    
    @staticmethod
    def determine_status(
        current_status: SessionStatus,
        elapsed_seconds: int,
        time_limit_seconds: int,
        is_paused: bool
    ) -> SessionStatus:
        """Determine authoritative session status.
        
        Automatically transitions to EXPIRED if time limit exceeded.
        
        Args:
            current_status: Current stored status
            elapsed_seconds: Time elapsed
            time_limit_seconds: Time limit
            is_paused: Whether currently paused
            
        Returns:
            Authoritative session status
        """
        # If already ended, stay ended
        if current_status == SessionStatus.ENDED:
            return SessionStatus.ENDED
        
        # Check for expiry
        if TimingRules.has_expired(elapsed_seconds, time_limit_seconds):
            return SessionStatus.EXPIRED
        
        # Otherwise return current status
        return current_status
