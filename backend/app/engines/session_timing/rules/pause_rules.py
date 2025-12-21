"""Pause rules and policies for Session & Timing Engine.

Defines constraints on pause behavior to prevent abuse.
"""

from typing import List, Tuple, Optional
from datetime import datetime

from app.engines.session_timing.errors import (
    PauseCountExceededError,
    PauseDurationExceededError,
    InsufficientTimeRemainingError,
)


class PausePolicy:
    """Configurable pause constraints.
    
    These limits prevent abuse while allowing legitimate breaks.
    """
    
    MAX_PAUSE_COUNT = 3
    """Maximum number of pauses allowed per session."""
    
    MAX_SINGLE_PAUSE_MINUTES = 5
    """Maximum duration of a single pause in minutes."""
    
    MAX_TOTAL_PAUSE_MINUTES = 10
    """Maximum cumulative pause duration in minutes."""
    
    MIN_TIME_REMAINING_TO_PAUSE = 60
    """Minimum seconds remaining to allow pause (prevents last-second abuse)."""


class PauseRules:
    """Pause validation and enforcement logic."""
    
    @staticmethod
    def validate_pause_request(
        current_pause_count: int,
        total_pause_duration_seconds: int,
        remaining_seconds: int,
        trace_id: str
    ) -> None:
        """Validate that pause request is allowed.
        
        Raises specific exception if pause is not allowed.
        
        Args:
            current_pause_count: Number of pauses so far
            total_pause_duration_seconds: Total pause time so far
            remaining_seconds: Time remaining in session
            trace_id: Trace ID for error context
            
        Raises:
            PauseCountExceededError: Too many pauses
            PauseDurationExceededError: Total pause time exceeded
            InsufficientTimeRemainingError: Too little time remaining
        """
        # Check pause count limit
        if current_pause_count >= PausePolicy.MAX_PAUSE_COUNT:
            raise PauseCountExceededError(
                message=f"Maximum pause count ({PausePolicy.MAX_PAUSE_COUNT}) exceeded",
                trace_id=trace_id,
                metadata={
                    "current_pause_count": current_pause_count,
                    "max_allowed": PausePolicy.MAX_PAUSE_COUNT
                }
            )
        
        # Check total pause duration limit
        max_total_pause_seconds = PausePolicy.MAX_TOTAL_PAUSE_MINUTES * 60
        if total_pause_duration_seconds >= max_total_pause_seconds:
            raise PauseDurationExceededError(
                message=f"Maximum total pause duration ({PausePolicy.MAX_TOTAL_PAUSE_MINUTES} minutes) exceeded",
                trace_id=trace_id,
                metadata={
                    "total_pause_duration_seconds": total_pause_duration_seconds,
                    "max_allowed_seconds": max_total_pause_seconds
                }
            )
        
        # Check minimum time remaining
        if remaining_seconds < PausePolicy.MIN_TIME_REMAINING_TO_PAUSE:
            raise InsufficientTimeRemainingError(
                message=f"Insufficient time remaining to pause (minimum {PausePolicy.MIN_TIME_REMAINING_TO_PAUSE} seconds required)",
                trace_id=trace_id,
                metadata={
                    "remaining_seconds": remaining_seconds,
                    "min_required": PausePolicy.MIN_TIME_REMAINING_TO_PAUSE
                }
            )
    
    @staticmethod
    def validate_pause_duration(
        paused_at: datetime,
        current_time: datetime,
        trace_id: str
    ) -> None:
        """Validate that current pause duration hasn't exceeded limit.
        
        Called during RESUME to check if single pause was too long.
        
        Args:
            paused_at: When pause started
            current_time: Current server time
            trace_id: Trace ID for error context
            
        Raises:
            PauseDurationExceededError: Single pause too long
        """
        pause_duration_seconds = int((current_time - paused_at).total_seconds())
        max_single_pause_seconds = PausePolicy.MAX_SINGLE_PAUSE_MINUTES * 60
        
        if pause_duration_seconds > max_single_pause_seconds:
            raise PauseDurationExceededError(
                message=f"Single pause duration ({pause_duration_seconds}s) exceeded limit ({PausePolicy.MAX_SINGLE_PAUSE_MINUTES} minutes)",
                trace_id=trace_id,
                metadata={
                    "pause_duration_seconds": pause_duration_seconds,
                    "max_allowed_seconds": max_single_pause_seconds,
                    "paused_at": paused_at.isoformat(),
                    "current_time": current_time.isoformat()
                }
            )
    
    @staticmethod
    def get_current_pause_period(
        pause_periods: List[Tuple[datetime, Optional[datetime]]]
    ) -> Optional[Tuple[datetime, Optional[datetime]]]:
        """Get the currently active pause period if exists.
        
        Args:
            pause_periods: List of (paused_at, resumed_at) tuples
            
        Returns:
            Current pause period or None
        """
        if not pause_periods:
            return None
        
        last_period = pause_periods[-1]
        paused_at, resumed_at = last_period
        
        # If resumed_at is None, it's the current pause
        if resumed_at is None:
            return last_period
        
        return None
    
    @staticmethod
    def is_currently_paused(
        pause_periods: List[Tuple[datetime, Optional[datetime]]]
    ) -> bool:
        """Check if session is currently in paused state.
        
        Args:
            pause_periods: List of (paused_at, resumed_at) tuples
            
        Returns:
            True if currently paused, False otherwise
        """
        return PauseRules.get_current_pause_period(pause_periods) is not None
