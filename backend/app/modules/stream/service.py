"""Stream service for live event management operations.

Implements live event creation, scheduling, and YouTube API integration.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import YouTubeAccount
from app.modules.account.repository import YouTubeAccountRepository
from app.modules.stream.models import (
    LiveEvent,
    LiveEventStatus,
    LatencyMode,
    StreamSession,
    RecurrencePattern,
    RecurrenceFrequency,
    StreamPlaylist,
    PlaylistItem,
    PlaylistLoopMode,
    PlaylistItemStatus,
    TransitionType,
)
from app.modules.stream.repository import (
    LiveEventRepository,
    StreamSessionRepository,
    RecurrencePatternRepository,
    StreamPlaylistRepository,
    PlaylistItemRepository,
)
from app.modules.stream.schemas import (
    CreateLiveEventRequest,
    ScheduleLiveEventRequest,
    UpdateLiveEventRequest,
    CreateRecurringEventRequest,
    RecurrencePatternRequest,
    LiveEventResponse,
    ScheduleConflictError,
    CreatePlaylistRequest,
    UpdatePlaylistRequest,
    PlaylistItemCreate,
    PlaylistItemUpdate,
    PlaylistStreamStatus,
    PlaylistLoopResult,
)
from app.modules.stream.youtube_api import YouTubeLiveStreamingClient, YouTubeAPIError


class StreamServiceError(Exception):
    """Base exception for stream service errors."""
    pass


class AccountNotFoundError(StreamServiceError):
    """Exception raised when account is not found."""
    pass


class LiveEventNotFoundError(StreamServiceError):
    """Exception raised when live event is not found."""
    pass


class ScheduleConflictException(StreamServiceError):
    """Exception raised when schedule conflict is detected."""

    def __init__(self, message: str, conflicting_event: LiveEvent):
        self.message = message
        self.conflicting_event = conflicting_event
        super().__init__(self.message)


class StreamService:
    """Service for live event management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize stream service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.event_repository = LiveEventRepository(session)
        self.session_repository = StreamSessionRepository(session)
        self.recurrence_repository = RecurrencePatternRepository(session)
        self.account_repository = YouTubeAccountRepository(session)
        self.playlist_repository = StreamPlaylistRepository(session)
        self.playlist_item_repository = PlaylistItemRepository(session)

    async def create_live_event(
        self,
        request: CreateLiveEventRequest,
        create_on_youtube: bool = True,
    ) -> LiveEvent:
        """Create a new live event.

        Creates a live event in the database and optionally on YouTube.

        Args:
            request: Live event creation request
            create_on_youtube: Whether to create broadcast on YouTube

        Returns:
            LiveEvent: Created live event

        Raises:
            AccountNotFoundError: If account not found
            ScheduleConflictException: If schedule conflict exists
            YouTubeAPIError: If YouTube API call fails
        """
        # Verify account exists
        account = await self.account_repository.get_by_id(request.account_id)
        if not account:
            raise AccountNotFoundError(f"Account {request.account_id} not found")

        # Check for schedule conflicts if scheduled
        if request.scheduled_start_at:
            conflict = await self.event_repository.check_schedule_conflict(
                account_id=request.account_id,
                start_at=request.scheduled_start_at,
                end_at=request.scheduled_end_at,
            )
            if conflict:
                raise ScheduleConflictException(
                    f"Schedule conflict with event '{conflict.title}'",
                    conflicting_event=conflict,
                )

        # Create event in database
        event = await self.event_repository.create(
            account_id=request.account_id,
            title=request.title,
            description=request.description,
            thumbnail_url=request.thumbnail_url,
            category_id=request.category_id,
            tags=request.tags,
            latency_mode=request.latency_mode.value,
            enable_dvr=request.enable_dvr,
            privacy_status=request.privacy_status,
            scheduled_start_at=request.scheduled_start_at,
            scheduled_end_at=request.scheduled_end_at,
        )

        # Update additional settings
        event.enable_auto_start = request.enable_auto_start
        event.enable_auto_stop = request.enable_auto_stop
        event.made_for_kids = request.made_for_kids

        # Create on YouTube if requested
        if create_on_youtube:
            try:
                await self._create_youtube_broadcast(event, account)
            except YouTubeAPIError as e:
                # Mark event as failed but keep it
                await self.event_repository.set_status(
                    event, LiveEventStatus.FAILED, error=str(e)
                )
                raise

        await self.session.commit()
        return event

    async def schedule_live_event(
        self,
        request: ScheduleLiveEventRequest,
    ) -> LiveEvent:
        """Schedule a live event for future broadcast.

        Args:
            request: Schedule live event request

        Returns:
            LiveEvent: Scheduled live event

        Raises:
            AccountNotFoundError: If account not found
            ScheduleConflictException: If schedule conflict exists
        """
        # Verify account exists
        account = await self.account_repository.get_by_id(request.account_id)
        if not account:
            raise AccountNotFoundError(f"Account {request.account_id} not found")

        # Check for schedule conflicts
        conflict = await self.event_repository.check_schedule_conflict(
            account_id=request.account_id,
            start_at=request.scheduled_start_at,
            end_at=request.scheduled_end_at,
        )
        if conflict:
            raise ScheduleConflictException(
                f"Schedule conflict with event '{conflict.title}'",
                conflicting_event=conflict,
            )

        # Create scheduled event
        event = await self.event_repository.create(
            account_id=request.account_id,
            title=request.title,
            description=request.description,
            thumbnail_url=request.thumbnail_url,
            category_id=request.category_id,
            tags=request.tags,
            latency_mode=request.latency_mode.value,
            enable_dvr=request.enable_dvr,
            privacy_status=request.privacy_status,
            scheduled_start_at=request.scheduled_start_at,
            scheduled_end_at=request.scheduled_end_at,
        )

        # Create on YouTube
        try:
            await self._create_youtube_broadcast(event, account)
        except YouTubeAPIError as e:
            await self.event_repository.set_status(
                event, LiveEventStatus.FAILED, error=str(e)
            )
            raise

        await self.session.commit()
        return event

    async def create_recurring_event(
        self,
        request: CreateRecurringEventRequest,
        generate_count: int = 4,
    ) -> tuple[LiveEvent, list[LiveEvent]]:
        """Create a recurring live event with future instances.

        Args:
            request: Recurring event creation request
            generate_count: Number of future instances to generate

        Returns:
            tuple: (parent_event, list of generated child events)

        Raises:
            AccountNotFoundError: If account not found
            ScheduleConflictException: If schedule conflict exists
        """
        # Verify account exists
        account = await self.account_repository.get_by_id(request.account_id)
        if not account:
            raise AccountNotFoundError(f"Account {request.account_id} not found")

        # Create parent event (template)
        parent_event = await self.event_repository.create(
            account_id=request.account_id,
            title=request.title,
            description=request.description,
            thumbnail_url=request.thumbnail_url,
            category_id=request.category_id,
            tags=request.tags,
            latency_mode=request.latency_mode.value,
            enable_dvr=request.enable_dvr,
            privacy_status=request.privacy_status,
            scheduled_start_at=request.first_occurrence_at,
            is_recurring=True,
        )

        # Create recurrence pattern
        recurrence = request.recurrence
        pattern = await self.recurrence_repository.create(
            live_event_id=parent_event.id,
            frequency=recurrence.frequency.value,
            interval=recurrence.interval,
            days_of_week=recurrence.days_of_week,
            day_of_month=recurrence.day_of_month,
            duration_minutes=recurrence.duration_minutes,
            end_date=recurrence.end_date,
            occurrence_count=recurrence.occurrence_count,
        )

        # Generate future instances
        child_events = await self._generate_recurring_instances(
            parent_event=parent_event,
            pattern=pattern,
            account=account,
            count=generate_count,
        )

        await self.session.commit()
        return parent_event, child_events

    async def get_live_event(
        self,
        event_id: uuid.UUID,
        include_sessions: bool = False,
    ) -> Optional[LiveEvent]:
        """Get live event by ID.

        Args:
            event_id: Event UUID
            include_sessions: Whether to load stream sessions

        Returns:
            Optional[LiveEvent]: Event if found
        """
        return await self.event_repository.get_by_id(event_id, include_sessions)

    async def get_account_events(
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
        return await self.event_repository.get_by_account_id(
            account_id=account_id,
            status=status,
            include_past=include_past,
            limit=limit,
            offset=offset,
        )

    async def update_live_event(
        self,
        event_id: uuid.UUID,
        request: UpdateLiveEventRequest,
        update_on_youtube: bool = True,
    ) -> LiveEvent:
        """Update a live event.

        Args:
            event_id: Event UUID
            request: Update request
            update_on_youtube: Whether to update on YouTube

        Returns:
            LiveEvent: Updated event

        Raises:
            LiveEventNotFoundError: If event not found
            ScheduleConflictException: If schedule conflict exists
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {event_id} not found")

        # Check for schedule conflicts if changing schedule
        if request.scheduled_start_at:
            conflict = await self.event_repository.check_schedule_conflict(
                account_id=event.account_id,
                start_at=request.scheduled_start_at,
                end_at=request.scheduled_end_at,
                exclude_event_id=event_id,
            )
            if conflict:
                raise ScheduleConflictException(
                    f"Schedule conflict with event '{conflict.title}'",
                    conflicting_event=conflict,
                )

        # Update local event
        update_data = request.model_dump(exclude_unset=True)
        if "latency_mode" in update_data and update_data["latency_mode"]:
            update_data["latency_mode"] = update_data["latency_mode"].value

        event = await self.event_repository.update(event, **update_data)

        # Update on YouTube if requested and broadcast exists
        if update_on_youtube and event.youtube_broadcast_id:
            account = await self.account_repository.get_by_id(event.account_id)
            if account:
                try:
                    client = YouTubeLiveStreamingClient(account.access_token)
                    await client.update_broadcast(
                        broadcast_id=event.youtube_broadcast_id,
                        title=request.title,
                        description=request.description,
                        scheduled_start_time=request.scheduled_start_at,
                        privacy_status=request.privacy_status,
                    )
                except YouTubeAPIError:
                    # Log error but don't fail the update
                    pass

        await self.session.commit()
        return event

    async def delete_live_event(
        self,
        event_id: uuid.UUID,
        delete_on_youtube: bool = True,
    ) -> None:
        """Delete a live event.

        Args:
            event_id: Event UUID
            delete_on_youtube: Whether to delete on YouTube

        Raises:
            LiveEventNotFoundError: If event not found
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {event_id} not found")

        # Delete on YouTube if requested
        if delete_on_youtube and event.youtube_broadcast_id:
            account = await self.account_repository.get_by_id(event.account_id)
            if account:
                try:
                    client = YouTubeLiveStreamingClient(account.access_token)
                    await client.delete_broadcast(event.youtube_broadcast_id)
                except YouTubeAPIError:
                    # Log error but continue with local deletion
                    pass

        await self.event_repository.delete(event)
        await self.session.commit()

    async def generate_recurring_instances(
        self,
        parent_event_id: uuid.UUID,
        count: int = 4,
    ) -> list[LiveEvent]:
        """Generate future instances for a recurring event.

        Args:
            parent_event_id: Parent event UUID
            count: Number of instances to generate

        Returns:
            list[LiveEvent]: Generated child events

        Raises:
            LiveEventNotFoundError: If parent event not found
        """
        parent_event = await self.event_repository.get_by_id(parent_event_id)
        if not parent_event:
            raise LiveEventNotFoundError(f"Event {parent_event_id} not found")

        if not parent_event.is_recurring:
            raise StreamServiceError("Event is not a recurring event")

        pattern = await self.recurrence_repository.get_by_event_id(parent_event_id)
        if not pattern:
            raise StreamServiceError("Recurrence pattern not found")

        account = await self.account_repository.get_by_id(parent_event.account_id)
        if not account:
            raise AccountNotFoundError(f"Account {parent_event.account_id} not found")

        child_events = await self._generate_recurring_instances(
            parent_event=parent_event,
            pattern=pattern,
            account=account,
            count=count,
        )

        await self.session.commit()
        return child_events

    async def _create_youtube_broadcast(
        self,
        event: LiveEvent,
        account: YouTubeAccount,
    ) -> None:
        """Create YouTube broadcast and stream for an event.

        Args:
            event: LiveEvent instance
            account: YouTubeAccount instance

        Raises:
            YouTubeAPIError: If API call fails
        """
        client = YouTubeLiveStreamingClient(account.access_token)

        # Create broadcast
        broadcast = await client.create_broadcast(
            title=event.title,
            description=event.description,
            scheduled_start_time=event.scheduled_start_at,
            privacy_status=event.privacy_status,
            latency_mode=event.latency_mode,
            enable_dvr=event.enable_dvr,
            enable_embed=event.enable_embed,
            record_from_start=event.record_from_start,
            made_for_kids=event.made_for_kids,
        )

        broadcast_id = broadcast["id"]

        # Create stream
        stream = await client.create_stream(
            title=f"{event.title} - Stream",
            resolution="1080p",
            frame_rate="30fps",
        )

        stream_id = stream["id"]

        # Bind broadcast to stream
        await client.bind_broadcast_to_stream(broadcast_id, stream_id)

        # Extract RTMP info
        rtmp_url, rtmp_key = client.extract_rtmp_info(stream)

        # Update event with YouTube IDs and RTMP info
        await self.event_repository.set_youtube_ids(
            event=event,
            broadcast_id=broadcast_id,
            stream_id=stream_id,
            rtmp_key=rtmp_key,
            rtmp_url=rtmp_url,
        )

    async def _generate_recurring_instances(
        self,
        parent_event: LiveEvent,
        pattern: RecurrencePattern,
        account: YouTubeAccount,
        count: int,
    ) -> list[LiveEvent]:
        """Generate recurring event instances.

        Args:
            parent_event: Parent event template
            pattern: Recurrence pattern
            account: YouTube account
            count: Number of instances to generate

        Returns:
            list[LiveEvent]: Generated child events
        """
        child_events = []
        current_date = pattern.next_occurrence_at or parent_event.scheduled_start_at

        if current_date is None:
            current_date = datetime.utcnow()

        for _ in range(count):
            if not pattern.should_generate_more():
                break

            # Calculate next occurrence
            next_date = self._calculate_next_occurrence(current_date, pattern)
            if next_date is None:
                break

            # Check for conflicts
            conflict = await self.event_repository.check_schedule_conflict(
                account_id=parent_event.account_id,
                start_at=next_date,
                end_at=next_date + timedelta(minutes=pattern.duration_minutes),
            )

            if not conflict:
                # Create child event
                child_event = await self.event_repository.create(
                    account_id=parent_event.account_id,
                    title=parent_event.title,
                    description=parent_event.description,
                    thumbnail_url=parent_event.thumbnail_url,
                    category_id=parent_event.category_id,
                    tags=parent_event.tags,
                    latency_mode=parent_event.latency_mode,
                    enable_dvr=parent_event.enable_dvr,
                    privacy_status=parent_event.privacy_status,
                    scheduled_start_at=next_date,
                    scheduled_end_at=next_date + timedelta(minutes=pattern.duration_minutes),
                )

                # Set parent reference
                child_event.parent_event_id = parent_event.id

                # Create on YouTube
                try:
                    await self._create_youtube_broadcast(child_event, account)
                except YouTubeAPIError:
                    # Mark as failed but continue
                    await self.event_repository.set_status(
                        child_event, LiveEventStatus.FAILED
                    )

                child_events.append(child_event)

                # Update pattern
                await self.recurrence_repository.increment_generated_count(pattern)

            current_date = next_date

        # Update next occurrence
        next_occurrence = self._calculate_next_occurrence(current_date, pattern)
        if next_occurrence:
            pattern.next_occurrence_at = next_occurrence
            await self.session.flush()

        return child_events

    def _calculate_next_occurrence(
        self,
        current_date: datetime,
        pattern: RecurrencePattern,
    ) -> Optional[datetime]:
        """Calculate the next occurrence date based on pattern.

        Args:
            current_date: Current date to calculate from
            pattern: Recurrence pattern

        Returns:
            Optional[datetime]: Next occurrence date or None if no more
        """
        if pattern.end_date and current_date >= pattern.end_date:
            return None

        if pattern.occurrence_count and pattern.generated_count >= pattern.occurrence_count:
            return None

        frequency = pattern.frequency
        interval = pattern.interval

        if frequency == RecurrenceFrequency.DAILY.value:
            return current_date + timedelta(days=interval)

        elif frequency == RecurrenceFrequency.WEEKLY.value:
            if pattern.days_of_week:
                # Find next day of week
                current_dow = current_date.weekday()
                days_of_week = sorted(pattern.days_of_week)

                for dow in days_of_week:
                    if dow > current_dow:
                        return current_date + timedelta(days=dow - current_dow)

                # Wrap to next week
                first_dow = days_of_week[0]
                days_until = 7 - current_dow + first_dow + (interval - 1) * 7
                return current_date + timedelta(days=days_until)
            else:
                return current_date + timedelta(weeks=interval)

        elif frequency == RecurrenceFrequency.MONTHLY.value:
            # Add months
            month = current_date.month + interval
            year = current_date.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1

            day = pattern.day_of_month or current_date.day
            # Handle month overflow
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            day = min(day, max_day)

            return current_date.replace(year=year, month=month, day=day)

        return None

    async def start_stream(
        self,
        event_id: uuid.UUID,
        agent_id: Optional[uuid.UUID] = None,
    ) -> StreamSession:
        """Start a live stream.

        Creates a stream session and updates event status to LIVE.
        Requirements: 6.1, 6.2

        Args:
            event_id: Live event UUID
            agent_id: Optional agent UUID to assign

        Returns:
            StreamSession: Created stream session

        Raises:
            LiveEventNotFoundError: If event not found
            ScheduleConflictException: If another stream is active on same account
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {event_id} not found")

        # Check for active streams on same account (conflict detection)
        active_events = await self.event_repository.get_by_account_id(
            account_id=event.account_id,
            status=LiveEventStatus.LIVE,
        )
        if active_events:
            raise ScheduleConflictException(
                f"Account already has an active stream: {active_events[0].title}",
                conflicting_event=active_events[0],
            )

        # Create stream session
        session = await self.session_repository.create(
            live_event_id=event.id,
            agent_id=agent_id,
        )

        # Start the session
        await self.session_repository.start_session(session)

        # Update event status
        await self.event_repository.set_status(event, LiveEventStatus.LIVE)

        await self.session.commit()
        return session

    async def stop_stream(
        self,
        event_id: uuid.UUID,
        reason: str = "manual_stop",
    ) -> None:
        """Stop a live stream.

        Ends the active stream session and updates event status.
        Requirements: 6.3

        Args:
            event_id: Live event UUID
            reason: Reason for stopping

        Raises:
            LiveEventNotFoundError: If event not found
        """
        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {event_id} not found")

        # Get active session
        active_session = await self.session_repository.get_active_session(event.id)
        if active_session:
            await self.session_repository.end_session(active_session, end_reason=reason)

        # Update event status
        await self.event_repository.set_status(event, LiveEventStatus.ENDED)

        await self.session.commit()

    async def handle_disconnection(
        self,
        event_id: uuid.UUID,
        session_id: uuid.UUID,
        error: Optional[str] = None,
    ) -> dict:
        """Handle stream disconnection.

        Implements auto-restart logic per Requirement 6.5.

        Args:
            event_id: Live event UUID
            session_id: Stream session UUID
            error: Error message if any

        Returns:
            dict: Action taken (restart_scheduled, ended, etc.)

        Raises:
            LiveEventNotFoundError: If event not found
        """
        from app.modules.stream.tasks import StreamAutoRestartManager

        event = await self.event_repository.get_by_id(event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {event_id} not found")

        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise StreamServiceError(f"Session {session_id} not found")

        restart_manager = StreamAutoRestartManager()

        # Update session status
        from app.modules.stream.models import ConnectionStatus
        session.connection_status = ConnectionStatus.DISCONNECTED.value
        if error:
            session.last_error = error

        # Check if auto-restart is enabled
        if not event.enable_auto_start:
            await self.session_repository.end_session(
                session, end_reason="disconnected_no_auto_restart"
            )
            await self.event_repository.set_status(event, LiveEventStatus.ENDED)
            await self.session.commit()
            return {"action": "ended", "reason": "auto_restart_disabled"}

        # Check if we should attempt restart
        if restart_manager.should_attempt_restart(session.reconnection_attempts):
            await self.session_repository.increment_reconnection_attempts(session)
            delay = restart_manager.calculate_restart_delay(session.reconnection_attempts)
            await self.session.commit()
            return {
                "action": "restart_scheduled",
                "attempt": session.reconnection_attempts,
                "delay_seconds": delay,
            }
        else:
            await self.session_repository.end_session(
                session,
                end_reason="max_reconnection_attempts_reached",
                error=error,
            )
            await self.event_repository.set_status(event, LiveEventStatus.FAILED)
            event.last_error = f"Stream failed after {session.reconnection_attempts} reconnection attempts"
            await self.session.commit()
            return {
                "action": "ended",
                "reason": "max_reconnection_attempts_reached",
                "total_attempts": session.reconnection_attempts,
            }

    async def check_schedule_conflict(
        self,
        account_id: uuid.UUID,
        start_at: datetime,
        end_at: Optional[datetime] = None,
        exclude_event_id: Optional[uuid.UUID] = None,
    ) -> Optional[LiveEvent]:
        """Check for scheduling conflicts on an account.

        Requirements: 6.4

        Args:
            account_id: YouTube account UUID
            start_at: Proposed start time
            end_at: Proposed end time
            exclude_event_id: Event ID to exclude from check

        Returns:
            Optional[LiveEvent]: Conflicting event if found
        """
        return await self.event_repository.check_schedule_conflict(
            account_id=account_id,
            start_at=start_at,
            end_at=end_at,
            exclude_event_id=exclude_event_id,
        )

    # ============================================
    # Playlist Streaming Methods (Requirements: 7.1, 7.2, 7.3, 7.4, 7.5)
    # ============================================

    async def create_playlist_stream(
        self,
        request: CreatePlaylistRequest,
    ) -> StreamPlaylist:
        """Create a playlist stream for a live event.

        Requirements: 7.1, 7.2, 7.3

        Args:
            request: Playlist creation request

        Returns:
            StreamPlaylist: Created playlist

        Raises:
            LiveEventNotFoundError: If live event not found
            StreamServiceError: If playlist already exists for event
        """
        # Verify live event exists
        event = await self.event_repository.get_by_id(request.live_event_id)
        if not event:
            raise LiveEventNotFoundError(f"Event {request.live_event_id} not found")

        # Check if playlist already exists
        existing = await self.playlist_repository.get_by_event_id(request.live_event_id)
        if existing:
            raise StreamServiceError(
                f"Playlist already exists for event {request.live_event_id}"
            )

        # Create playlist
        playlist = await self.playlist_repository.create(
            live_event_id=request.live_event_id,
            name=request.name,
            loop_mode=request.loop_mode.value,
            loop_count=request.loop_count,
            default_transition=request.default_transition.value,
            default_transition_duration_ms=request.default_transition_duration_ms,
        )

        # Add initial items
        for item_data in request.items:
            await self.playlist_item_repository.create(
                playlist_id=playlist.id,
                video_title=item_data.video_title,
                position=item_data.position,
                video_id=item_data.video_id,
                video_url=item_data.video_url,
                video_duration_seconds=item_data.video_duration_seconds,
                transition_type=item_data.transition_type.value,
                transition_duration_ms=item_data.transition_duration_ms,
                start_offset_seconds=item_data.start_offset_seconds,
                end_offset_seconds=item_data.end_offset_seconds,
            )

        await self.session.commit()
        return playlist

    async def get_playlist(
        self,
        playlist_id: uuid.UUID,
        include_items: bool = True,
    ) -> Optional[StreamPlaylist]:
        """Get playlist by ID.

        Args:
            playlist_id: Playlist UUID
            include_items: Whether to load items

        Returns:
            Optional[StreamPlaylist]: Playlist if found
        """
        return await self.playlist_repository.get_by_id(playlist_id, include_items)

    async def get_playlist_by_event(
        self,
        live_event_id: uuid.UUID,
        include_items: bool = True,
    ) -> Optional[StreamPlaylist]:
        """Get playlist for a live event.

        Args:
            live_event_id: Live event UUID
            include_items: Whether to load items

        Returns:
            Optional[StreamPlaylist]: Playlist if found
        """
        return await self.playlist_repository.get_by_event_id(
            live_event_id, include_items
        )

    async def update_playlist(
        self,
        playlist_id: uuid.UUID,
        request: UpdatePlaylistRequest,
    ) -> StreamPlaylist:
        """Update playlist settings.

        Requirements: 7.5 - Allow playlist modification during stream.

        Args:
            playlist_id: Playlist UUID
            request: Update request

        Returns:
            StreamPlaylist: Updated playlist

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        update_data = request.model_dump(exclude_unset=True)
        if "loop_mode" in update_data and update_data["loop_mode"]:
            update_data["loop_mode"] = update_data["loop_mode"].value
        if "default_transition" in update_data and update_data["default_transition"]:
            update_data["default_transition"] = update_data["default_transition"].value

        playlist = await self.playlist_repository.update(playlist, **update_data)
        await self.session.commit()
        return playlist

    async def add_playlist_item(
        self,
        playlist_id: uuid.UUID,
        item_data: PlaylistItemCreate,
    ) -> PlaylistItem:
        """Add item to playlist.

        Requirements: 7.1, 7.5

        Args:
            playlist_id: Playlist UUID
            item_data: Item creation data

        Returns:
            PlaylistItem: Created item

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        item = await self.playlist_item_repository.create(
            playlist_id=playlist_id,
            video_title=item_data.video_title,
            position=item_data.position,
            video_id=item_data.video_id,
            video_url=item_data.video_url,
            video_duration_seconds=item_data.video_duration_seconds,
            transition_type=item_data.transition_type.value,
            transition_duration_ms=item_data.transition_duration_ms,
            start_offset_seconds=item_data.start_offset_seconds,
            end_offset_seconds=item_data.end_offset_seconds,
        )

        await self.session.commit()
        return item

    async def update_playlist_item(
        self,
        item_id: uuid.UUID,
        request: PlaylistItemUpdate,
    ) -> PlaylistItem:
        """Update playlist item.

        Requirements: 7.5

        Args:
            item_id: Item UUID
            request: Update request

        Returns:
            PlaylistItem: Updated item

        Raises:
            StreamServiceError: If item not found
        """
        item = await self.playlist_item_repository.get_by_id(item_id)
        if not item:
            raise StreamServiceError(f"Playlist item {item_id} not found")

        update_data = request.model_dump(exclude_unset=True)
        if "transition_type" in update_data and update_data["transition_type"]:
            update_data["transition_type"] = update_data["transition_type"].value

        item = await self.playlist_item_repository.update(item, **update_data)
        await self.session.commit()
        return item

    async def remove_playlist_item(self, item_id: uuid.UUID) -> None:
        """Remove item from playlist.

        Requirements: 7.5

        Args:
            item_id: Item UUID

        Raises:
            StreamServiceError: If item not found
        """
        item = await self.playlist_item_repository.get_by_id(item_id)
        if not item:
            raise StreamServiceError(f"Playlist item {item_id} not found")

        await self.playlist_item_repository.delete(item)
        await self.session.commit()

    async def reorder_playlist(
        self,
        playlist_id: uuid.UUID,
        item_ids: list[uuid.UUID],
    ) -> list[PlaylistItem]:
        """Reorder playlist items.

        Requirements: 7.5 - Allow playlist modification during stream.

        Args:
            playlist_id: Playlist UUID
            item_ids: Item IDs in new order

        Returns:
            list[PlaylistItem]: Reordered items

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        items = await self.playlist_item_repository.reorder_items(playlist_id, item_ids)
        await self.session.commit()
        return items

    async def start_playlist_stream(
        self,
        playlist_id: uuid.UUID,
    ) -> PlaylistStreamStatus:
        """Start streaming a playlist.

        Requirements: 7.1, 7.2

        Args:
            playlist_id: Playlist UUID

        Returns:
            PlaylistStreamStatus: Current stream status

        Raises:
            StreamServiceError: If playlist not found or empty
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id, include_items=True)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        if not playlist.items:
            raise StreamServiceError("Playlist is empty")

        # Reset playlist state
        await self.playlist_repository.reset_playlist(playlist)
        await self.playlist_item_repository.reset_all_items(playlist_id)

        # Activate playlist
        playlist.is_active = True
        playlist.current_item_index = 0

        # Mark first item as playing
        first_item = playlist.items[0]
        await self.playlist_item_repository.mark_as_playing(first_item)

        await self.session.commit()

        return await self._build_playlist_status(playlist)

    async def advance_playlist(
        self,
        playlist_id: uuid.UUID,
        skip_on_failure: bool = True,
        failure_error: Optional[str] = None,
    ) -> PlaylistStreamStatus:
        """Advance playlist to next item.

        Implements loop logic (Requirements: 7.2) and skip on failure (Requirements: 7.4).

        Args:
            playlist_id: Playlist UUID
            skip_on_failure: Whether current item failed
            failure_error: Error message if failed

        Returns:
            PlaylistStreamStatus: Updated stream status

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id, include_items=True)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        if not playlist.is_active:
            raise StreamServiceError("Playlist is not active")

        # Get current item and mark as completed or skipped
        current_item = await self.playlist_item_repository.get_item_at_position(
            playlist_id, playlist.current_item_index
        )

        if current_item:
            if skip_on_failure and failure_error:
                # Requirements: 7.4 - Skip to next video on failure
                await self.playlist_item_repository.mark_as_skipped(current_item, failure_error)
                await self.playlist_repository.increment_stats(playlist, skips=1, failures=1)
            else:
                await self.playlist_item_repository.mark_as_completed(current_item)
                await self.playlist_repository.increment_stats(playlist, plays=1)

        # Advance to next item (handles loop logic per Requirements: 7.2)
        next_index = await self.playlist_repository.advance_to_next_item(playlist)

        if next_index is not None:
            # Mark next item as playing
            next_item = await self.playlist_item_repository.get_item_at_position(
                playlist_id, next_index
            )
            if next_item:
                await self.playlist_item_repository.mark_as_playing(next_item)

                # If looping back to start, reset all items
                if next_index == 0 and playlist.current_loop > 0:
                    await self.playlist_item_repository.reset_all_items(playlist_id)
                    await self.playlist_item_repository.mark_as_playing(next_item)

        await self.session.commit()

        # Refresh playlist to get updated state
        playlist = await self.playlist_repository.get_by_id(playlist_id, include_items=True)
        return await self._build_playlist_status(playlist)

    async def stop_playlist_stream(
        self,
        playlist_id: uuid.UUID,
    ) -> PlaylistStreamStatus:
        """Stop playlist streaming.

        Args:
            playlist_id: Playlist UUID

        Returns:
            PlaylistStreamStatus: Final stream status

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id, include_items=True)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        playlist.is_active = False
        await self.session.commit()

        return await self._build_playlist_status(playlist)

    async def get_playlist_status(
        self,
        playlist_id: uuid.UUID,
    ) -> PlaylistStreamStatus:
        """Get current playlist streaming status.

        Args:
            playlist_id: Playlist UUID

        Returns:
            PlaylistStreamStatus: Current stream status

        Raises:
            StreamServiceError: If playlist not found
        """
        playlist = await self.playlist_repository.get_by_id(playlist_id, include_items=True)
        if not playlist:
            raise StreamServiceError(f"Playlist {playlist_id} not found")

        return await self._build_playlist_status(playlist)

    async def _build_playlist_status(
        self,
        playlist: StreamPlaylist,
    ) -> PlaylistStreamStatus:
        """Build playlist status response.

        Args:
            playlist: StreamPlaylist instance

        Returns:
            PlaylistStreamStatus: Status response
        """
        from app.modules.stream.schemas import PlaylistItemResponse

        current_item = None
        next_item = None
        completed_items = 0
        skipped_items = 0
        failed_items = 0

        if playlist.items:
            for item in playlist.items:
                if item.position == playlist.current_item_index:
                    current_item = PlaylistItemResponse(
                        id=item.id,
                        playlist_id=item.playlist_id,
                        video_id=item.video_id,
                        video_url=item.video_url,
                        video_title=item.video_title,
                        video_duration_seconds=item.video_duration_seconds,
                        position=item.position,
                        transition_type=item.transition_type,
                        transition_duration_ms=item.transition_duration_ms,
                        start_offset_seconds=item.start_offset_seconds,
                        end_offset_seconds=item.end_offset_seconds,
                        status=item.status,
                        play_count=item.play_count,
                        last_played_at=item.last_played_at,
                        last_error=item.last_error,
                        effective_duration=item.get_effective_duration(),
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                    )

                next_index = playlist.get_next_item_index()
                if next_index is not None and item.position == next_index:
                    next_item = PlaylistItemResponse(
                        id=item.id,
                        playlist_id=item.playlist_id,
                        video_id=item.video_id,
                        video_url=item.video_url,
                        video_title=item.video_title,
                        video_duration_seconds=item.video_duration_seconds,
                        position=item.position,
                        transition_type=item.transition_type,
                        transition_duration_ms=item.transition_duration_ms,
                        start_offset_seconds=item.start_offset_seconds,
                        end_offset_seconds=item.end_offset_seconds,
                        status=item.status,
                        play_count=item.play_count,
                        last_played_at=item.last_played_at,
                        last_error=item.last_error,
                        effective_duration=item.get_effective_duration(),
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                    )

                if item.status == PlaylistItemStatus.COMPLETED.value:
                    completed_items += 1
                elif item.status == PlaylistItemStatus.SKIPPED.value:
                    skipped_items += 1
                elif item.status == PlaylistItemStatus.FAILED.value:
                    failed_items += 1

        return PlaylistStreamStatus(
            playlist_id=playlist.id,
            is_active=playlist.is_active,
            current_item_index=playlist.current_item_index,
            current_item=current_item,
            next_item=next_item,
            current_loop=playlist.current_loop,
            total_loops=playlist.loop_count,
            loop_mode=playlist.loop_mode,
            total_items=len(playlist.items) if playlist.items else 0,
            completed_items=completed_items,
            skipped_items=skipped_items,
            failed_items=failed_items,
        )

    def calculate_playlist_loop_behavior(
        self,
        loop_mode: str,
        loop_count: Optional[int],
        total_items: int,
        current_loop: int = 0,
    ) -> PlaylistLoopResult:
        """Calculate expected playlist loop behavior.

        Used for property testing of loop behavior (Property 12).

        Args:
            loop_mode: Loop mode (none, count, infinite)
            loop_count: Number of loops for COUNT mode
            total_items: Total items in playlist
            current_loop: Current loop iteration

        Returns:
            PlaylistLoopResult: Expected loop behavior
        """
        should_loop = False
        total_plays_expected = total_items

        if loop_mode == PlaylistLoopMode.INFINITE.value:
            should_loop = True
            # For infinite, we can't calculate total plays
            total_plays_expected = -1  # Indicates infinite
        elif loop_mode == PlaylistLoopMode.COUNT.value and loop_count is not None:
            should_loop = current_loop < loop_count
            total_plays_expected = total_items * loop_count
        else:
            # NONE mode
            should_loop = False
            total_plays_expected = total_items

        return PlaylistLoopResult(
            should_loop=should_loop,
            current_loop=current_loop,
            loop_count=loop_count,
            loop_mode=loop_mode,
            total_plays_expected=total_plays_expected,
        )
