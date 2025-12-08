"""Stream repository for database operations.

Implements CRUD operations for LiveEvent and StreamSession with scheduling support.
Requirements: 5.1, 5.2, 5.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, or_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.stream.models import (
    LiveEvent,
    LiveEventStatus,
    LatencyMode,
    StreamSession,
    ConnectionStatus,
    RecurrencePattern,
    RecurrenceFrequency,
)


class LiveEventRepository:
    """Repository for LiveEvent CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        account_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        category_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        latency_mode: str = LatencyMode.NORMAL.value,
        enable_dvr: bool = True,
        privacy_status: str = "private",
        scheduled_start_at: Optional[datetime] = None,
        scheduled_end_at: Optional[datetime] = None,
        is_recurring: bool = False,
    ) -> LiveEvent:
        """Create a new live event.

        Args:
            account_id: YouTube account UUID
            title: Event title
            description: Event description
            thumbnail_url: Thumbnail URL
            category_id: YouTube category ID
            tags: List of tags
            latency_mode: Latency mode setting
            enable_dvr: Enable DVR recording
            privacy_status: Privacy status (public, unlisted, private)
            scheduled_start_at: Scheduled start datetime
            scheduled_end_at: Scheduled end datetime
            is_recurring: Whether this is a recurring event

        Returns:
            LiveEvent: Created live event instance
        """
        status = LiveEventStatus.CREATED.value
        if scheduled_start_at:
            status = LiveEventStatus.SCHEDULED.value

        event = LiveEvent(
            account_id=account_id,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            category_id=category_id,
            tags=tags,
            latency_mode=latency_mode,
            enable_dvr=enable_dvr,
            privacy_status=privacy_status,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            is_recurring=is_recurring,
            status=status,
        )

        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(
        self, event_id: uuid.UUID, include_sessions: bool = False
    ) -> Optional[LiveEvent]:
        """Get live event by ID.

        Args:
            event_id: Event UUID
            include_sessions: Whether to load stream sessions

        Returns:
            Optional[LiveEvent]: Event if found, None otherwise
        """
        query = select(LiveEvent).where(LiveEvent.id == event_id)
        if include_sessions:
            query = query.options(selectinload(LiveEvent.stream_sessions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_broadcast_id(self, broadcast_id: str) -> Optional[LiveEvent]:
        """Get live event by YouTube broadcast ID.

        Args:
            broadcast_id: YouTube broadcast ID

        Returns:
            Optional[LiveEvent]: Event if found, None otherwise
        """
        result = await self.session.execute(
            select(LiveEvent).where(LiveEvent.youtube_broadcast_id == broadcast_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        status: Optional[LiveEventStatus] = None,
        include_past: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LiveEvent]:
        """Get all live events for an account.

        Args:
            account_id: YouTube account UUID
            status: Optional status filter
            include_past: Include ended/cancelled events
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            list[LiveEvent]: List of live events
        """
        query = (
            select(LiveEvent)
            .where(LiveEvent.account_id == account_id)
            .order_by(LiveEvent.scheduled_start_at.desc().nullsfirst())
            .limit(limit)
            .offset(offset)
        )

        if status:
            query = query.where(LiveEvent.status == status.value)
        elif not include_past:
            query = query.where(
                LiveEvent.status.notin_([
                    LiveEventStatus.ENDED.value,
                    LiveEventStatus.CANCELLED.value,
                ])
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scheduled_events(
        self,
        account_id: Optional[uuid.UUID] = None,
        start_from: Optional[datetime] = None,
        start_until: Optional[datetime] = None,
    ) -> list[LiveEvent]:
        """Get scheduled events within a time range.

        Args:
            account_id: Optional account filter
            start_from: Start of time range
            start_until: End of time range

        Returns:
            list[LiveEvent]: List of scheduled events
        """
        query = select(LiveEvent).where(
            LiveEvent.status == LiveEventStatus.SCHEDULED.value
        )

        if account_id:
            query = query.where(LiveEvent.account_id == account_id)
        if start_from:
            query = query.where(LiveEvent.scheduled_start_at >= start_from)
        if start_until:
            query = query.where(LiveEvent.scheduled_start_at <= start_until)

        query = query.order_by(LiveEvent.scheduled_start_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_events_ready_to_start(self) -> list[LiveEvent]:
        """Get scheduled events that should start now.

        Returns:
            list[LiveEvent]: Events ready to start
        """
        now = datetime.utcnow()
        result = await self.session.execute(
            select(LiveEvent)
            .where(LiveEvent.status == LiveEventStatus.SCHEDULED.value)
            .where(LiveEvent.scheduled_start_at <= now)
        )
        return list(result.scalars().all())

    async def check_schedule_conflict(
        self,
        account_id: uuid.UUID,
        start_at: datetime,
        end_at: Optional[datetime] = None,
        exclude_event_id: Optional[uuid.UUID] = None,
    ) -> Optional[LiveEvent]:
        """Check for scheduling conflicts on the same account.

        Args:
            account_id: YouTube account UUID
            start_at: Proposed start time
            end_at: Proposed end time
            exclude_event_id: Event ID to exclude from check

        Returns:
            Optional[LiveEvent]: Conflicting event if found, None otherwise
        """
        # Default end time if not provided (2 hours)
        if end_at is None:
            end_at = start_at + timedelta(hours=2)

        query = (
            select(LiveEvent)
            .where(LiveEvent.account_id == account_id)
            .where(
                LiveEvent.status.in_([
                    LiveEventStatus.CREATED.value,
                    LiveEventStatus.SCHEDULED.value,
                    LiveEventStatus.LIVE.value,
                ])
            )
        )

        if exclude_event_id:
            query = query.where(LiveEvent.id != exclude_event_id)

        result = await self.session.execute(query)
        events = result.scalars().all()

        for event in events:
            if event.has_time_conflict(start_at, end_at):
                return event

        return None

    async def update(self, event: LiveEvent, **kwargs) -> LiveEvent:
        """Update live event attributes.

        Args:
            event: LiveEvent instance to update
            **kwargs: Attributes to update

        Returns:
            LiveEvent: Updated event instance
        """
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        await self.session.flush()
        return event

    async def set_youtube_ids(
        self,
        event: LiveEvent,
        broadcast_id: str,
        stream_id: str,
        rtmp_key: str,
        rtmp_url: Optional[str] = None,
    ) -> LiveEvent:
        """Set YouTube broadcast and stream IDs.

        Args:
            event: LiveEvent instance
            broadcast_id: YouTube broadcast ID
            stream_id: YouTube stream ID
            rtmp_key: RTMP stream key (will be encrypted)
            rtmp_url: RTMP URL

        Returns:
            LiveEvent: Updated event instance
        """
        event.youtube_broadcast_id = broadcast_id
        event.youtube_stream_id = stream_id
        event.rtmp_key = rtmp_key  # Will be encrypted by property setter
        event.rtmp_url = rtmp_url
        await self.session.flush()
        return event

    async def set_status(
        self,
        event: LiveEvent,
        status: LiveEventStatus,
        error: Optional[str] = None,
    ) -> LiveEvent:
        """Update event status.

        Args:
            event: LiveEvent instance
            status: New status
            error: Error message if failed

        Returns:
            LiveEvent: Updated event instance
        """
        event.status = status.value
        if error:
            event.last_error = error

        if status == LiveEventStatus.LIVE and event.actual_start_at is None:
            event.actual_start_at = datetime.utcnow()
        elif status in [LiveEventStatus.ENDED, LiveEventStatus.CANCELLED]:
            event.actual_end_at = datetime.utcnow()

        await self.session.flush()
        return event

    async def delete(self, event: LiveEvent) -> None:
        """Delete a live event.

        Args:
            event: LiveEvent instance to delete
        """
        await self.session.delete(event)
        await self.session.flush()

    async def count_by_account(
        self, account_id: uuid.UUID, status: Optional[LiveEventStatus] = None
    ) -> int:
        """Count live events for an account.

        Args:
            account_id: YouTube account UUID
            status: Optional status filter

        Returns:
            int: Number of events
        """
        query = select(sql_func.count(LiveEvent.id)).where(
            LiveEvent.account_id == account_id
        )
        if status:
            query = query.where(LiveEvent.status == status.value)
        result = await self.session.execute(query)
        return result.scalar_one() or 0


class StreamSessionRepository:
    """Repository for StreamSession CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        live_event_id: uuid.UUID,
        agent_id: Optional[uuid.UUID] = None,
    ) -> StreamSession:
        """Create a new stream session.

        Args:
            live_event_id: Live event UUID
            agent_id: Assigned agent UUID

        Returns:
            StreamSession: Created session instance
        """
        session = StreamSession(
            live_event_id=live_event_id,
            agent_id=agent_id,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[StreamSession]:
        """Get stream session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Optional[StreamSession]: Session if found, None otherwise
        """
        result = await self.session.execute(
            select(StreamSession).where(StreamSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_session(
        self, live_event_id: uuid.UUID
    ) -> Optional[StreamSession]:
        """Get active session for a live event.

        Args:
            live_event_id: Live event UUID

        Returns:
            Optional[StreamSession]: Active session if found, None otherwise
        """
        result = await self.session.execute(
            select(StreamSession)
            .where(StreamSession.live_event_id == live_event_id)
            .where(StreamSession.ended_at.is_(None))
            .order_by(StreamSession.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_sessions_by_event(
        self, live_event_id: uuid.UUID
    ) -> list[StreamSession]:
        """Get all sessions for a live event.

        Args:
            live_event_id: Live event UUID

        Returns:
            list[StreamSession]: List of sessions
        """
        result = await self.session.execute(
            select(StreamSession)
            .where(StreamSession.live_event_id == live_event_id)
            .order_by(StreamSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def start_session(self, session: StreamSession) -> StreamSession:
        """Mark session as started.

        Args:
            session: StreamSession instance

        Returns:
            StreamSession: Updated session instance
        """
        session.started_at = datetime.utcnow()
        session.connection_status = ConnectionStatus.GOOD.value
        await self.session.flush()
        return session

    async def end_session(
        self,
        session: StreamSession,
        end_reason: Optional[str] = None,
        error: Optional[str] = None,
    ) -> StreamSession:
        """Mark session as ended.

        Args:
            session: StreamSession instance
            end_reason: Reason for ending
            error: Error message if applicable

        Returns:
            StreamSession: Updated session instance
        """
        session.ended_at = datetime.utcnow()
        session.connection_status = ConnectionStatus.DISCONNECTED.value
        if end_reason:
            session.end_reason = end_reason
        if error:
            session.last_error = error
        await self.session.flush()
        return session

    async def update_metrics(
        self,
        session: StreamSession,
        peak_viewers: Optional[int] = None,
        total_chat_messages: Optional[int] = None,
        average_bitrate: Optional[int] = None,
        dropped_frames: Optional[int] = None,
        connection_status: Optional[ConnectionStatus] = None,
    ) -> StreamSession:
        """Update session metrics.

        Args:
            session: StreamSession instance
            peak_viewers: Peak viewer count
            total_chat_messages: Total chat messages
            average_bitrate: Average bitrate
            dropped_frames: Dropped frame count
            connection_status: Connection status

        Returns:
            StreamSession: Updated session instance
        """
        if peak_viewers is not None and peak_viewers > session.peak_viewers:
            session.peak_viewers = peak_viewers
        if total_chat_messages is not None:
            session.total_chat_messages = total_chat_messages
        if average_bitrate is not None:
            session.average_bitrate = average_bitrate
        if dropped_frames is not None:
            session.dropped_frames = dropped_frames
        if connection_status is not None:
            session.connection_status = connection_status.value
        await self.session.flush()
        return session

    async def increment_reconnection_attempts(
        self, session: StreamSession
    ) -> StreamSession:
        """Increment reconnection attempt counter.

        Args:
            session: StreamSession instance

        Returns:
            StreamSession: Updated session instance
        """
        session.reconnection_attempts += 1
        await self.session.flush()
        return session


class RecurrencePatternRepository:
    """Repository for RecurrencePattern CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        live_event_id: uuid.UUID,
        frequency: str = RecurrenceFrequency.WEEKLY.value,
        interval: int = 1,
        days_of_week: Optional[list[int]] = None,
        day_of_month: Optional[int] = None,
        duration_minutes: int = 60,
        end_date: Optional[datetime] = None,
        occurrence_count: Optional[int] = None,
    ) -> RecurrencePattern:
        """Create a new recurrence pattern.

        Args:
            live_event_id: Live event UUID
            frequency: Recurrence frequency
            interval: Interval between occurrences
            days_of_week: Days of week for weekly recurrence
            day_of_month: Day of month for monthly recurrence
            duration_minutes: Duration of each occurrence
            end_date: End date for recurrence
            occurrence_count: Maximum number of occurrences

        Returns:
            RecurrencePattern: Created pattern instance
        """
        pattern = RecurrencePattern(
            live_event_id=live_event_id,
            frequency=frequency,
            interval=interval,
            days_of_week=days_of_week,
            day_of_month=day_of_month,
            duration_minutes=duration_minutes,
            end_date=end_date,
            occurrence_count=occurrence_count,
        )
        self.session.add(pattern)
        await self.session.flush()
        return pattern

    async def get_by_event_id(
        self, live_event_id: uuid.UUID
    ) -> Optional[RecurrencePattern]:
        """Get recurrence pattern for a live event.

        Args:
            live_event_id: Live event UUID

        Returns:
            Optional[RecurrencePattern]: Pattern if found, None otherwise
        """
        result = await self.session.execute(
            select(RecurrencePattern).where(
                RecurrencePattern.live_event_id == live_event_id
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self, pattern: RecurrencePattern, **kwargs
    ) -> RecurrencePattern:
        """Update recurrence pattern attributes.

        Args:
            pattern: RecurrencePattern instance to update
            **kwargs: Attributes to update

        Returns:
            RecurrencePattern: Updated pattern instance
        """
        for key, value in kwargs.items():
            if hasattr(pattern, key):
                setattr(pattern, key, value)
        await self.session.flush()
        return pattern

    async def increment_generated_count(
        self, pattern: RecurrencePattern
    ) -> RecurrencePattern:
        """Increment generated occurrence count.

        Args:
            pattern: RecurrencePattern instance

        Returns:
            RecurrencePattern: Updated pattern instance
        """
        pattern.generated_count += 1
        pattern.last_generated_at = datetime.utcnow()
        await self.session.flush()
        return pattern

    async def delete(self, pattern: RecurrencePattern) -> None:
        """Delete a recurrence pattern.

        Args:
            pattern: RecurrencePattern instance to delete
        """
        await self.session.delete(pattern)
        await self.session.flush()
