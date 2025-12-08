"""Monitoring service for multi-channel dashboard.

Implements channel grid, filtering, and layout preferences.
Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import YouTubeAccount, AccountStatus
from app.modules.stream.models import LiveEvent, LiveEventStatus, StreamSession
from app.modules.monitoring.models import MonitoringLayoutPreference
from app.modules.monitoring.schemas import (
    ChannelStatusFilter,
    ChannelStatus,
    IssueSeverity,
    ChannelIssue,
    ChannelGridItem,
    ChannelGridResponse,
    ChannelDetailMetrics,
    StreamDetailInfo,
    StreamSummary,
    ScheduledStreamInfo,
    LayoutPreferences,
    LayoutPreferencesResponse,
)


class MonitoringService:
    """Service for multi-channel monitoring dashboard.
    
    Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel_grid(
        self,
        user_id: uuid.UUID,
        status_filter: ChannelStatusFilter = ChannelStatusFilter.ALL,
        search: Optional[str] = None,
        sort_by: str = "status",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 12,
    ) -> ChannelGridResponse:
        """Get channel grid with filtering support.
        
        Requirements: 16.1, 16.2
        
        Args:
            user_id: User ID to get channels for
            status_filter: Filter by channel status
            search: Search term for channel title
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            page: Page number
            page_size: Items per page
            
        Returns:
            ChannelGridResponse with filtered channels
        """
        # Get all accounts for user
        query = select(YouTubeAccount).where(YouTubeAccount.user_id == user_id)
        result = await self.session.execute(query)
        accounts = list(result.scalars().all())
        
        # Build channel grid items with status
        grid_items: list[ChannelGridItem] = []
        for account in accounts:
            item = await self._build_channel_grid_item(account)
            grid_items.append(item)
        
        total = len(grid_items)
        
        # Apply filters (Requirements: 16.2)
        filtered_items = self._apply_filters(
            grid_items, status_filter, search
        )
        
        filters_applied = []
        if status_filter != ChannelStatusFilter.ALL:
            filters_applied.append(f"status:{status_filter.value}")
        if search:
            filters_applied.append(f"search:{search}")
        
        # Sort items (Requirements: 16.3 - priority sorting for issues)
        sorted_items = self._sort_channels(filtered_items, sort_by, sort_order)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = sorted_items[start_idx:end_idx]
        
        return ChannelGridResponse(
            channels=paginated_items,
            total=total,
            filtered_count=len(filtered_items),
            filters_applied=filters_applied,
        )

    def _apply_filters(
        self,
        items: list[ChannelGridItem],
        status_filter: ChannelStatusFilter,
        search: Optional[str],
    ) -> list[ChannelGridItem]:
        """Apply filters to channel grid items.
        
        Requirements: 16.2
        """
        filtered = items
        
        # Filter by status
        if status_filter != ChannelStatusFilter.ALL:
            filtered = [
                item for item in filtered
                if self._matches_status_filter(item, status_filter)
            ]
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            filtered = [
                item for item in filtered
                if search_lower in item.channel_title.lower()
                or search_lower in item.channel_id.lower()
            ]
        
        return filtered

    def _matches_status_filter(
        self, item: ChannelGridItem, status_filter: ChannelStatusFilter
    ) -> bool:
        """Check if channel matches the status filter.
        
        Requirements: 16.2
        """
        if status_filter == ChannelStatusFilter.ALL:
            return True
        elif status_filter == ChannelStatusFilter.LIVE:
            return item.status == ChannelStatus.LIVE
        elif status_filter == ChannelStatusFilter.SCHEDULED:
            return item.status == ChannelStatus.SCHEDULED
        elif status_filter == ChannelStatusFilter.OFFLINE:
            return item.status == ChannelStatus.OFFLINE
        elif status_filter == ChannelStatusFilter.ERROR:
            return item.status == ChannelStatus.ERROR
        elif status_filter == ChannelStatusFilter.TOKEN_EXPIRED:
            return item.status == ChannelStatus.TOKEN_EXPIRED
        return True

    def _sort_channels(
        self,
        items: list[ChannelGridItem],
        sort_by: str,
        sort_order: str,
    ) -> list[ChannelGridItem]:
        """Sort channels with priority for critical issues.
        
        Requirements: 16.3 - Priority sorting
        """
        reverse = sort_order == "desc"
        
        # Always put critical issues first
        def sort_key(item: ChannelGridItem):
            # Priority: critical issues first, then by sort field
            priority = 0 if item.has_critical_issue else 1
            
            if sort_by == "status":
                status_order = {
                    ChannelStatus.ERROR: 0,
                    ChannelStatus.TOKEN_EXPIRED: 1,
                    ChannelStatus.LIVE: 2,
                    ChannelStatus.SCHEDULED: 3,
                    ChannelStatus.OFFLINE: 4,
                }
                return (priority, status_order.get(item.status, 5))
            elif sort_by == "subscribers":
                return (priority, -item.subscriber_count if not reverse else item.subscriber_count)
            elif sort_by == "views":
                return (priority, -item.view_count if not reverse else item.view_count)
            elif sort_by == "title":
                return (priority, item.channel_title.lower())
            elif sort_by == "quota":
                return (priority, -item.quota_usage_percent if not reverse else item.quota_usage_percent)
            else:
                return (priority, item.channel_title.lower())
        
        return sorted(items, key=sort_key, reverse=reverse and sort_by not in ["status"])

    async def _build_channel_grid_item(
        self, account: YouTubeAccount
    ) -> ChannelGridItem:
        """Build a channel grid item from account data.
        
        Requirements: 16.1, 16.3
        """
        # Determine channel status
        status = await self._determine_channel_status(account)
        
        # Get current stream info if live
        current_stream = await self._get_current_stream(account.id)
        
        # Get next scheduled stream
        next_scheduled = await self._get_next_scheduled_stream(account.id)
        
        # Detect issues (Requirements: 16.3)
        issues = self._detect_channel_issues(account, status)
        has_critical = any(i.severity == IssueSeverity.CRITICAL for i in issues)
        
        return ChannelGridItem(
            account_id=account.id,
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            thumbnail_url=account.thumbnail_url,
            subscriber_count=account.subscriber_count,
            video_count=account.video_count,
            view_count=account.view_count,
            status=status,
            is_monetized=account.is_monetized,
            has_live_streaming_enabled=account.has_live_streaming_enabled,
            strike_count=account.strike_count,
            token_expires_at=account.token_expires_at,
            is_token_expired=account.is_token_expired(),
            is_token_expiring_soon=account.is_token_expiring_soon(hours=24),
            daily_quota_used=account.daily_quota_used,
            quota_usage_percent=account.get_quota_usage_percent(),
            current_stream_id=current_stream.get("id") if current_stream else None,
            current_stream_title=current_stream.get("title") if current_stream else None,
            current_viewer_count=current_stream.get("viewer_count") if current_stream else None,
            stream_started_at=current_stream.get("started_at") if current_stream else None,
            next_scheduled_stream_id=next_scheduled.get("id") if next_scheduled else None,
            next_scheduled_stream_title=next_scheduled.get("title") if next_scheduled else None,
            next_scheduled_at=next_scheduled.get("scheduled_at") if next_scheduled else None,
            has_critical_issue=has_critical,
            issues=issues,
            last_sync_at=account.last_sync_at,
            last_error=account.last_error,
        )

    async def _determine_channel_status(
        self, account: YouTubeAccount
    ) -> ChannelStatus:
        """Determine the current status of a channel."""
        # Check for token expiry first
        if account.is_token_expired():
            return ChannelStatus.TOKEN_EXPIRED
        
        # Check for error status
        if account.status == AccountStatus.ERROR.value:
            return ChannelStatus.ERROR
        
        # Check if currently live
        live_query = select(LiveEvent).where(
            and_(
                LiveEvent.account_id == account.id,
                LiveEvent.status == LiveEventStatus.LIVE.value,
            )
        )
        result = await self.session.execute(live_query)
        if result.scalar_one_or_none():
            return ChannelStatus.LIVE
        
        # Check for scheduled streams
        now = datetime.utcnow()
        scheduled_query = select(LiveEvent).where(
            and_(
                LiveEvent.account_id == account.id,
                LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                LiveEvent.scheduled_start_at > now,
            )
        )
        result = await self.session.execute(scheduled_query)
        if result.scalar_one_or_none():
            return ChannelStatus.SCHEDULED
        
        return ChannelStatus.OFFLINE

    async def _get_current_stream(
        self, account_id: uuid.UUID
    ) -> Optional[dict]:
        """Get current live stream info for an account."""
        query = select(LiveEvent).where(
            and_(
                LiveEvent.account_id == account_id,
                LiveEvent.status == LiveEventStatus.LIVE.value,
            )
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return None
        
        return {
            "id": event.id,
            "title": event.title,
            "viewer_count": event.peak_viewers,
            "started_at": event.actual_start_at,
        }

    async def _get_next_scheduled_stream(
        self, account_id: uuid.UUID
    ) -> Optional[dict]:
        """Get next scheduled stream for an account."""
        now = datetime.utcnow()
        query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account_id,
                    LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                    LiveEvent.scheduled_start_at > now,
                )
            )
            .order_by(LiveEvent.scheduled_start_at.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return None
        
        return {
            "id": event.id,
            "title": event.title,
            "scheduled_at": event.scheduled_start_at,
        }

    def _detect_channel_issues(
        self, account: YouTubeAccount, status: ChannelStatus
    ) -> list[ChannelIssue]:
        """Detect issues with a channel.
        
        Requirements: 16.3
        """
        issues = []
        now = datetime.utcnow()
        
        # Critical: Token expired
        if account.is_token_expired():
            issues.append(ChannelIssue(
                severity=IssueSeverity.CRITICAL,
                message="OAuth token has expired. Re-authentication required.",
                detected_at=now,
            ))
        
        # Critical: Account error
        if account.status == AccountStatus.ERROR.value:
            issues.append(ChannelIssue(
                severity=IssueSeverity.CRITICAL,
                message=f"Account error: {account.last_error or 'Unknown error'}",
                detected_at=now,
            ))
        
        # Critical: Strike detected
        if account.strike_count > 0:
            issues.append(ChannelIssue(
                severity=IssueSeverity.CRITICAL,
                message=f"Channel has {account.strike_count} active strike(s)",
                detected_at=now,
            ))
        
        # Warning: Token expiring soon
        if not account.is_token_expired() and account.is_token_expiring_soon(hours=24):
            issues.append(ChannelIssue(
                severity=IssueSeverity.WARNING,
                message="OAuth token expires within 24 hours",
                detected_at=now,
            ))
        
        # Warning: High quota usage
        quota_percent = account.get_quota_usage_percent()
        if quota_percent >= 90:
            issues.append(ChannelIssue(
                severity=IssueSeverity.WARNING,
                message=f"API quota usage at {quota_percent:.1f}%",
                detected_at=now,
            ))
        elif quota_percent >= 80:
            issues.append(ChannelIssue(
                severity=IssueSeverity.INFO,
                message=f"API quota usage approaching limit ({quota_percent:.1f}%)",
                detected_at=now,
            ))
        
        return issues

    async def get_channel_details(
        self, account_id: uuid.UUID
    ) -> Optional[ChannelDetailMetrics]:
        """Get detailed metrics for a channel.
        
        Requirements: 16.4
        """
        # Get account
        query = select(YouTubeAccount).where(YouTubeAccount.id == account_id)
        result = await self.session.execute(query)
        account = result.scalar_one_or_none()
        
        if not account:
            return None
        
        status = await self._determine_channel_status(account)
        issues = self._detect_channel_issues(account, status)
        
        # Get current stream details
        current_stream = await self._get_current_stream_details(account_id)
        
        # Get recent streams
        recent_streams = await self._get_recent_streams(account_id, limit=5)
        
        # Get scheduled streams
        scheduled_streams = await self._get_scheduled_streams(account_id, limit=5)
        
        return ChannelDetailMetrics(
            account_id=account.id,
            channel_id=account.channel_id,
            channel_title=account.channel_title,
            thumbnail_url=account.thumbnail_url,
            subscriber_count=account.subscriber_count,
            video_count=account.video_count,
            view_count=account.view_count,
            is_monetized=account.is_monetized,
            status=status,
            strike_count=account.strike_count,
            token_expires_at=account.token_expires_at,
            is_token_expired=account.is_token_expired(),
            is_token_expiring_soon=account.is_token_expiring_soon(hours=24),
            daily_quota_used=account.daily_quota_used,
            daily_quota_limit=10000,
            quota_usage_percent=account.get_quota_usage_percent(),
            quota_reset_at=account.quota_reset_at,
            current_stream=current_stream,
            recent_streams=recent_streams,
            scheduled_streams=scheduled_streams,
            issues=issues,
            last_sync_at=account.last_sync_at,
            created_at=account.created_at,
        )

    async def _get_current_stream_details(
        self, account_id: uuid.UUID
    ) -> Optional[StreamDetailInfo]:
        """Get detailed info about current live stream."""
        query = select(LiveEvent).where(
            and_(
                LiveEvent.account_id == account_id,
                LiveEvent.status == LiveEventStatus.LIVE.value,
            )
        )
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event or not event.actual_start_at:
            return None
        
        duration = int((datetime.utcnow() - event.actual_start_at.replace(tzinfo=None)).total_seconds())
        
        return StreamDetailInfo(
            stream_id=event.id,
            title=event.title,
            viewer_count=event.peak_viewers,
            peak_viewers=event.peak_viewers,
            chat_messages=event.total_chat_messages,
            started_at=event.actual_start_at,
            duration_seconds=duration,
            health_status="good",
        )

    async def _get_recent_streams(
        self, account_id: uuid.UUID, limit: int = 5
    ) -> list[StreamSummary]:
        """Get recent completed streams."""
        query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account_id,
                    LiveEvent.status == LiveEventStatus.ENDED.value,
                )
            )
            .order_by(LiveEvent.actual_end_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        summaries = []
        for event in events:
            if event.actual_start_at:
                duration = 0
                if event.actual_end_at:
                    duration = int((event.actual_end_at - event.actual_start_at).total_seconds())
                summaries.append(StreamSummary(
                    stream_id=event.id,
                    title=event.title,
                    started_at=event.actual_start_at,
                    ended_at=event.actual_end_at,
                    duration_seconds=duration,
                    peak_viewers=event.peak_viewers,
                    total_chat_messages=event.total_chat_messages,
                ))
        
        return summaries

    async def _get_scheduled_streams(
        self, account_id: uuid.UUID, limit: int = 5
    ) -> list[ScheduledStreamInfo]:
        """Get upcoming scheduled streams."""
        now = datetime.utcnow()
        query = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.account_id == account_id,
                    LiveEvent.status == LiveEventStatus.SCHEDULED.value,
                    LiveEvent.scheduled_start_at > now,
                )
            )
            .order_by(LiveEvent.scheduled_start_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        events = result.scalars().all()
        
        return [
            ScheduledStreamInfo(
                stream_id=event.id,
                title=event.title,
                scheduled_start_at=event.scheduled_start_at,
                scheduled_end_at=event.scheduled_end_at,
            )
            for event in events
            if event.scheduled_start_at
        ]

    async def get_layout_preferences(
        self, user_id: uuid.UUID
    ) -> LayoutPreferencesResponse:
        """Get user's layout preferences.
        
        Requirements: 16.5
        """
        query = select(MonitoringLayoutPreference).where(
            MonitoringLayoutPreference.user_id == user_id
        )
        result = await self.session.execute(query)
        pref = result.scalar_one_or_none()
        
        if not pref:
            # Return defaults
            return LayoutPreferencesResponse(
                user_id=user_id,
                preferences=LayoutPreferences(),
                updated_at=datetime.utcnow(),
            )
        
        return LayoutPreferencesResponse(
            user_id=user_id,
            preferences=LayoutPreferences(
                grid_columns=pref.grid_columns,
                grid_rows=pref.grid_rows,
                show_metrics=pref.show_metrics,
                sort_by=pref.sort_by,
                sort_order=pref.sort_order,
                default_filter=ChannelStatusFilter(pref.default_filter),
                compact_mode=pref.compact_mode,
                show_issues_only=pref.show_issues_only,
            ),
            updated_at=pref.updated_at,
        )

    async def update_layout_preferences(
        self,
        user_id: uuid.UUID,
        updates: dict,
    ) -> LayoutPreferencesResponse:
        """Update user's layout preferences.
        
        Requirements: 16.5
        """
        query = select(MonitoringLayoutPreference).where(
            MonitoringLayoutPreference.user_id == user_id
        )
        result = await self.session.execute(query)
        pref = result.scalar_one_or_none()
        
        if not pref:
            # Create new preferences
            pref = MonitoringLayoutPreference(user_id=user_id)
            self.session.add(pref)
        
        # Apply updates
        for key, value in updates.items():
            if value is not None and hasattr(pref, key):
                if key == "default_filter" and isinstance(value, ChannelStatusFilter):
                    setattr(pref, key, value.value)
                else:
                    setattr(pref, key, value)
        
        await self.session.flush()
        
        return await self.get_layout_preferences(user_id)
