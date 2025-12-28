"""Timezone conversion utilities for ZimPrep.

Handles conversion between UTC (database storage) and local timezones (display).
All times stored in database are UTC. Conversion happens at API response time.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Default timezone for Zimbabwe
DEFAULT_TIMEZONE = "Africa/Harare"

# Common timezones for Southern Africa
SUPPORTED_TIMEZONES = {
    "Africa/Harare": "Central Africa Time (CAT)",
    "Africa/Johannesburg": "South Africa Standard Time (SAST)",
    "Africa/Lusaka": "Central Africa Time (CAT)",
    "Africa/Gaborone": "Central Africa Time (CAT)",
    "Africa/Maputo": "Central Africa Time (CAT)",
    "UTC": "Coordinated Universal Time (UTC)",
}


def convert_utc_to_local(
    utc_datetime: datetime,
    timezone_str: str = DEFAULT_TIMEZONE
) -> datetime:
    """Convert UTC datetime to local timezone.
    
    Args:
        utc_datetime: Datetime in UTC (timezone-aware or naive)
        timezone_str: IANA timezone string (e.g., 'Africa/Harare')
        
    Returns:
        Datetime in local timezone (timezone-aware)
        
    Example:
        >>> utc_time = datetime(2025, 5, 14, 7, 0, 0, tzinfo=timezone.utc)
        >>> local_time = convert_utc_to_local(utc_time, "Africa/Harare")
        >>> print(local_time)  # 2025-05-14 09:00:00+02:00 (CAT is UTC+2)
    """
    try:
        # Ensure UTC datetime is timezone-aware
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
        
        # Convert to target timezone
        local_tz = ZoneInfo(timezone_str)
        local_datetime = utc_datetime.astimezone(local_tz)
        
        return local_datetime
    
    except Exception as e:
        logger.error(
            f"Error converting timezone: {e}",
            extra={
                "utc_datetime": str(utc_datetime),
                "timezone": timezone_str,
                "error": str(e)
            }
        )
        # Fallback to UTC
        return utc_datetime


def format_exam_time(
    utc_datetime: datetime,
    timezone_str: str = DEFAULT_TIMEZONE,
    include_timezone_name: bool = True
) -> Dict[str, Any]:
    """Format exam time with both UTC and local timezone info.
    
    Args:
        utc_datetime: Exam scheduled time in UTC
        timezone_str: Candidate's local timezone
        include_timezone_name: Include human-readable timezone name
        
    Returns:
        Dictionary with UTC, local, timezone, and display formats
        
    Example:
        >>> utc_time = datetime(2025, 5, 14, 7, 0, 0, tzinfo=timezone.utc)
        >>> formatted = format_exam_time(utc_time, "Africa/Harare")
        >>> print(formatted)
        {
            "utc": "2025-05-14T07:00:00+00:00",
            "local": "2025-05-14T09:00:00+02:00",
            "timezone": "Africa/Harare",
            "timezone_name": "Central Africa Time (CAT)",
            "display": "May 14, 2025 at 9:00 AM CAT"
        }
    """
    try:
        # Convert to local time
        local_datetime = convert_utc_to_local(utc_datetime, timezone_str)
        
        # Get timezone abbreviation (e.g., "CAT")
        timezone_abbr = local_datetime.strftime("%Z")
        
        # Human-readable display format
        display_format = local_datetime.strftime("%B %d, %Y at %-I:%M %p")
        if timezone_abbr:
            display_format += f" {timezone_abbr}"
        
        result = {
            "utc": utc_datetime.isoformat(),
            "local": local_datetime.isoformat(),
            "timezone": timezone_str,
            "display": display_format,
        }
        
        # Add human-readable timezone name
        if include_timezone_name and timezone_str in SUPPORTED_TIMEZONES:
            result["timezone_name"] = SUPPORTED_TIMEZONES[timezone_str]
        
        return result
    
    except Exception as e:
        logger.error(
            f"Error formatting exam time: {e}",
            extra={
                "utc_datetime": str(utc_datetime),
                "timezone": timezone_str,
                "error": str(e)
            }
        )
        # Fallback to UTC only
        return {
            "utc": utc_datetime.isoformat(),
            "local": utc_datetime.isoformat(),
            "timezone": "UTC",
            "display": utc_datetime.strftime("%B %d, %Y at %-I:%M %p UTC"),
        }


def get_time_until_exam(
    exam_datetime: datetime,
    current_time: datetime | None = None
) -> Dict[str, Any]:
    """Calculate time remaining until exam.
    
    Args:
        exam_datetime: Scheduled exam time
        current_time: Current time (defaults to now)
        
    Returns:
        Dictionary with time remaining in various formats
        
    Example:
        >>> exam_time = datetime.now() + timedelta(days=5, hours=3)
        >>> time_remaining = get_time_until_exam(exam_time)
        >>> print(time_remaining)
        {
            "days": 5,
            "hours": 3,
            "minutes": 0,
            "total_seconds": 453600,
            "display": "5 days, 3 hours",
            "urgency": "low"
        }
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Ensure both are timezone-aware
    if exam_datetime.tzinfo is None:
        exam_datetime = exam_datetime.replace(tzinfo=ZoneInfo("UTC"))
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=ZoneInfo("UTC"))
    
    # Calculate difference
    time_diff = exam_datetime - current_time
    total_seconds = int(time_diff.total_seconds())
    
    if total_seconds <= 0:
        return {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "total_seconds": 0,
            "display": "Exam has started or passed",
            "urgency": "passed"
        }
    
    # Calculate components
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    # Determine urgency level
    if total_seconds < 3600:  # Less than 1 hour
        urgency = "critical"
    elif total_seconds < 86400:  # Less than 1 day
        urgency = "high"
    elif total_seconds < 259200:  # Less than 3 days
        urgency = "medium"
    else:
        urgency = "low"
    
    # Format display
    if days > 0:
        display = f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
    elif hours > 0:
        display = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        display = f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "total_seconds": total_seconds,
        "display": display,
        "urgency": urgency
    }


def validate_timezone(timezone_str: str) -> bool:
    """Validate if timezone string is valid IANA timezone.
    
    Args:
        timezone_str: Timezone string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ZoneInfo(timezone_str)
        return True
    except Exception:
        return False
