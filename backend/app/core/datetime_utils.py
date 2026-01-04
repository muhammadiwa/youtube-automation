"""Datetime utilities for consistent timezone handling.

All datetime operations should use these utilities to ensure:
1. All datetimes are timezone-aware (UTC)
2. Consistent comparison between datetimes
3. No more "offset-naive vs offset-aware" errors

Usage:
    from app.core.datetime_utils import utcnow, ensure_utc, to_utc_timestamp

    # Get current time
    now = utcnow()
    
    # Ensure datetime is UTC aware before comparison
    scheduled_at = ensure_utc(event.scheduled_start_at)
    if scheduled_at > now:
        ...
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def utcnow() -> datetime:
    """Get current UTC time with timezone info.
    
    Returns:
        datetime: Current time in UTC with tzinfo set
        
    Example:
        >>> now = utcnow()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is UTC aware.
    
    - If None, returns None
    - If naive (no tzinfo), assumes it's UTC and adds tzinfo
    - If aware, converts to UTC
    
    Args:
        dt: Datetime to convert (can be naive or aware)
        
    Returns:
        datetime: UTC aware datetime or None
        
    Example:
        >>> naive = datetime(2026, 1, 4, 12, 0, 0)
        >>> aware = ensure_utc(naive)
        >>> aware.tzinfo
        datetime.timezone.utc
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume it's already UTC
        return dt.replace(tzinfo=timezone.utc)
    # Aware datetime - convert to UTC
    return dt.astimezone(timezone.utc)


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to naive UTC (for legacy code compatibility).
    
    This is useful when you need to work with code that expects naive datetimes.
    The returned datetime will be in UTC but without tzinfo.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        datetime: Naive datetime in UTC or None
    """
    if dt is None:
        return None
    utc_dt = ensure_utc(dt)
    return utc_dt.replace(tzinfo=None) if utc_dt else None


def is_in_future(dt: Optional[datetime]) -> bool:
    """Check if datetime is in the future.
    
    Args:
        dt: Datetime to check
        
    Returns:
        bool: True if datetime is in the future
    """
    if dt is None:
        return False
    return ensure_utc(dt) > utcnow()


def is_in_past(dt: Optional[datetime]) -> bool:
    """Check if datetime is in the past.
    
    Args:
        dt: Datetime to check
        
    Returns:
        bool: True if datetime is in the past
    """
    if dt is None:
        return False
    return ensure_utc(dt) < utcnow()


def seconds_until(dt: Optional[datetime]) -> int:
    """Get seconds until a datetime.
    
    Args:
        dt: Target datetime
        
    Returns:
        int: Seconds until datetime (negative if in past)
    """
    if dt is None:
        return 0
    diff = ensure_utc(dt) - utcnow()
    return int(diff.total_seconds())


def seconds_since(dt: Optional[datetime]) -> int:
    """Get seconds since a datetime.
    
    Args:
        dt: Target datetime
        
    Returns:
        int: Seconds since datetime (negative if in future)
    """
    if dt is None:
        return 0
    diff = utcnow() - ensure_utc(dt)
    return int(diff.total_seconds())


def hours_since(dt: Optional[datetime]) -> float:
    """Get hours since a datetime.
    
    Args:
        dt: Target datetime
        
    Returns:
        float: Hours since datetime
    """
    return seconds_since(dt) / 3600


def add_hours(dt: Optional[datetime], hours: int) -> Optional[datetime]:
    """Add hours to a datetime.
    
    Args:
        dt: Base datetime
        hours: Hours to add
        
    Returns:
        datetime: New datetime with hours added
    """
    if dt is None:
        return None
    return ensure_utc(dt) + timedelta(hours=hours)


def add_days(dt: Optional[datetime], days: int) -> Optional[datetime]:
    """Add days to a datetime.
    
    Args:
        dt: Base datetime
        days: Days to add
        
    Returns:
        datetime: New datetime with days added
    """
    if dt is None:
        return None
    return ensure_utc(dt) + timedelta(days=days)


def start_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get start of day (00:00:00) in UTC.
    
    Args:
        dt: Date to get start of (defaults to today)
        
    Returns:
        datetime: Start of day in UTC
    """
    if dt is None:
        dt = utcnow()
    else:
        dt = ensure_utc(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get end of day (23:59:59) in UTC.
    
    Args:
        dt: Date to get end of (defaults to today)
        
    Returns:
        datetime: End of day in UTC
    """
    if dt is None:
        dt = utcnow()
    else:
        dt = ensure_utc(dt)
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def to_iso_utc(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string with 'Z' suffix for UTC.
    
    This is the preferred format for sending datetimes to frontend.
    The 'Z' suffix ensures JavaScript interprets it as UTC.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        str: ISO string with 'Z' suffix (e.g., "2026-01-04T12:30:00Z") or None
        
    Example:
        >>> dt = datetime(2026, 1, 4, 12, 30, 0)
        >>> to_iso_utc(dt)
        "2026-01-04T12:30:00Z"
    """
    if dt is None:
        return None
    utc_dt = ensure_utc(dt)
    if utc_dt is None:
        return None
    # Format as ISO without microseconds, with Z suffix
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
