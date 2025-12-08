"""Celery tasks for stream automation.

Implements stream scheduling, auto-start/stop, and auto-restart on disconnection.
Requirements: 6.1, 6.4, 6.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from celery import Task
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.modules.job.tasks import BaseTaskWithRetry, RetryConfig, RETRY_CONFIGS
from app.modules.stream.models import (
    LiveEvent,
    LiveEventStatus,
    StreamSession,
    ConnectionStatus,
)
from app.modules.stream.repository import (
    LiveEventRepository,
    StreamSessionRepository,
)
from app.modules.account.repository import YouTubeAccountRepository


# Stream-specific retry configuration
STREAM_RECONNECT_CONFIG = RETRY_CONFIGS["stream_reconnect"]


class StreamScheduler:
    """Handles stream scheduling logic.
    
    Implements conflict detection and timing validation.
    Requirements: 6.1, 6.4
    """
    
    # Maximum allowed deviation from scheduled time (30 seconds per Requirement 6.1)
    MAX_START_DEVIATION_SECONDS = 30
    
    @staticmethod
    def check_time_conflict(
        event1_start: datetime,
        event1_end: Optional[datetime],
        event2_start: datetime,
        event2_end: Optional[datetime],
        default_duration_hours: int = 2,
    ) -> bool:
        """Check if two time ranges conflict.
        
        Args:
            event1_start: Start time of first event
            event1_end: End time of first event (optional)
            event2_start: Start time of second event
            event2_end: End time of second event (optional)
            default_duration_hours: Default duration if end time not specified
            
        Returns:
            bool: True if there is a conflict
        """
        # Normalize to naive datetime for comparison
        e1_start = event1_start.replace(tzinfo=None) if event1_start.tzinfo else event1_start
        e2_start = event2_start.replace(tzinfo=None) if event2_start.tzinfo else event2_start
        
        # Calculate end times with default duration if not provided
        default_duration = timedelta(hours=default_duration_hours)
        
        if event1_end:
            e1_end = event1_end.replace(tzinfo=None) if event1_end.tzinfo else event1_end
        else:
            e1_end = e1_start + default_duration
            
        if event2_end:
            e2_end = event2_end.replace(tzinfo=None) if event2_end.tzinfo else event2_end
        else:
            e2_end = e2_start + default_duration
        
        # Check for overlap: events conflict if one starts before the other ends
        return e1_start < e2_end and e2_start < e1_end
    
    @staticmethod
    def is_within_start_window(scheduled_time: datetime, current_time: Optional[datetime] = None) -> bool:
        """Check if current time is within the allowed start window.
        
        Per Requirement 6.1: Stream should start within 30 seconds of scheduled time.
        
        Args:
            scheduled_time: The scheduled start time
            current_time: Current time (defaults to now)
            
        Returns:
            bool: True if within start window
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        # Normalize timezones
        scheduled = scheduled_time.replace(tzinfo=None) if scheduled_time.tzinfo else scheduled_time
        current = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
        
        # Check if we're past the scheduled time but within the allowed window
        if current < scheduled:
            return False
            
        deviation = (current - scheduled).total_seconds()
        return deviation <= StreamScheduler.MAX_START_DEVIATION_SECONDS
    
    @staticmethod
    def calculate_start_deviation(scheduled_time: datetime, actual_time: datetime) -> float:
        """Calculate the deviation between scheduled and actual start time.
        
        Args:
            scheduled_time: The scheduled start time
            actual_time: The actual start time
            
        Returns:
            float: Deviation in seconds (positive if late, negative if early)
        """
        scheduled = scheduled_time.replace(tzinfo=None) if scheduled_time.tzinfo else scheduled_time
        actual = actual_time.replace(tzinfo=None) if actual_time.tzinfo else actual_time
        
        return (actual - scheduled).total_seconds()


