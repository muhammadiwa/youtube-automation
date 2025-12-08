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
    StreamHealthLog,
)
from app.modules.stream.repository import (
    LiveEventRepository,
    StreamSessionRepository,
    StreamHealthLogRepository,
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



# ============================================
# Stream Health Monitoring (Requirements: 8.1, 8.2, 8.3, 8.4, 8.5)
# ============================================

class HealthThresholds:
    """Health metric thresholds for alerting.
    
    Requirements: 8.2
    """
    # Bitrate thresholds (in bps)
    MIN_BITRATE_WARNING = 1000000  # 1 Mbps
    MIN_BITRATE_CRITICAL = 500000  # 500 Kbps
    
    # Frame rate thresholds
    MIN_FRAME_RATE_WARNING = 25.0
    MIN_FRAME_RATE_CRITICAL = 15.0
    
    # Dropped frames thresholds (per collection interval)
    MAX_DROPPED_FRAMES_WARNING = 10
    MAX_DROPPED_FRAMES_CRITICAL = 50
    
    # Latency thresholds (in ms)
    MAX_LATENCY_WARNING = 2000
    MAX_LATENCY_CRITICAL = 5000


class StreamHealthMonitor:
    """Monitors stream health and triggers alerts.
    
    Requirements: 8.1, 8.2
    """
    
    # Collection interval in seconds (Requirements: 8.1)
    COLLECTION_INTERVAL_SECONDS = 10
    
    # Alert timing requirement (Requirements: 8.2)
    MAX_ALERT_DELAY_SECONDS = 30
    
    def __init__(self, thresholds: Optional[HealthThresholds] = None):
        """Initialize with thresholds.
        
        Args:
            thresholds: Health thresholds (defaults to standard thresholds)
        """
        self.thresholds = thresholds or HealthThresholds()
    
    def evaluate_health(
        self,
        bitrate: int,
        frame_rate: Optional[float],
        dropped_frames_delta: int,
        latency_ms: Optional[int],
    ) -> tuple[str, Optional[str], Optional[str]]:
        """Evaluate stream health based on metrics.
        
        Args:
            bitrate: Current bitrate in bps
            frame_rate: Current frame rate
            dropped_frames_delta: Dropped frames since last check
            latency_ms: Latency in milliseconds
            
        Returns:
            tuple: (connection_status, alert_type, alert_message)
        """
        alerts = []
        status = ConnectionStatus.EXCELLENT.value
        
        # Check bitrate
        if bitrate < self.thresholds.MIN_BITRATE_CRITICAL:
            alerts.append(("critical", f"Bitrate critically low: {bitrate} bps"))
            status = ConnectionStatus.POOR.value
        elif bitrate < self.thresholds.MIN_BITRATE_WARNING:
            alerts.append(("warning", f"Bitrate low: {bitrate} bps"))
            if status == ConnectionStatus.EXCELLENT.value:
                status = ConnectionStatus.FAIR.value
        
        # Check frame rate
        if frame_rate is not None:
            if frame_rate < self.thresholds.MIN_FRAME_RATE_CRITICAL:
                alerts.append(("critical", f"Frame rate critically low: {frame_rate} fps"))
                status = ConnectionStatus.POOR.value
            elif frame_rate < self.thresholds.MIN_FRAME_RATE_WARNING:
                alerts.append(("warning", f"Frame rate low: {frame_rate} fps"))
                if status in [ConnectionStatus.EXCELLENT.value, ConnectionStatus.GOOD.value]:
                    status = ConnectionStatus.FAIR.value
        
        # Check dropped frames
        if dropped_frames_delta >= self.thresholds.MAX_DROPPED_FRAMES_CRITICAL:
            alerts.append(("critical", f"High frame drops: {dropped_frames_delta} frames"))
            status = ConnectionStatus.POOR.value
        elif dropped_frames_delta >= self.thresholds.MAX_DROPPED_FRAMES_WARNING:
            alerts.append(("warning", f"Frame drops detected: {dropped_frames_delta} frames"))
            if status in [ConnectionStatus.EXCELLENT.value, ConnectionStatus.GOOD.value]:
                status = ConnectionStatus.FAIR.value
        
        # Check latency
        if latency_ms is not None:
            if latency_ms >= self.thresholds.MAX_LATENCY_CRITICAL:
                alerts.append(("critical", f"Latency critically high: {latency_ms} ms"))
                status = ConnectionStatus.POOR.value
            elif latency_ms >= self.thresholds.MAX_LATENCY_WARNING:
                alerts.append(("warning", f"Latency high: {latency_ms} ms"))
                if status in [ConnectionStatus.EXCELLENT.value, ConnectionStatus.GOOD.value]:
                    status = ConnectionStatus.FAIR.value
        
        # Determine overall status if no issues
        if not alerts and status == ConnectionStatus.EXCELLENT.value:
            if bitrate > self.thresholds.MIN_BITRATE_WARNING * 2:
                status = ConnectionStatus.EXCELLENT.value
            else:
                status = ConnectionStatus.GOOD.value
        
        # Build alert response
        if alerts:
            # Prioritize critical alerts
            critical_alerts = [a for a in alerts if a[0] == "critical"]
            if critical_alerts:
                return status, "critical", "; ".join(a[1] for a in critical_alerts)
            else:
                return status, "warning", "; ".join(a[1] for a in alerts)
        
        return status, None, None
    
    def should_trigger_alert(
        self,
        alert_type: Optional[str],
        last_alert_time: Optional[datetime],
    ) -> bool:
        """Check if alert should be triggered based on timing.
        
        Requirements: 8.2 - Trigger alerts within 30 seconds.
        
        Args:
            alert_type: Type of alert (critical, warning, None)
            last_alert_time: Time of last alert
            
        Returns:
            bool: True if alert should be triggered
        """
        if alert_type is None:
            return False
        
        if last_alert_time is None:
            return True
        
        # Always trigger critical alerts
        if alert_type == "critical":
            return True
        
        # For warnings, don't spam - wait at least 30 seconds
        elapsed = (datetime.utcnow() - last_alert_time).total_seconds()
        return elapsed >= self.MAX_ALERT_DELAY_SECONDS


class StreamReconnectionManager:
    """Manages stream reconnection with exponential backoff.
    
    Requirements: 8.3, 8.4
    """
    
    MAX_RECONNECTION_ATTEMPTS = 5
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize with retry configuration.
        
        Args:
            retry_config: Retry configuration
        """
        self.retry_config = retry_config or STREAM_RECONNECT_CONFIG
    
    def should_attempt_reconnection(self, attempts: int) -> bool:
        """Check if reconnection should be attempted.
        
        Args:
            attempts: Number of reconnection attempts made
            
        Returns:
            bool: True if reconnection should be attempted
        """
        return attempts < self.MAX_RECONNECTION_ATTEMPTS
    
    def calculate_reconnection_delay(self, attempt: int) -> float:
        """Calculate delay before next reconnection attempt.
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            float: Delay in seconds
        """
        return self.retry_config.calculate_delay(attempt)
    
    def get_total_attempts_made(self, attempts: int) -> int:
        """Get total attempts made.
        
        Args:
            attempts: Current attempt count
            
        Returns:
            int: Total attempts
        """
        return attempts


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def collect_stream_health_metrics(self: BaseTaskWithRetry, session_id: str) -> dict:
    """Collect health metrics for an active stream session.
    
    Requirements: 8.1 - Collect metrics every 10 seconds.
    
    Args:
        session_id: UUID of the stream session
        
    Returns:
        dict: Collected metrics and status
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _collect_health_metrics_async(session_id)
    )


