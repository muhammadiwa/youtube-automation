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
)
from app.modules.stream.repository import (
    LiveEventRepository,
    StreamSessionRepository,
    RecurrencePatternRepository,
)
from app.modules.stream.schemas import (
    CreateLiveEventRequest,
    ScheduleLiveEventRequest,
    UpdateLiveEventRequest,
    CreateRecurringEventRequest,
    RecurrencePatternRequest,
    LiveEventResponse,
    ScheduleConflictError,
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