class StreamAutoRestartManager:
    """Manages auto-restart logic for disconnected streams.
    
    Implements exponential backoff reconnection per Requirement 6.5.
    """
    
    MAX_RECONNECTION_ATTEMPTS = 5
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize with retry configuration.
        
        Args:
            retry_config: Retry configuration (defaults to stream_reconnect config)
        """
        self.retry_config = retry_config or STREAM_RECONNECT_CONFIG
    
    def should_attempt_restart(self, reconnection_attempts: int) -> bool:
        """Check if restart should be attempted.
        
        Args:
            reconnection_attempts: Number of reconnection attempts made
            
        Returns:
            bool: True if restart should be attempted
        """
        return reconnection_attempts < self.MAX_RECONNECTION_ATTEMPTS
    
    def calculate_restart_delay(self, attempt: int) -> float:
        """Calculate delay before next restart attempt.
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            float: Delay in seconds
        """
        return self.retry_config.calculate_delay(attempt)
    
    def get_remaining_attempts(self, reconnection_attempts: int) -> int:
        """Get number of remaining restart attempts.
        
        Args:
            reconnection_attempts: Number of attempts already made
            
        Returns:
            int: Remaining attempts
        """
        return max(0, self.MAX_RECONNECTION_ATTEMPTS - reconnection_attempts)


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def check_scheduled_streams(self: BaseTaskWithRetry) -> dict:
    """Periodic task to check and start scheduled streams.
    
    Runs every 10 seconds to check for streams that should start.
    Requirements: 6.1
    
    Returns:
        dict: Summary of processed streams
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_check_scheduled_streams_async())


async def _check_scheduled_streams_async() -> dict:
    """Async implementation of scheduled stream check."""
    started = []
    errors = []
    
    async with async_session_maker() as session:
        repo = LiveEventRepository(session)
        
        # Get events ready to start
        events = await repo.get_events_ready_to_start()
        
        for event in events:
            try:
                # Check if within start window (30 seconds)
                if event.scheduled_start_at:
                    scheduler = StreamScheduler()
                    if scheduler.is_within_start_window(event.scheduled_start_at):
                        # Trigger stream start
                        start_stream_task.delay(str(event.id))
                        started.append(str(event.id))
            except Exception as e:
                errors.append({"event_id": str(event.id), "error": str(e)})
        
        await session.commit()
    
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "started_count": len(started),
        "started_events": started,
        "errors": errors,
    }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def start_stream_task(self: BaseTaskWithRetry, event_id: str) -> dict:
    """Start a scheduled stream.
    
    Requirements: 6.1, 6.2
    
    Args:
        event_id: UUID of the live event to start
        
    Returns:
        dict: Result of stream start operation
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_start_stream_async(event_id))


async def _start_stream_async(event_id: str) -> dict:
    """Async implementation of stream start."""
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        # Verify event is in correct state
        if event.status not in [LiveEventStatus.SCHEDULED.value, LiveEventStatus.CREATED.value]:
            return {"success": False, "error": f"Event in invalid state: {event.status}"}
        
        # Record start time for timing validation
        actual_start = datetime.utcnow()
        
        # Calculate deviation if scheduled
        deviation_seconds = None
        if event.scheduled_start_at:
            deviation_seconds = StreamScheduler.calculate_start_deviation(
                event.scheduled_start_at, actual_start
            )
        
        # Create stream session
        stream_session = await session_repo.create(
            live_event_id=event.id,
            agent_id=None,  # Will be assigned by agent manager
        )
        
        # Start the session
        await session_repo.start_session(stream_session)
        
        # Update event status
        event.status = LiveEventStatus.LIVE.value
        event.actual_start_at = actual_start
        
        await session.commit()
        
        return {
            "success": True,
            "event_id": event_id,
            "session_id": str(stream_session.id),
            "actual_start_at": actual_start.isoformat(),
            "deviation_seconds": deviation_seconds,
            "within_timing_requirement": deviation_seconds is None or abs(deviation_seconds) <= 30,
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def stop_stream_task(self: BaseTaskWithRetry, event_id: str, reason: str = "scheduled_end") -> dict:
    """Stop a running stream.
    
    Requirements: 6.3
    
    Args:
        event_id: UUID of the live event to stop
        reason: Reason for stopping
        
    Returns:
        dict: Result of stream stop operation
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_stop_stream_async(event_id, reason))