async def _collect_health_metrics_async(session_id: str) -> dict:
    """Async implementation of health metric collection."""
    monitor = StreamHealthMonitor()
    
    async with async_session_maker() as session:
        session_repo = StreamSessionRepository(session)
        health_repo = StreamHealthLogRepository(session)
        
        stream_session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not stream_session:
            return {"success": False, "error": "Session not found"}
        
        if not stream_session.is_active():
            return {"success": False, "error": "Session is not active"}
        
        # In a real implementation, these would come from the streaming agent
        # For now, we simulate metric collection
        collected_at = datetime.utcnow()
        
        # Get previous log to calculate deltas
        previous_log = await health_repo.get_latest_by_session(uuid.UUID(session_id))
        previous_dropped = previous_log.dropped_frames if previous_log else 0
        
        # Simulated metrics (in production, these come from FFmpeg/RTMP agent)
        bitrate = stream_session.average_bitrate or 3000000  # 3 Mbps default
        frame_rate = 30.0
        dropped_frames = stream_session.dropped_frames
        dropped_frames_delta = max(0, dropped_frames - previous_dropped)
        latency_ms = 500  # Simulated
        viewer_count = stream_session.peak_viewers
        chat_rate = 0.0
        
        # Evaluate health
        connection_status, alert_type, alert_message = monitor.evaluate_health(
            bitrate=bitrate,
            frame_rate=frame_rate,
            dropped_frames_delta=dropped_frames_delta,
            latency_ms=latency_ms,
        )
        
        # Check if alert should be triggered
        last_alert_time = None
        if previous_log and previous_log.is_alert_triggered:
            last_alert_time = previous_log.collected_at
        
        should_alert = monitor.should_trigger_alert(alert_type, last_alert_time)
        
        # Create health log entry
        health_log = await health_repo.create(
            session_id=uuid.UUID(session_id),
            bitrate=bitrate,
            frame_rate=frame_rate,
            dropped_frames=dropped_frames,
            dropped_frames_delta=dropped_frames_delta,
            connection_status=connection_status,
            latency_ms=latency_ms,
            viewer_count=viewer_count,
            chat_rate=chat_rate,
            is_alert_triggered=should_alert,
            alert_type=alert_type if should_alert else None,
            alert_message=alert_message if should_alert else None,
            collected_at=collected_at,
        )
        
        # Update session connection status
        await session_repo.update_metrics(
            stream_session,
            connection_status=ConnectionStatus(connection_status),
        )
        
        await session.commit()
        
        result = {
            "success": True,
            "session_id": session_id,
            "health_log_id": str(health_log.id),
            "collected_at": collected_at.isoformat(),
            "connection_status": connection_status,
            "bitrate": bitrate,
            "frame_rate": frame_rate,
            "dropped_frames_delta": dropped_frames_delta,
            "alert_triggered": should_alert,
        }
        
        if should_alert:
            result["alert_type"] = alert_type
            result["alert_message"] = alert_message
            # Trigger alert notification task
            trigger_health_alert.delay(
                session_id=session_id,
                alert_type=alert_type,
                alert_message=alert_message,
            )
        
        return result


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def trigger_health_alert(
    self: BaseTaskWithRetry,
    session_id: str,
    alert_type: str,
    alert_message: str,
) -> dict:
    """Trigger health alert notification.
    
    Requirements: 8.2 - Trigger alerts within 30 seconds.
    
    Args:
        session_id: UUID of the stream session
        alert_type: Type of alert (critical, warning)
        alert_message: Alert message
        
    Returns:
        dict: Alert result
    """
    # In production, this would send notifications via the notification service
    return {
        "success": True,
        "session_id": session_id,
        "alert_type": alert_type,
        "alert_message": alert_message,
        "triggered_at": datetime.utcnow().isoformat(),
    }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def check_active_streams_health(self: BaseTaskWithRetry) -> dict:
    """Periodic task to collect health metrics for all active streams.
    
    Should run every 10 seconds per Requirements: 8.1.
    
    Returns:
        dict: Summary of health checks
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_check_active_streams_health_async())


async def _check_active_streams_health_async() -> dict:
    """Async implementation of active streams health check."""
    checked = []
    errors = []
    
    async with async_session_maker() as session:
        # Get all active stream sessions
        result = await session.execute(
            select(StreamSession)
            .where(StreamSession.started_at.isnot(None))
            .where(StreamSession.ended_at.is_(None))
        )
        active_sessions = result.scalars().all()
        
        for stream_session in active_sessions:
            try:
                # Schedule health collection for each active session
                collect_stream_health_metrics.delay(str(stream_session.id))
                checked.append(str(stream_session.id))
            except Exception as e:
                errors.append({"session_id": str(stream_session.id), "error": str(e)})
    
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "active_sessions": len(checked),
        "checked_sessions": checked,
        "errors": errors,
    }


@celery_app.task(bind=True, base=BaseTaskWithRetry, retry_config_name="stream_reconnect")
def attempt_stream_reconnection(
    self: BaseTaskWithRetry,
    event_id: str,
    session_id: str,
    attempt: int,
) -> dict:
    """Attempt to reconnect a disconnected stream.
    
    Requirements: 8.3 - Reconnection with exponential backoff up to 5 times.
    
    Args:
        event_id: UUID of the live event
        session_id: UUID of the stream session
        attempt: Current attempt number
        
    Returns:
        dict: Reconnection result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _attempt_reconnection_async(event_id, session_id, attempt)
    )


