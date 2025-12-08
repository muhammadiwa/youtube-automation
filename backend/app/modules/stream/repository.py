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
    StreamPlaylist,
    PlaylistItem,
    PlaylistLoopMode,
    PlaylistItemStatus,
    TransitionType,
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


class StreamPlaylistRepository:
    """Repository for StreamPlaylist CRUD operations.
    
    Requirements: 7.1, 7.2, 7.5
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        live_event_id: uuid.UUID,
        name: str = "Default Playlist",
        loop_mode: str = PlaylistLoopMode.NONE.value,
        loop_count: Optional[int] = None,
        default_transition: str = TransitionType.CUT.value,
        default_transition_duration_ms: int = 500,
    ) -> StreamPlaylist:
        """Create a new stream playlist.

        Args:
            live_event_id: Live event UUID
            name: Playlist name
            loop_mode: Loop mode (none, count, infinite)
            loop_count: Number of loops for COUNT mode
            default_transition: Default transition type
            default_transition_duration_ms: Default transition duration

        Returns:
            StreamPlaylist: Created playlist instance
        """
        playlist = StreamPlaylist(
            live_event_id=live_event_id,
            name=name,
            loop_mode=loop_mode,
            loop_count=loop_count,
            default_transition=default_transition,
            default_transition_duration_ms=default_transition_duration_ms,
        )
        self.session.add(playlist)
        await self.session.flush()
        return playlist

    async def get_by_id(
        self, playlist_id: uuid.UUID, include_items: bool = False
    ) -> Optional[StreamPlaylist]:
        """Get playlist by ID.

        Args:
            playlist_id: Playlist UUID
            include_items: Whether to load playlist items

        Returns:
            Optional[StreamPlaylist]: Playlist if found
        """
        query = select(StreamPlaylist).where(StreamPlaylist.id == playlist_id)
        if include_items:
            query = query.options(selectinload(StreamPlaylist.items))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_event_id(
        self, live_event_id: uuid.UUID, include_items: bool = False
    ) -> Optional[StreamPlaylist]:
        """Get playlist for a live event.

        Args:
            live_event_id: Live event UUID
            include_items: Whether to load playlist items

        Returns:
            Optional[StreamPlaylist]: Playlist if found
        """
        query = select(StreamPlaylist).where(
            StreamPlaylist.live_event_id == live_event_id
        )
        if include_items:
            query = query.options(selectinload(StreamPlaylist.items))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, playlist: StreamPlaylist, **kwargs) -> StreamPlaylist:
        """Update playlist attributes.

        Args:
            playlist: StreamPlaylist instance
            **kwargs: Attributes to update

        Returns:
            StreamPlaylist: Updated playlist instance
        """
        for key, value in kwargs.items():
            if hasattr(playlist, key):
                setattr(playlist, key, value)
        await self.session.flush()
        return playlist

    async def set_active(self, playlist: StreamPlaylist, is_active: bool) -> StreamPlaylist:
        """Set playlist active state.

        Args:
            playlist: StreamPlaylist instance
            is_active: Whether playlist is active

        Returns:
            StreamPlaylist: Updated playlist instance
        """
        playlist.is_active = is_active
        await self.session.flush()
        return playlist

    async def advance_to_next_item(self, playlist: StreamPlaylist) -> Optional[int]:
        """Advance playlist to next item.
        
        Handles loop logic per Requirements 7.2.

        Args:
            playlist: StreamPlaylist instance

        Returns:
            Optional[int]: New item index or None if playlist complete
        """
        next_index = playlist.get_next_item_index()
        
        if next_index is None:
            # Playlist complete
            playlist.is_active = False
            await self.session.flush()
            return None
        
        if next_index == 0 and playlist.current_item_index > 0:
            # Looping back to start
            playlist.current_loop += 1
        
        playlist.current_item_index = next_index
        await self.session.flush()
        return next_index

    async def reset_playlist(self, playlist: StreamPlaylist) -> StreamPlaylist:
        """Reset playlist to initial state.

        Args:
            playlist: StreamPlaylist instance

        Returns:
            StreamPlaylist: Reset playlist instance
        """
        playlist.current_item_index = 0
        playlist.current_loop = 0
        playlist.is_active = False
        await self.session.flush()
        return playlist

    async def increment_stats(
        self,
        playlist: StreamPlaylist,
        plays: int = 0,
        skips: int = 0,
        failures: int = 0,
    ) -> StreamPlaylist:
        """Increment playlist statistics.

        Args:
            playlist: StreamPlaylist instance
            plays: Number of plays to add
            skips: Number of skips to add
            failures: Number of failures to add

        Returns:
            StreamPlaylist: Updated playlist instance
        """
        playlist.total_plays += plays
        playlist.total_skips += skips
        playlist.total_failures += failures
        await self.session.flush()
        return playlist

    async def delete(self, playlist: StreamPlaylist) -> None:
        """Delete a playlist.

        Args:
            playlist: StreamPlaylist instance to delete
        """
        await self.session.delete(playlist)
        await self.session.flush()


class PlaylistItemRepository:
    """Repository for PlaylistItem CRUD operations.
    
    Requirements: 7.1, 7.3, 7.4
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        playlist_id: uuid.UUID,
        video_title: str,
        position: int,
        video_id: Optional[uuid.UUID] = None,
        video_url: Optional[str] = None,
        video_duration_seconds: Optional[int] = None,
        transition_type: str = TransitionType.CUT.value,
        transition_duration_ms: int = 500,
        start_offset_seconds: int = 0,
        end_offset_seconds: Optional[int] = None,
    ) -> PlaylistItem:
        """Create a new playlist item.

        Args:
            playlist_id: Playlist UUID
            video_title: Video title
            position: Position in playlist
            video_id: Optional video UUID
            video_url: Optional video URL
            video_duration_seconds: Video duration
            transition_type: Transition type
            transition_duration_ms: Transition duration
            start_offset_seconds: Start offset
            end_offset_seconds: End offset

        Returns:
            PlaylistItem: Created item instance
        """
        item = PlaylistItem(
            playlist_id=playlist_id,
            video_title=video_title,
            position=position,
            video_id=video_id,
            video_url=video_url,
            video_duration_seconds=video_duration_seconds,
            transition_type=transition_type,
            transition_duration_ms=transition_duration_ms,
            start_offset_seconds=start_offset_seconds,
            end_offset_seconds=end_offset_seconds,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_id(self, item_id: uuid.UUID) -> Optional[PlaylistItem]:
        """Get playlist item by ID.

        Args:
            item_id: Item UUID

        Returns:
            Optional[PlaylistItem]: Item if found
        """
        result = await self.session.execute(
            select(PlaylistItem).where(PlaylistItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_playlist_id(
        self, playlist_id: uuid.UUID
    ) -> list[PlaylistItem]:
        """Get all items for a playlist ordered by position.

        Args:
            playlist_id: Playlist UUID

        Returns:
            list[PlaylistItem]: List of items
        """
        result = await self.session.execute(
            select(PlaylistItem)
            .where(PlaylistItem.playlist_id == playlist_id)
            .order_by(PlaylistItem.position.asc())
        )
        return list(result.scalars().all())

    async def get_item_at_position(
        self, playlist_id: uuid.UUID, position: int
    ) -> Optional[PlaylistItem]:
        """Get item at specific position.

        Args:
            playlist_id: Playlist UUID
            position: Position index

        Returns:
            Optional[PlaylistItem]: Item if found
        """
        result = await self.session.execute(
            select(PlaylistItem)
            .where(PlaylistItem.playlist_id == playlist_id)
            .where(PlaylistItem.position == position)
        )
        return result.scalar_one_or_none()

    async def update(self, item: PlaylistItem, **kwargs) -> PlaylistItem:
        """Update playlist item attributes.

        Args:
            item: PlaylistItem instance
            **kwargs: Attributes to update

        Returns:
            PlaylistItem: Updated item instance
        """
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        await self.session.flush()
        return item

    async def update_position(self, item: PlaylistItem, new_position: int) -> PlaylistItem:
        """Update item position.

        Args:
            item: PlaylistItem instance
            new_position: New position

        Returns:
            PlaylistItem: Updated item instance
        """
        item.position = new_position
        await self.session.flush()
        return item

    async def mark_as_playing(self, item: PlaylistItem) -> PlaylistItem:
        """Mark item as currently playing.

        Args:
            item: PlaylistItem instance

        Returns:
            PlaylistItem: Updated item instance
        """
        item.mark_as_playing()
        await self.session.flush()
        return item

    async def mark_as_completed(self, item: PlaylistItem) -> PlaylistItem:
        """Mark item as completed.

        Args:
            item: PlaylistItem instance

        Returns:
            PlaylistItem: Updated item instance
        """
        item.mark_as_completed()
        await self.session.flush()
        return item

    async def mark_as_skipped(
        self, item: PlaylistItem, error: Optional[str] = None
    ) -> PlaylistItem:
        """Mark item as skipped (Requirements: 7.4).

        Args:
            item: PlaylistItem instance
            error: Optional error message

        Returns:
            PlaylistItem: Updated item instance
        """
        item.mark_as_skipped(error)
        await self.session.flush()
        return item

    async def mark_as_failed(self, item: PlaylistItem, error: str) -> PlaylistItem:
        """Mark item as failed.

        Args:
            item: PlaylistItem instance
            error: Error message

        Returns:
            PlaylistItem: Updated item instance
        """
        item.mark_as_failed(error)
        await self.session.flush()
        return item

    async def reset_all_items(self, playlist_id: uuid.UUID) -> int:
        """Reset all items in playlist to pending status.

        Args:
            playlist_id: Playlist UUID

        Returns:
            int: Number of items reset
        """
        items = await self.get_by_playlist_id(playlist_id)
        for item in items:
            item.reset_status()
        await self.session.flush()
        return len(items)

    async def reorder_items(
        self, playlist_id: uuid.UUID, item_ids: list[uuid.UUID]
    ) -> list[PlaylistItem]:
        """Reorder playlist items.
        
        Requirements: 7.5 - Allow playlist modification during stream.

        Args:
            playlist_id: Playlist UUID
            item_ids: List of item IDs in new order

        Returns:
            list[PlaylistItem]: Reordered items
        """
        items = await self.get_by_playlist_id(playlist_id)
        item_map = {item.id: item for item in items}
        
        reordered = []
        for position, item_id in enumerate(item_ids):
            if item_id in item_map:
                item = item_map[item_id]
                item.position = position
                reordered.append(item)
        
        await self.session.flush()
        return reordered

    async def delete(self, item: PlaylistItem) -> None:
        """Delete a playlist item.

        Args:
            item: PlaylistItem instance to delete
        """
        await self.session.delete(item)
        await self.session.flush()

    async def delete_by_playlist_id(self, playlist_id: uuid.UUID) -> int:
        """Delete all items in a playlist.

        Args:
            playlist_id: Playlist UUID

        Returns:
            int: Number of items deleted
        """
        items = await self.get_by_playlist_id(playlist_id)
        count = len(items)
        for item in items:
            await self.session.delete(item)
        await self.session.flush()
        return count

    async def count_by_playlist(self, playlist_id: uuid.UUID) -> int:
        """Count items in a playlist.

        Args:
            playlist_id: Playlist UUID

        Returns:
            int: Number of items
        """
        result = await self.session.execute(
            select(sql_func.count(PlaylistItem.id)).where(
                PlaylistItem.playlist_id == playlist_id
            )
        )
        return result.scalar_one() or 0