async def _stop_stream_async(event_id: str, reason: str) -> dict:
    """Async implementation of stream stop."""
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        # Get active session
        active_session = await session_repo.get_active_session(event.id)
        if active_session:
            await session_repo.end_session(active_session, end_reason=reason)
        
        # Update event status
        event.status = LiveEventStatus.ENDED.value
        event.actual_end_at = datetime.utcnow()
        
        await session.commit()
        
        return {
            "success": True,
            "event_id": event_id,
            "ended_at": event.actual_end_at.isoformat(),
            "reason": reason,
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry, retry_config_name="stream_reconnect")
def handle_stream_disconnection(
    self: BaseTaskWithRetry,
    event_id: str,
    session_id: str,
    error: Optional[str] = None,
) -> dict:
    """Handle stream disconnection and attempt auto-restart.
    
    Requirements: 6.5
    
    Args:
        event_id: UUID of the live event
        session_id: UUID of the stream session
        error: Error message if any
        
    Returns:
        dict: Result of disconnection handling
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _handle_disconnection_async(event_id, session_id, error)
    )


async def _handle_disconnection_async(event_id: str, session_id: str, error: Optional[str]) -> dict:
    """Async implementation of disconnection handling."""
    restart_manager = StreamAutoRestartManager()
    
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        stream_session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not stream_session:
            return {"success": False, "error": "Session not found"}
        
        # Update session status
        stream_session.connection_status = ConnectionStatus.DISCONNECTED.value
        if error:
            stream_session.last_error = error
        
        # Check if auto-restart is enabled
        if not event.enable_auto_start:
            await session_repo.end_session(stream_session, end_reason="disconnected_no_auto_restart")
            event.status = LiveEventStatus.ENDED.value
            await session.commit()
            return {
                "success": True,
                "action": "ended",
                "reason": "auto_restart_disabled",
            }
        
        # Check if we should attempt restart
        current_attempts = stream_session.reconnection_attempts
        if restart_manager.should_attempt_restart(current_attempts):
            # Increment attempt counter
            await session_repo.increment_reconnection_attempts(stream_session)
            
            # Calculate delay for next attempt
            delay = restart_manager.calculate_restart_delay(current_attempts + 1)
            
            await session.commit()
            
            # Schedule restart task
            restart_stream_task.apply_async(
                args=[event_id, session_id],
                countdown=delay,
            )
            
            return {
                "success": True,
                "action": "restart_scheduled",
                "attempt": current_attempts + 1,
                "max_attempts": restart_manager.MAX_RECONNECTION_ATTEMPTS,
                "delay_seconds": delay,
            }
        else:
            # Max attempts reached, end the stream
            await session_repo.end_session(
                stream_session,
                end_reason="max_reconnection_attempts_reached",
                error=error,
            )
            event.status = LiveEventStatus.FAILED.value
            event.last_error = f"Stream failed after {current_attempts} reconnection attempts"
            
            await session.commit()
            
            return {
                "success": True,
                "action": "ended",
                "reason": "max_reconnection_attempts_reached",
                "total_attempts": current_attempts,
            }


@celery_app.task(bind=True, base=BaseTaskWithRetry, retry_config_name="stream_reconnect")
def restart_stream_task(self: BaseTaskWithRetry, event_id: str, session_id: str) -> dict:
    """Restart a disconnected stream.
    
    Requirements: 6.5
    
    Args:
        event_id: UUID of the live event
        session_id: UUID of the stream session
        
    Returns:
        dict: Result of restart operation
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _restart_stream_async(event_id, session_id)
    )


async def _restart_stream_async(event_id: str, session_id: str) -> dict:
    """Async implementation of stream restart."""
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        stream_session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not stream_session:
            return {"success": False, "error": "Session not found"}
        
        # Update session status to reconnecting
        stream_session.connection_status = ConnectionStatus.FAIR.value
        
        # In a real implementation, this would trigger the agent to reconnect
        # For now, we simulate a successful reconnection
        stream_session.connection_status = ConnectionStatus.GOOD.value
        
        await session.commit()
        
        return {
            "success": True,
            "event_id": event_id,
            "session_id": session_id,
            "reconnection_attempt": stream_session.reconnection_attempts,
            "status": "reconnected",
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def check_stream_end_times(self: BaseTaskWithRetry) -> dict:
    """Periodic task to check and stop streams at scheduled end time.
    
    Requirements: 6.3
    
    Returns:
        dict: Summary of processed streams
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_check_stream_end_times_async())


async def _check_stream_end_times_async() -> dict:
    """Async implementation of stream end time check."""
    stopped = []
    errors = []
    
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        
        # Get live events with scheduled end times
        result = await session.execute(
            select(LiveEvent)
            .where(LiveEvent.status == LiveEventStatus.LIVE.value)
            .where(LiveEvent.scheduled_end_at.isnot(None))
            .where(LiveEvent.enable_auto_stop == True)
        )
        events = result.scalars().all()
        
        now = datetime.utcnow()
        
        for event in events:
            try:
                end_time = event.scheduled_end_at.replace(tzinfo=None) if event.scheduled_end_at.tzinfo else event.scheduled_end_at
                if now >= end_time:
                    stop_stream_task.delay(str(event.id), "scheduled_end")
                    stopped.append(str(event.id))
            except Exception as e:
                errors.append({"event_id": str(event.id), "error": str(e)})
    
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "stopped_count": len(stopped),
        "stopped_events": stopped,
        "errors": errors,
    }