async def _attempt_reconnection_async(event_id: str, session_id: str, attempt: int) -> dict:
    """Async implementation of stream reconnection attempt."""
    reconnection_manager = StreamReconnectionManager()
    
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        stream_session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not stream_session:
            return {"success": False, "error": "Session not found"}
        
        # Check if we should attempt reconnection
        if not reconnection_manager.should_attempt_reconnection(attempt):
            # Max attempts reached, trigger failover
            trigger_stream_failover.delay(event_id, session_id)
            return {
                "success": False,
                "action": "failover_triggered",
                "reason": "max_reconnection_attempts_reached",
                "total_attempts": attempt,
            }
        
        # Update session status
        stream_session.connection_status = ConnectionStatus.FAIR.value
        await session_repo.increment_reconnection_attempts(stream_session)
        
        # In production, this would trigger the agent to reconnect
        # Simulate reconnection attempt
        reconnection_success = True  # Simulated
        
        if reconnection_success:
            stream_session.connection_status = ConnectionStatus.GOOD.value
            await session.commit()
            return {
                "success": True,
                "event_id": event_id,
                "session_id": session_id,
                "attempt": attempt,
                "status": "reconnected",
            }
        else:
            # Schedule next attempt with exponential backoff
            delay = reconnection_manager.calculate_reconnection_delay(attempt + 1)
            await session.commit()
            
            attempt_stream_reconnection.apply_async(
                args=[event_id, session_id, attempt + 1],
                countdown=delay,
            )
            
            return {
                "success": False,
                "action": "retry_scheduled",
                "attempt": attempt,
                "next_attempt": attempt + 1,
                "delay_seconds": delay,
            }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def trigger_stream_failover(
    self: BaseTaskWithRetry,
    event_id: str,
    session_id: str,
) -> dict:
    """Trigger failover to backup stream or static video.
    
    Requirements: 8.4 - Execute failover when reconnection fails.
    
    Args:
        event_id: UUID of the live event
        session_id: UUID of the stream session
        
    Returns:
        dict: Failover result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _trigger_failover_async(event_id, session_id)
    )


async def _trigger_failover_async(event_id: str, session_id: str) -> dict:
    """Async implementation of stream failover."""
    async with async_session_maker() as session:
        event_repo = LiveEventRepository(session)
        session_repo = StreamSessionRepository(session)
        
        event = await event_repo.get_by_id(uuid.UUID(event_id))
        if not event:
            return {"success": False, "error": "Event not found"}
        
        stream_session = await session_repo.get_by_id(uuid.UUID(session_id))
        if not stream_session:
            return {"success": False, "error": "Session not found"}
        
        # End the current session
        await session_repo.end_session(
            stream_session,
            end_reason="failover_triggered",
            error="Max reconnection attempts reached",
        )
        
        # In production, this would:
        # 1. Switch to backup stream if configured
        # 2. Or play static video/image
        # 3. Or end the stream gracefully
        
        # For now, we mark the event as failed
        event.status = LiveEventStatus.FAILED.value
        event.last_error = "Stream failed after max reconnection attempts, failover executed"
        
        await session.commit()
        
        return {
            "success": True,
            "event_id": event_id,
            "session_id": session_id,
            "action": "failover_executed",
            "failover_type": "stream_ended",  # Could be "backup_stream" or "static_video"
        }


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def cleanup_old_health_logs(
    self: BaseTaskWithRetry,
    retention_days: int = 7,
) -> dict:
    """Clean up old health logs for data retention.
    
    Requirements: 8.5 - Historical data retention.
    
    Args:
        retention_days: Number of days to retain logs
        
    Returns:
        dict: Cleanup result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _cleanup_old_health_logs_async(retention_days)
    )


async def _cleanup_old_health_logs_async(retention_days: int) -> dict:
    """Async implementation of health log cleanup."""
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    total_deleted = 0
    
    async with async_session_maker() as session:
        health_repo = StreamHealthLogRepository(session)
        
        # Get all sessions with old logs
        result = await session.execute(
            select(StreamHealthLog.session_id)
            .where(StreamHealthLog.collected_at < cutoff_date)
            .distinct()
        )
        session_ids = [row[0] for row in result.all()]
        
        for session_id in session_ids:
            deleted = await health_repo.delete_old_logs(session_id, cutoff_date)
            total_deleted += deleted
        
        await session.commit()
    
    return {
        "success": True,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
        "sessions_processed": len(session_ids),
        "logs_deleted": total_deleted,
    }
