"""Strike service for strike management operations.

Implements strike sync, alerting, and auto-pause functionality.
Requirements: 20.1, 20.2, 20.3, 20.4, 20.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import YouTubeAccount
from app.modules.account.repository import YouTubeAccountRepository
from app.modules.stream.models import LiveEvent, LiveEventStatus
from app.modules.stream.repository import LiveEventRepository
from app.modules.strike.models import (
    Strike,
    StrikeAlert,
    PausedStream,
    StrikeStatus,
    StrikeType,
    StrikeSeverity,
    AppealStatus,
)
from app.modules.strike.repository import (
    StrikeRepository,
    StrikeAlertRepository,
    PausedStreamRepository,
)
from app.modules.strike.schemas import (
    StrikeCreate,
    StrikeResponse,
    StrikeSummary,
    StrikeSyncResult,
    StrikeTimeline,
    StrikeTimelineEvent,
    AccountStrikeTimeline,
    YouTubeStrikeData,
)
from app.modules.strike.youtube_api import YouTubeStrikeClient


class StrikeServiceError(Exception):
    """Base exception for strike service errors."""
    pass


class AccountNotFoundError(StrikeServiceError):
    """Exception raised when account is not found."""
    pass


class StrikeNotFoundError(StrikeServiceError):
    """Exception raised when strike is not found."""
    pass


class StrikeService:
    """Service for strike management operations."""

    # Alert timing threshold (Requirements: 20.2)
    ALERT_THRESHOLD_HOURS = 1

    def __init__(self, session: AsyncSession):
        """Initialize strike service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.strike_repository = StrikeRepository(session)
        self.alert_repository = StrikeAlertRepository(session)
        self.paused_stream_repository = PausedStreamRepository(session)
        self.account_repository = YouTubeAccountRepository(session)
        self.event_repository = LiveEventRepository(session)

    async def sync_strikes(self, account_id: uuid.UUID) -> StrikeSyncResult:
        """Sync strike status from YouTube for an account.

        Fetches current strike status and updates local records.
        Requirements: 20.1

        Args:
            account_id: YouTube account UUID

        Returns:
            StrikeSyncResult: Result of sync operation
        """
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        # Initialize YouTube client
        client = YouTubeStrikeClient(account.access_token)

        # Fetch strikes from YouTube
        youtube_strikes = await client.get_channel_strikes(account.channel_id)

        new_strikes = 0
        updated_strikes = 0
        resolved_strikes = 0

        # Process each strike from YouTube
        for strike_data in youtube_strikes:
            existing_strike = None
            if strike_data.strike_id:
                existing_strike = await self.strike_repository.get_by_youtube_id(
                    strike_data.strike_id
                )

            if existing_strike:
                # Update existing strike
                await self.strike_repository.update(
                    existing_strike,
                    reason=strike_data.reason,
                    reason_details=strike_data.reason_details,
                    expires_at=strike_data.expires_at,
                )
                updated_strikes += 1
            else:
                # Create new strike
                await self.create_strike(
                    StrikeCreate(
                        account_id=account_id,
                        youtube_strike_id=strike_data.strike_id,
                        strike_type=StrikeType(strike_data.strike_type),
                        severity=StrikeSeverity(strike_data.severity),
                        reason=strike_data.reason,
                        reason_details=strike_data.reason_details,
                        affected_video_id=strike_data.affected_video_id,
                        affected_video_title=strike_data.affected_video_title,
                        issued_at=strike_data.issued_at,
                        expires_at=strike_data.expires_at,
                    )
                )
                new_strikes += 1

        # Check for resolved strikes (in our DB but not in YouTube response)
        youtube_strike_ids = {s.strike_id for s in youtube_strikes if s.strike_id}
        local_strikes = await self.strike_repository.get_active_strikes(account_id)
        
        for local_strike in local_strikes:
            if (
                local_strike.youtube_strike_id
                and local_strike.youtube_strike_id not in youtube_strike_ids
            ):
                await self.strike_repository.set_status(
                    local_strike, StrikeStatus.RESOLVED
                )
                resolved_strikes += 1

        # Update account strike count
        active_count = await self.strike_repository.count_active_strikes(account_id)
        account.strike_count = active_count
        
        await self.session.commit()

        # Get updated strikes list
        all_strikes = await self.strike_repository.get_by_account_id(account_id)
        strike_responses = [
            StrikeResponse.model_validate(s) for s in all_strikes
        ]

        return StrikeSyncResult(
            account_id=account_id,
            synced_at=datetime.utcnow(),
            new_strikes=new_strikes,
            updated_strikes=updated_strikes,
            resolved_strikes=resolved_strikes,
            total_active_strikes=active_count,
            strikes=strike_responses,
        )

    async def create_strike(self, request: StrikeCreate) -> Strike:
        """Create a new strike record.

        Args:
            request: Strike creation request

        Returns:
            Strike: Created strike
        """
        strike = await self.strike_repository.create(
            account_id=request.account_id,
            youtube_strike_id=request.youtube_strike_id,
            strike_type=request.strike_type.value,
            severity=request.severity.value,
            reason=request.reason,
            reason_details=request.reason_details,
            affected_video_id=request.affected_video_id,
            affected_video_title=request.affected_video_title,
            affected_content_url=request.affected_content_url,
            issued_at=request.issued_at,
            expires_at=request.expires_at,
            extra_data=request.extra_data,
        )

        await self.session.commit()
        return strike

    async def get_strike(self, strike_id: uuid.UUID) -> Optional[Strike]:
        """Get strike by ID.

        Args:
            strike_id: Strike UUID

        Returns:
            Optional[Strike]: Strike if found
        """
        return await self.strike_repository.get_by_id(strike_id, include_alerts=True)

    async def get_account_strikes(
        self,
        account_id: uuid.UUID,
        include_expired: bool = False,
    ) -> list[Strike]:
        """Get all strikes for an account.

        Args:
            account_id: YouTube account UUID
            include_expired: Include expired strikes

        Returns:
            list[Strike]: List of strikes
        """
        return await self.strike_repository.get_by_account_id(
            account_id, include_expired=include_expired
        )

    async def get_strike_summary(self, account_id: uuid.UUID) -> StrikeSummary:
        """Get strike summary for an account.

        Args:
            account_id: YouTube account UUID

        Returns:
            StrikeSummary: Strike summary
        """
        all_strikes = await self.strike_repository.get_by_account_id(
            account_id, include_expired=True
        )

        active_count = 0
        appealed_count = 0
        resolved_count = 0
        expired_count = 0
        has_high_risk = False
        latest_strike = None

        for strike in all_strikes:
            if strike.status == StrikeStatus.ACTIVE.value:
                active_count += 1
                if strike.is_high_risk():
                    has_high_risk = True
            elif strike.status == StrikeStatus.EXPIRED.value:
                expired_count += 1
            elif strike.status == StrikeStatus.RESOLVED.value:
                resolved_count += 1
            
            if strike.appeal_status != AppealStatus.NOT_APPEALED.value:
                appealed_count += 1

            if latest_strike is None or strike.issued_at > latest_strike.issued_at:
                latest_strike = strike

        return StrikeSummary(
            account_id=account_id,
            total_strikes=len(all_strikes),
            active_strikes=active_count,
            appealed_strikes=appealed_count,
            resolved_strikes=resolved_count,
            expired_strikes=expired_count,
            has_high_risk=has_high_risk,
            latest_strike=StrikeResponse.model_validate(latest_strike) if latest_strike else None,
        )

    async def get_strike_timeline(self, strike_id: uuid.UUID) -> StrikeTimeline:
        """Get timeline of events for a strike.

        Requirements: 20.4

        Args:
            strike_id: Strike UUID

        Returns:
            StrikeTimeline: Timeline of events
        """
        strike = await self.strike_repository.get_by_id(strike_id, include_alerts=True)
        if not strike:
            raise StrikeNotFoundError(f"Strike {strike_id} not found")

        events = []

        # Strike issued event
        events.append(StrikeTimelineEvent(
            event_type="issued",
            timestamp=strike.issued_at,
            description=f"Strike issued: {strike.reason}",
            details={
                "strike_type": strike.strike_type,
                "severity": strike.severity,
            },
        ))

        # Appeal events
        if strike.appeal_submitted_at:
            events.append(StrikeTimelineEvent(
                event_type="appealed",
                timestamp=strike.appeal_submitted_at,
                description="Appeal submitted",
                details={"reason": strike.appeal_reason},
            ))

        if strike.appeal_resolved_at:
            events.append(StrikeTimelineEvent(
                event_type="appeal_resolved",
                timestamp=strike.appeal_resolved_at,
                description=f"Appeal {strike.appeal_status}",
                details={"response": strike.appeal_response},
            ))

        # Resolution events
        if strike.resolved_at:
            events.append(StrikeTimelineEvent(
                event_type="resolved",
                timestamp=strike.resolved_at,
                description=f"Strike resolved: {strike.status}",
            ))

        # Expiry event
        if strike.expires_at and strike.status == StrikeStatus.EXPIRED.value:
            events.append(StrikeTimelineEvent(
                event_type="expired",
                timestamp=strike.expires_at,
                description="Strike expired",
            ))

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        return StrikeTimeline(strike_id=strike_id, events=events)

    async def get_account_strike_timeline(
        self, account_id: uuid.UUID
    ) -> AccountStrikeTimeline:
        """Get timeline of all strikes for an account.

        Requirements: 20.4

        Args:
            account_id: YouTube account UUID

        Returns:
            AccountStrikeTimeline: Account strike timeline
        """
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        strikes = await self.strike_repository.get_by_account_id(
            account_id, include_expired=True
        )

        timelines = []
        for strike in strikes:
            timeline = await self.get_strike_timeline(strike.id)
            timelines.append(timeline)

        return AccountStrikeTimeline(
            account_id=account_id,
            channel_title=account.channel_title,
            timelines=timelines,
            total_strikes=len(strikes),
        )


    async def create_strike_alert(
        self,
        strike: Strike,
        alert_type: str = "new_strike",
    ) -> StrikeAlert:
        """Create an alert for a strike.

        Requirements: 20.2

        Args:
            strike: Strike to alert about
            alert_type: Type of alert

        Returns:
            StrikeAlert: Created alert
        """
        title = self._get_alert_title(strike, alert_type)
        message = self._get_alert_message(strike, alert_type)
        severity = "critical" if strike.is_high_risk() else "high"

        alert = await self.alert_repository.create(
            strike_id=strike.id,
            account_id=strike.account_id,
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity,
        )

        # Mark strike notification as sent
        await self.strike_repository.mark_notification_sent(strike)

        await self.session.commit()
        return alert

    def _get_alert_title(self, strike: Strike, alert_type: str) -> str:
        """Generate alert title based on strike and alert type."""
        titles = {
            "new_strike": f"New {strike.strike_type.replace('_', ' ').title()} Strike Detected",
            "strike_risk": f"Strike Risk Warning: {strike.strike_type.replace('_', ' ').title()}",
            "appeal_update": f"Strike Appeal Update",
            "strike_expiring": f"Strike Expiring Soon",
            "streams_paused": f"Scheduled Streams Paused Due to Strike",
        }
        return titles.get(alert_type, "Strike Alert")

    def _get_alert_message(self, strike: Strike, alert_type: str) -> str:
        """Generate alert message based on strike and alert type."""
        base_message = f"Reason: {strike.reason}"
        
        if strike.affected_video_title:
            base_message += f"\nAffected content: {strike.affected_video_title}"
        
        if strike.severity == StrikeSeverity.TERMINATION_RISK.value:
            base_message += "\n\n⚠️ WARNING: This strike puts your channel at risk of termination!"
        
        if alert_type == "streams_paused":
            base_message += "\n\nScheduled streams have been automatically paused. Please review and confirm to resume."
        
        return base_message

    async def check_and_alert_new_strikes(
        self,
        account_id: uuid.UUID,
        detection_time: datetime,
    ) -> list[StrikeAlert]:
        """Check for new strikes and create alerts within threshold.

        Requirements: 20.2 - Alert within 1 hour of flag detection

        Args:
            account_id: YouTube account UUID
            detection_time: Time when strike was detected

        Returns:
            list[StrikeAlert]: Created alerts
        """
        alerts = []
        threshold = datetime.utcnow() - timedelta(hours=self.ALERT_THRESHOLD_HOURS)

        # Get strikes that haven't been notified yet
        strikes = await self.strike_repository.get_active_strikes(account_id)
        
        for strike in strikes:
            if not strike.notification_sent:
                # Check if within alert threshold
                if strike.issued_at >= threshold or detection_time >= threshold:
                    alert = await self.create_strike_alert(strike, "new_strike")
                    alerts.append(alert)

        return alerts

    async def pause_scheduled_streams(
        self,
        account_id: uuid.UUID,
        strike: Strike,
    ) -> list[PausedStream]:
        """Pause scheduled streams due to strike risk.

        Requirements: 20.3

        Args:
            account_id: YouTube account UUID
            strike: Strike causing the pause

        Returns:
            list[PausedStream]: List of paused streams
        """
        paused_streams = []

        # Get scheduled streams for the account
        scheduled_events = await self.event_repository.get_by_account_id(
            account_id=account_id,
            status=LiveEventStatus.SCHEDULED,
        )

        for event in scheduled_events:
            # Check if already paused
            existing_pause = await self.paused_stream_repository.get_by_event_id(event.id)
            if existing_pause:
                continue

            # Create paused stream record
            paused_stream = await self.paused_stream_repository.create(
                strike_id=strike.id,
                live_event_id=event.id,
                account_id=account_id,
                original_status=event.status,
                original_scheduled_start_at=event.scheduled_start_at,
                pause_reason=f"Strike detected: {strike.reason}",
            )

            # Update event status to cancelled/paused
            await self.event_repository.set_status(
                event, LiveEventStatus.CANCELLED, error="Paused due to strike risk"
            )

            paused_streams.append(paused_stream)

        # Mark strike as having paused streams
        if paused_streams:
            await self.strike_repository.mark_streams_paused(strike)
            
            # Create alert for paused streams
            await self.create_strike_alert(strike, "streams_paused")

        await self.session.commit()
        return paused_streams

    async def resume_paused_stream(
        self,
        paused_stream_id: uuid.UUID,
        user_id: uuid.UUID,
        confirmation: bool = True,
    ) -> PausedStream:
        """Resume a paused stream with user confirmation.

        Requirements: 20.5

        Args:
            paused_stream_id: Paused stream UUID
            user_id: User confirming the resume
            confirmation: User confirmation flag

        Returns:
            PausedStream: Updated paused stream record
        """
        paused_stream = await self.paused_stream_repository.get_by_id(paused_stream_id)
        if not paused_stream:
            raise StrikeServiceError(f"Paused stream {paused_stream_id} not found")

        if paused_stream.resumed:
            raise StrikeServiceError("Stream has already been resumed")

        if not confirmation:
            raise StrikeServiceError("User confirmation required to resume stream")

        # Resume the paused stream record
        paused_stream = await self.paused_stream_repository.resume(
            paused_stream, user_id, confirmation
        )

        # Restore the live event to scheduled status
        event = await self.event_repository.get_by_id(paused_stream.live_event_id)
        if event:
            await self.event_repository.set_status(event, LiveEventStatus.SCHEDULED)
            event.last_error = None

        # Update strike record
        strike = await self.strike_repository.get_by_id(paused_stream.strike_id)
        if strike:
            # Check if all streams for this strike have been resumed
            remaining_paused = await self.paused_stream_repository.get_by_strike_id(
                strike.id
            )
            all_resumed = all(ps.resumed for ps in remaining_paused)
            if all_resumed:
                await self.strike_repository.mark_streams_resumed(strike)

        await self.session.commit()
        return paused_stream

    async def resume_all_paused_streams(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        confirmation: bool = True,
    ) -> list[PausedStream]:
        """Resume all paused streams for an account.

        Requirements: 20.5

        Args:
            account_id: YouTube account UUID
            user_id: User confirming the resume
            confirmation: User confirmation flag

        Returns:
            list[PausedStream]: List of resumed streams
        """
        if not confirmation:
            raise StrikeServiceError("User confirmation required to resume streams")

        paused_streams = await self.paused_stream_repository.get_by_account_id(
            account_id, resumed=False
        )

        resumed_streams = []
        for paused_stream in paused_streams:
            try:
                resumed = await self.resume_paused_stream(
                    paused_stream.id, user_id, confirmation
                )
                resumed_streams.append(resumed)
            except StrikeServiceError:
                continue

        return resumed_streams

    async def get_paused_streams(
        self,
        account_id: uuid.UUID,
        include_resumed: bool = False,
    ) -> list[PausedStream]:
        """Get paused streams for an account.

        Args:
            account_id: YouTube account UUID
            include_resumed: Include already resumed streams

        Returns:
            list[PausedStream]: List of paused streams
        """
        resumed_filter = None if include_resumed else False
        return await self.paused_stream_repository.get_by_account_id(
            account_id, resumed=resumed_filter
        )

    async def submit_appeal(
        self,
        strike_id: uuid.UUID,
        appeal_reason: str,
    ) -> Strike:
        """Submit an appeal for a strike.

        Args:
            strike_id: Strike UUID
            appeal_reason: Reason for appeal

        Returns:
            Strike: Updated strike
        """
        strike = await self.strike_repository.get_by_id(strike_id)
        if not strike:
            raise StrikeNotFoundError(f"Strike {strike_id} not found")

        if not strike.can_appeal():
            raise StrikeServiceError("Strike cannot be appealed")

        strike = await self.strike_repository.set_appeal_status(
            strike,
            AppealStatus.PENDING,
            appeal_reason=appeal_reason,
        )

        await self.session.commit()
        return strike

    async def update_appeal_status(
        self,
        strike_id: uuid.UUID,
        appeal_status: AppealStatus,
        appeal_response: Optional[str] = None,
    ) -> Strike:
        """Update appeal status for a strike.

        Args:
            strike_id: Strike UUID
            appeal_status: New appeal status
            appeal_response: Response from YouTube (if any)

        Returns:
            Strike: Updated strike
        """
        strike = await self.strike_repository.get_by_id(strike_id)
        if not strike:
            raise StrikeNotFoundError(f"Strike {strike_id} not found")

        strike = await self.strike_repository.set_appeal_status(
            strike,
            appeal_status,
            appeal_response=appeal_response,
        )

        # If appeal approved, resume any paused streams
        if appeal_status == AppealStatus.APPROVED:
            paused_streams = await self.paused_stream_repository.get_by_strike_id(
                strike_id
            )
            # Note: Streams still require user confirmation to resume

        await self.session.commit()
        return strike

    async def check_expired_strikes(self) -> int:
        """Check and update expired strikes.

        Returns:
            int: Number of strikes marked as expired
        """
        # This would typically be called by a scheduled task
        # Implementation would query all active strikes and check expiry
        expired_count = 0
        # TODO: Implement batch expiry check
        return expired_count
