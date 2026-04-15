"""Monitoring service - Live Control Center.

Provides real-time monitoring data for YouTube channels and streams.
All data is fetched from database - no mock data.
"""

import uuid
from datetime import timedelta
from typing import Optional

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow, ensure_utc, to_naive_utc, is_in_future, hours_since

from app.modules.account.models import YouTubeAccount, AccountStatus
from app.modules.stream.models import LiveEvent, LiveEventStatus
from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
from app.modules.monitoring.schemas import (
    StreamStatus,
    HealthStatus,
    AlertSeverity,
    AlertType,
    Alert,
    LiveStreamInfo,
    LiveStreamsResponse,
    ScheduledStreamInfo,
    ScheduledStreamsResponse,
    ChannelStatusInfo,
    MonitoringOverview,
    MonitoringDashboardResponse,
)


class MonitoringService:
    """Service for Live Control Center monitoring."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # Main Dashboard
    # ========================================================================

    async def get_dashboard(self, user_id: uuid.UUID) -> MonitoringDashboardResponse:
        """Get complete monitoring dashboard data.
        
        Args:
            user_id: User ID to get data for
            
        Returns:
            Complete dashboard with overview, live streams, scheduled, channels, alerts
        """
        # Get all user's accounts
        accounts = await self._get_user_accounts(user_id)
        
        # Build channel status list
        channels: list[ChannelStatusInfo] = []
        live_streams: list[LiveStreamInfo] = []
        scheduled_streams: list[ScheduledStreamInfo] = []
        alerts: list[Alert] = []
        
        for account in accounts:
            # Get channel status
            channel_status = await self._build_channel_status(account)
            channels.append(channel_status)
            
            # Collect live stream if any
            if channel_status.current_stream:
                live_streams.append(channel_status.current_stream)
            
            # Collect scheduled stream if any
            if channel_status.next_scheduled:
                scheduled_streams.append(channel_status.next_scheduled)
            
            # Generate alerts for this channel
            channel_alerts = self._generate_alerts(account, channel_status)
            alerts.extend(channel_alerts)
        
        # Get all scheduled streams (not just next one per channel)
        all_scheduled = await self._get_all_scheduled_streams(user_id)
        
        # Build overview
        overview = self._build_overview(channels, live_streams, all_scheduled, alerts)
        
        # Sort alerts by severity and time
        alerts.sort(key=lambda a: (
            0 if a.severity == AlertSeverity.CRITICAL else 1 if a.severity == AlertSeverity.WARNING else 2,
            a.created_at
        ), reverse=True)
        
        return MonitoringDashboardResponse(
            overview=overview,
            live_streams=live_streams,
            scheduled_streams=all_scheduled[:10],  # Limit to 10 upcoming
            channels=channels,
            alerts=alerts[:20],  # Limit to 20 alerts
        )

    # ========================================================================
    # Live Streams
    # ========================================================================

    async def get_live_streams(self, user_id: uuid.UUID) -> LiveStreamsResponse:
        """Get all currently live streams for user.
        
        Only returns streams that are truly live (no error, not stale).
        
        Args:
            user_id: User ID
            
        Returns:
            List of live streams with total counts
        """
        now = utcnow()
        # Calculate 24 hours ago for stale check
        stale_threshold = to_naive_utc(now - timedelta(hours=24))
        
        # Get live events - only those without errors and not stale
        query = (
            select(LiveEvent, YouTubeAccount)
            .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
            .where(
                and_(
                    YouTubeAccount.user_id == user_id,
                    LiveEvent.status == LiveEventStatus.LIVE.value,
                    LiveEvent.last_error.is_(None),  # No error
                )
            )
            .order_by(LiveEvent.actual_start_at.desc())
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        streams = []
        total_viewers = 0
        
        for event, account in rows:
            # Skip stale streams (live for more than 24 hours)
            if event.actual_start_at:
                start = to_naive_utc(ensure_utc(event.actual_start_at))
                if start < stale_threshold:
                    continue  # Skip stale stream
            
            stream_info = self._build_live_stream_info(event, account)
            streams.append(stream_info)
            total_viewers += stream_info.viewer_count
        
        return LiveStreamsResponse(
            streams=streams,
            total_live=len(streams),
            total_viewers=total_viewers,
        )

    # ========================================================================
    # Scheduled Streams
    # ========================================================================

    async def get_scheduled_streams(
        self, 
        user_id: uuid.UUID,
        days_ahead: int = 7,
    ) -> ScheduledStreamsResponse:
        """Get scheduled streams for user.
        
        Args:
            user_id: User ID
            days_ahead: How many days ahead to look
            
        Returns:
            List of scheduled streams
        """
        streams = await self._get_all_scheduled_streams(user_id, days_ahead)
        
        return ScheduledStreamsResponse(
            streams=streams,
            total_scheduled=len(streams),
        )

    async def _get_all_scheduled_streams(
        self,
        user_id: uuid.UUID,
        days_ahead: int = 7,
    ) -> list[ScheduledStreamInfo]:
        """Get all scheduled streams for user from both LiveEvent and StreamJob."""
        now = utcnow()
        now_naive = to_naive_utc(now)
        end_date = to_naive_utc(now + timedelta(days=days_ahead))
        
        streams = []
        
        # 1. Get from LiveEvent (YouTube Live broadcasts)
        live_event_query = (
            select(LiveEvent, YouTubeAccount)
            .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
            .where(
                and_(
                    YouTubeAccount.user_id == user_id,
                    LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                    LiveEvent.scheduled_start_at.isnot(None),
                )
            )
            .order_by(LiveEvent.scheduled_start_at.asc())
        )
        
        result = await self.session.execute(live_event_query)
        rows = result.all()
        
        for event, account in rows:
            # Handle timezone comparison
            scheduled_at = to_naive_utc(ensure_utc(event.scheduled_start_at))
            if scheduled_at:
                if scheduled_at > now_naive and scheduled_at < end_date:
                    stream_info = self._build_scheduled_stream_info(event, account)
                    streams.append(stream_info)
        
        # 2. Get from StreamJob (FFmpeg streaming jobs)
        stream_job_query = (
            select(StreamJob, YouTubeAccount)
            .join(YouTubeAccount, StreamJob.account_id == YouTubeAccount.id)
            .where(
                and_(
                    StreamJob.user_id == user_id,
                    StreamJob.status == StreamJobStatus.SCHEDULED.value,
                    StreamJob.scheduled_start_at.isnot(None),
                )
            )
            .order_by(StreamJob.scheduled_start_at.asc())
        )
        
        result = await self.session.execute(stream_job_query)
        rows = result.all()
        
        for job, account in rows:
            # Handle timezone comparison
            scheduled_at = to_naive_utc(ensure_utc(job.scheduled_start_at))
            if scheduled_at:
                if scheduled_at > now_naive and scheduled_at < end_date:
                    stream_info = self._build_scheduled_stream_info_from_job(job, account)
                    streams.append(stream_info)
        
        # Sort all streams by scheduled time
        streams.sort(key=lambda s: s.scheduled_start_at)
        
        return streams
    
    def _build_scheduled_stream_info_from_job(
        self, job: StreamJob, account: YouTubeAccount
    ) -> ScheduledStreamInfo:
        """Build scheduled stream info from StreamJob."""
        now = utcnow()
        scheduled_at = ensure_utc(job.scheduled_start_at)
        
        starts_in = int((scheduled_at - now).total_seconds()) if scheduled_at else 0
        
        # Use ensure_utc() to keep timezone info - Pydantic will serialize with +00:00
        # Frontend will correctly interpret as UTC
        return ScheduledStreamInfo(
            stream_id=str(job.id),
            account_id=str(account.id),
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            channel_thumbnail=account.thumbnail_url,
            title=job.title,
            description=job.description,
            scheduled_start_at=ensure_utc(scheduled_at),
            scheduled_end_at=ensure_utc(job.scheduled_end_at),
            starts_in_seconds=max(0, starts_in),
        )

    # ========================================================================
    # Channel Status
    # ========================================================================

    async def get_channel_status(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[ChannelStatusInfo]:
        """Get status for a specific channel.
        
        Args:
            account_id: Account ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Channel status or None if not found
        """
        query = select(YouTubeAccount).where(
            and_(
                YouTubeAccount.id == account_id,
                YouTubeAccount.user_id == user_id,
            )
        )
        result = await self.session.execute(query)
        account = result.scalar_one_or_none()
        
        if not account:
            return None
        
        return await self._build_channel_status(account)

    # ========================================================================
    # Alerts
    # ========================================================================

    async def get_alerts(self, user_id: uuid.UUID) -> list[Alert]:
        """Get all active alerts for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of alerts sorted by severity
        """
        accounts = await self._get_user_accounts(user_id)
        alerts = []
        
        for account in accounts:
            channel_status = await self._build_channel_status(account)
            channel_alerts = self._generate_alerts(account, channel_status)
            alerts.extend(channel_alerts)
        
        # Sort by severity
        alerts.sort(key=lambda a: (
            0 if a.severity == AlertSeverity.CRITICAL else 1 if a.severity == AlertSeverity.WARNING else 2,
            a.created_at
        ), reverse=True)
        
        return alerts

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_user_accounts(self, user_id: uuid.UUID) -> list[YouTubeAccount]:
        """Get all accounts for a user."""
        query = (
            select(YouTubeAccount)
            .where(YouTubeAccount.user_id == user_id)
            .order_by(YouTubeAccount.channel_title)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _build_channel_status(self, account: YouTubeAccount) -> ChannelStatusInfo:
        """Build channel status from account data."""
        # Determine stream status
        stream_status = await self._get_stream_status(account.id)
        
        # Get current live stream if any
        current_stream = await self._get_current_live_stream(account)
        
        # Get next scheduled stream
        next_scheduled = await self._get_next_scheduled_stream(account)
        
        # Determine health status
        health_status = self._determine_health_status(account)
        
        # Count alerts
        alert_count = self._count_alerts(account)
        
        # Calculate quota percentage
        quota_percent = account.get_quota_usage_percent() if hasattr(account, 'get_quota_usage_percent') else 0.0
        
        return ChannelStatusInfo(
            account_id=str(account.id),
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            thumbnail_url=account.thumbnail_url,
            subscriber_count=account.subscriber_count or 0,
            video_count=account.video_count or 0,
            view_count=account.view_count or 0,
            stream_status=stream_status,
            health_status=health_status,
            token_expires_at=account.token_expires_at,
            is_token_expired=account.is_token_expired() if hasattr(account, 'is_token_expired') else False,
            is_token_expiring_soon=account.is_token_expiring_soon(hours=24) if hasattr(account, 'is_token_expiring_soon') else False,
            quota_used=account.daily_quota_used or 0,
            quota_limit=10000,
            quota_percent=quota_percent,
            strike_count=account.strike_count or 0,
            has_error=account.status == AccountStatus.ERROR.value if hasattr(AccountStatus, 'ERROR') else account.status == "error",
            last_error=account.last_error,
            alert_count=alert_count,
            current_stream=current_stream,
            next_scheduled=next_scheduled,
            last_sync_at=account.last_sync_at,
        )

    async def _get_stream_status(self, account_id: uuid.UUID) -> StreamStatus:
        """Determine stream status for an account (checks both LiveEvent and StreamJob)."""
        now = utcnow()
        now_naive = to_naive_utc(now)
        
        # Check if live from LiveEvent
        live_query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account_id,
                    LiveEvent.status == LiveEventStatus.LIVE.value,
                    LiveEvent.last_error.is_(None),
                )
            )
            .limit(1)
        )
        result = await self.session.execute(live_query)
        live_event = result.scalar_one_or_none()
        
        if live_event:
            if live_event.actual_start_at:
                start = ensure_utc(live_event.actual_start_at)
                hours_live = hours_since(start)
                if hours_live <= 24:
                    return StreamStatus.LIVE
        
        # Check if live from StreamJob (running status)
        streaming_job_query = (
            select(StreamJob)
            .where(
                and_(
                    StreamJob.account_id == account_id,
                    StreamJob.status == StreamJobStatus.RUNNING.value,
                )
            )
            .limit(1)
        )
        result = await self.session.execute(streaming_job_query)
        if result.scalar_one_or_none():
            return StreamStatus.LIVE
        
        # Check if scheduled from LiveEvent
        scheduled_query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account_id,
                    LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                    LiveEvent.scheduled_start_at.isnot(None),
                )
            )
            .order_by(LiveEvent.scheduled_start_at.asc())
            .limit(1)
        )
        result = await self.session.execute(scheduled_query)
        event = result.scalar_one_or_none()
        if event and event.scheduled_start_at:
            scheduled_at = to_naive_utc(ensure_utc(event.scheduled_start_at))
            if scheduled_at > now_naive:
                return StreamStatus.SCHEDULED
        
        # Check if scheduled from StreamJob
        scheduled_job_query = (
            select(StreamJob)
            .where(
                and_(
                    StreamJob.account_id == account_id,
                    StreamJob.status == StreamJobStatus.SCHEDULED.value,
                    StreamJob.scheduled_start_at.isnot(None),
                )
            )
            .order_by(StreamJob.scheduled_start_at.asc())
            .limit(1)
        )
        result = await self.session.execute(scheduled_job_query)
        job = result.scalar_one_or_none()
        if job and job.scheduled_start_at:
            scheduled_at = to_naive_utc(ensure_utc(job.scheduled_start_at))
            if scheduled_at > now_naive:
                return StreamStatus.SCHEDULED
        
        return StreamStatus.OFFLINE

    async def _get_current_live_stream(self, account: YouTubeAccount) -> Optional[LiveStreamInfo]:
        """Get current live stream for account.
        
        Only returns streams that are truly live (no error, not stale).
        """
        query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account.id,
                    LiveEvent.status == LiveEventStatus.LIVE.value,
                    LiveEvent.last_error.is_(None),
                )
            )
            .order_by(LiveEvent.actual_start_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return None
        
        # Check if stream is stale (live for more than 24 hours)
        if event.actual_start_at:
            hours_live = hours_since(event.actual_start_at)
            if hours_live > 24:
                return None  # Stale stream, don't show as live
        
        return self._build_live_stream_info(event, account)

    async def _get_next_scheduled_stream(self, account: YouTubeAccount) -> Optional[ScheduledStreamInfo]:
        """Get next scheduled stream for account (checks both LiveEvent and StreamJob)."""
        now = utcnow()
        now_naive = to_naive_utc(now)
        candidates = []
        
        # Check LiveEvent
        event_query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account.id,
                    LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                    LiveEvent.scheduled_start_at.isnot(None),
                )
            )
            .order_by(LiveEvent.scheduled_start_at.asc())
            .limit(1)
        )
        result = await self.session.execute(event_query)
        event = result.scalar_one_or_none()
        
        if event and event.scheduled_start_at:
            scheduled_at = to_naive_utc(ensure_utc(event.scheduled_start_at))
            if scheduled_at > now_naive:
                candidates.append(('event', event, scheduled_at))
        
        # Check StreamJob
        job_query = (
            select(StreamJob)
            .where(
                and_(
                    StreamJob.account_id == account.id,
                    StreamJob.status == StreamJobStatus.SCHEDULED.value,
                    StreamJob.scheduled_start_at.isnot(None),
                )
            )
            .order_by(StreamJob.scheduled_start_at.asc())
            .limit(1)
        )
        result = await self.session.execute(job_query)
        job = result.scalar_one_or_none()
        
        if job and job.scheduled_start_at:
            scheduled_at = to_naive_utc(ensure_utc(job.scheduled_start_at))
            if scheduled_at > now_naive:
                candidates.append(('job', job, scheduled_at))
        
        if not candidates:
            return None
        
        # Return the one with earliest scheduled time
        candidates.sort(key=lambda x: x[2])
        source_type, source, _ = candidates[0]
        
        if source_type == 'event':
            return self._build_scheduled_stream_info(source, account)
        else:
            return self._build_scheduled_stream_info_from_job(source, account)

    def _build_live_stream_info(self, event: LiveEvent, account: YouTubeAccount) -> LiveStreamInfo:
        """Build live stream info from event and account."""
        now = utcnow()
        started_at = ensure_utc(event.actual_start_at) or now
        
        duration = int((now - started_at).total_seconds())
        
        # Use ensure_utc() to keep timezone info - Pydantic will serialize with +00:00
        # Frontend will correctly interpret as UTC
        return LiveStreamInfo(
            stream_id=str(event.id),
            account_id=str(account.id),
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            channel_thumbnail=account.thumbnail_url,
            title=event.title,
            description=event.description,
            youtube_broadcast_id=event.youtube_broadcast_id,
            viewer_count=event.peak_viewers or 0,  # Use peak as current (would need real-time API)
            peak_viewers=event.peak_viewers or 0,
            chat_messages=event.total_chat_messages or 0,
            likes=0,  # Would need real-time API
            started_at=ensure_utc(started_at),
            duration_seconds=max(0, duration),
            health_status=HealthStatus.HEALTHY,
        )

    def _build_scheduled_stream_info(self, event: LiveEvent, account: YouTubeAccount) -> ScheduledStreamInfo:
        """Build scheduled stream info from event and account."""
        now = utcnow()
        scheduled_at = ensure_utc(event.scheduled_start_at)
        
        starts_in = int((scheduled_at - now).total_seconds()) if scheduled_at else 0
        
        # Use ensure_utc() to keep timezone info - Pydantic will serialize with +00:00
        # Frontend will correctly interpret as UTC
        return ScheduledStreamInfo(
            stream_id=str(event.id),
            account_id=str(account.id),
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            channel_thumbnail=account.thumbnail_url,
            title=event.title,
            description=event.description,
            scheduled_start_at=ensure_utc(scheduled_at),
            scheduled_end_at=ensure_utc(event.scheduled_end_at),
            starts_in_seconds=max(0, starts_in),
        )

    def _determine_health_status(self, account: YouTubeAccount) -> HealthStatus:
        """Determine health status based on account state."""
        # Critical conditions
        if account.is_token_expired() if hasattr(account, 'is_token_expired') else False:
            return HealthStatus.CRITICAL
        if account.status == "error":
            return HealthStatus.CRITICAL
        
        # Warning conditions
        if account.is_token_expiring_soon(hours=24) if hasattr(account, 'is_token_expiring_soon') else False:
            return HealthStatus.WARNING
        quota_percent = account.get_quota_usage_percent() if hasattr(account, 'get_quota_usage_percent') else 0
        if quota_percent >= 80:
            return HealthStatus.WARNING
        
        return HealthStatus.HEALTHY

    def _count_alerts(self, account: YouTubeAccount) -> int:
        """Count number of alerts for an account."""
        count = 0
        
        if account.is_token_expired() if hasattr(account, 'is_token_expired') else False:
            count += 1
        elif account.is_token_expiring_soon(hours=24) if hasattr(account, 'is_token_expiring_soon') else False:
            count += 1
        
        if account.status == "error":
            count += 1
        
        quota_percent = account.get_quota_usage_percent() if hasattr(account, 'get_quota_usage_percent') else 0
        if quota_percent >= 80:
            count += 1
        
        return count

    def _generate_alerts(self, account: YouTubeAccount, status: ChannelStatusInfo) -> list[Alert]:
        """Generate alerts for a channel based on its status."""
        alerts = []
        now = utcnow()
        
        # Token expired
        if status.is_token_expired:
            alerts.append(Alert(
                id=f"token-expired-{account.id}",
                type=AlertType.TOKEN_EXPIRED,
                severity=AlertSeverity.CRITICAL,
                channel_id=account.channel_id,
                channel_title=account.channel_title,
                message="OAuth token has expired",
                details="Re-authenticate to restore access",
                created_at=now,
            ))
        # Token expiring soon
        elif status.is_token_expiring_soon:
            alerts.append(Alert(
                id=f"token-expiring-{account.id}",
                type=AlertType.TOKEN_EXPIRING,
                severity=AlertSeverity.WARNING,
                channel_id=account.channel_id,
                channel_title=account.channel_title,
                message="OAuth token expires within 24 hours",
                details="Re-authenticate soon to avoid interruption",
                created_at=now,
            ))
        
        # Account error
        if status.has_error:
            alerts.append(Alert(
                id=f"error-{account.id}",
                type=AlertType.ACCOUNT_ERROR,
                severity=AlertSeverity.CRITICAL,
                channel_id=account.channel_id,
                channel_title=account.channel_title,
                message="Account has an error",
                details=status.last_error,
                created_at=now,
            ))
        
        # Quota warnings
        if status.quota_percent >= 95:
            alerts.append(Alert(
                id=f"quota-critical-{account.id}",
                type=AlertType.QUOTA_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                channel_id=account.channel_id,
                channel_title=account.channel_title,
                message=f"API quota at {status.quota_percent:.0f}%",
                details="Quota will reset at midnight Pacific Time",
                created_at=now,
            ))
        elif status.quota_percent >= 80:
            alerts.append(Alert(
                id=f"quota-high-{account.id}",
                type=AlertType.QUOTA_HIGH,
                severity=AlertSeverity.WARNING,
                channel_id=account.channel_id,
                channel_title=account.channel_title,
                message=f"API quota at {status.quota_percent:.0f}%",
                details="Consider reducing API calls",
                created_at=now,
            ))
        
        return alerts

    def _build_overview(
        self,
        channels: list[ChannelStatusInfo],
        live_streams: list[LiveStreamInfo],
        scheduled_streams: list[ScheduledStreamInfo],
        alerts: list[Alert],
    ) -> MonitoringOverview:
        """Build overview statistics."""
        # Count by stream status
        live_count = sum(1 for c in channels if c.stream_status == StreamStatus.LIVE)
        scheduled_count = sum(1 for c in channels if c.stream_status == StreamStatus.SCHEDULED)
        offline_count = sum(1 for c in channels if c.stream_status == StreamStatus.OFFLINE)
        
        # Count by health status
        healthy_count = sum(1 for c in channels if c.health_status == HealthStatus.HEALTHY)
        warning_count = sum(1 for c in channels if c.health_status == HealthStatus.WARNING)
        critical_count = sum(1 for c in channels if c.health_status == HealthStatus.CRITICAL)
        
        # Total viewers
        total_viewers = sum(s.viewer_count for s in live_streams)
        
        # Scheduled today
        today = utcnow().date()
        scheduled_today = sum(
            1 for s in scheduled_streams 
            if s.scheduled_start_at and s.scheduled_start_at.date() == today
        )
        
        # Alert counts
        active_alerts = len(alerts)
        critical_alerts = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
        
        return MonitoringOverview(
            total_channels=len(channels),
            live_channels=live_count,
            scheduled_channels=scheduled_count,
            offline_channels=offline_count,
            healthy_channels=healthy_count,
            warning_channels=warning_count,
            critical_channels=critical_count,
            total_viewers=total_viewers,
            total_scheduled_today=scheduled_today,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
        )
