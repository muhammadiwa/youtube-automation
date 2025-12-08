"""Analytics service for business logic.

Implements dashboard metrics, period comparisons, and report generation.
Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsSnapshot, AnalyticsReport
from app.modules.analytics.repository import AnalyticsRepository, AnalyticsReportRepository
from app.modules.analytics.schemas import (
    DashboardMetrics,
    AccountMetrics,
    ChannelComparisonItem,
    ChannelComparisonResponse,
    AIInsight,
)


class AnalyticsServiceError(Exception):
    """Base exception for analytics service errors."""
    pass


class SnapshotNotFoundError(AnalyticsServiceError):
    """Raised when snapshot is not found."""
    pass


class ReportNotFoundError(AnalyticsServiceError):
    """Raised when report is not found."""
    pass


class InvalidDateRangeError(AnalyticsServiceError):
    """Raised when date range is invalid."""
    pass


def calculate_percent_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values.

    Args:
        current: Current value
        previous: Previous value

    Returns:
        float: Percentage change
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


def calculate_variance(value: float, average: float) -> float:
    """Calculate variance from average as percentage.

    Args:
        value: Individual value
        average: Average value

    Returns:
        float: Variance percentage
    """
    if average == 0:
        return 0.0
    return ((value - average) / average) * 100


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.snapshot_repo = AnalyticsRepository(session)
        self.report_repo = AnalyticsReportRepository(session)

    async def get_dashboard_metrics(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> DashboardMetrics:
        """Get aggregated dashboard metrics with period comparison.

        Args:
            user_id: User UUID
            start_date: Start of date range
            end_date: End of date range
            account_ids: Optional list of account IDs to filter

        Returns:
            DashboardMetrics: Aggregated metrics with comparisons
        """
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must be >= start_date")

        # Calculate comparison period (same duration, immediately before)
        period_days = (end_date - start_date).days + 1
        comparison_end = start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days - 1)

        # Get current period metrics
        current_metrics = await self.snapshot_repo.get_aggregated_metrics(
            start_date, end_date, account_ids
        )

        # Get comparison period metrics
        comparison_metrics = await self.snapshot_repo.get_aggregated_metrics(
            comparison_start, comparison_end, account_ids
        )

        # Calculate changes
        subscriber_change = (
            current_metrics["total_subscribers"] - comparison_metrics["total_subscribers"]
        )
        views_change = current_metrics["total_views"] - comparison_metrics["total_views"]
        revenue_change = current_metrics["total_revenue"] - comparison_metrics["total_revenue"]

        return DashboardMetrics(
            total_subscribers=current_metrics["total_subscribers"],
            total_views=current_metrics["total_views"],
            total_videos=current_metrics["total_videos"],
            total_revenue=current_metrics["total_revenue"],
            subscriber_change=subscriber_change,
            subscriber_change_percent=calculate_percent_change(
                current_metrics["total_subscribers"],
                comparison_metrics["total_subscribers"],
            ),
            views_change=views_change,
            views_change_percent=calculate_percent_change(
                current_metrics["total_views"],
                comparison_metrics["total_views"],
            ),
            revenue_change=revenue_change,
            revenue_change_percent=calculate_percent_change(
                current_metrics["total_revenue"],
                comparison_metrics["total_revenue"],
            ),
            total_likes=current_metrics["total_likes"],
            total_comments=current_metrics["total_comments"],
            average_engagement_rate=current_metrics["average_engagement_rate"],
            total_watch_time_minutes=current_metrics["total_watch_time_minutes"],
            start_date=start_date,
            end_date=end_date,
            comparison_start_date=comparison_start,
            comparison_end_date=comparison_end,
        )

    async def get_account_metrics(
        self,
        account_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> AccountMetrics:
        """Get metrics for a single account.

        Args:
            account_id: YouTube account UUID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            AccountMetrics: Account-specific metrics
        """
        snapshots = await self.snapshot_repo.get_by_account_date_range(
            account_id, start_date, end_date
        )

        if not snapshots:
            return AccountMetrics(account_id=account_id)

        # Get latest snapshot for current values
        latest = snapshots[-1]

        # Calculate totals and changes
        total_views = sum(s.total_views for s in snapshots)
        total_revenue = sum(s.estimated_revenue for s in snapshots)
        subscriber_change = sum(s.subscriber_change for s in snapshots)
        views_change = sum(s.views_change for s in snapshots)
        watch_time = sum(s.watch_time_minutes for s in snapshots)
        avg_engagement = (
            sum(s.engagement_rate for s in snapshots) / len(snapshots)
            if snapshots else 0.0
        )

        return AccountMetrics(
            account_id=account_id,
            subscriber_count=latest.subscriber_count,
            total_views=total_views,
            total_videos=latest.total_videos,
            estimated_revenue=total_revenue,
            subscriber_change=subscriber_change,
            views_change=views_change,
            revenue_change=total_revenue,  # For the period
            engagement_rate=avg_engagement,
            watch_time_minutes=watch_time,
        )

    async def compare_channels(
        self,
        account_ids: list[uuid.UUID],
        start_date: date,
        end_date: date,
    ) -> ChannelComparisonResponse:
        """Compare metrics across multiple channels.

        Args:
            account_ids: List of account IDs to compare
            start_date: Start of date range
            end_date: End of date range

        Returns:
            ChannelComparisonResponse: Comparison data with variance indicators
        """
        if len(account_ids) < 2:
            raise AnalyticsServiceError("At least 2 accounts required for comparison")

        # Get metrics for each account
        channel_metrics = []
        for account_id in account_ids:
            metrics = await self.get_account_metrics(account_id, start_date, end_date)
            channel_metrics.append(metrics)

        # Calculate averages
        avg_subscribers = (
            sum(m.subscriber_count for m in channel_metrics) / len(channel_metrics)
        )
        avg_views = sum(m.total_views for m in channel_metrics) / len(channel_metrics)
        avg_revenue = (
            sum(m.estimated_revenue for m in channel_metrics) / len(channel_metrics)
        )
        avg_engagement = (
            sum(m.engagement_rate for m in channel_metrics) / len(channel_metrics)
        )

        # Build comparison items with variance
        comparison_items = []
        for metrics in channel_metrics:
            item = ChannelComparisonItem(
                account_id=metrics.account_id,
                subscriber_count=metrics.subscriber_count,
                subscriber_change=metrics.subscriber_change,
                total_views=metrics.total_views,
                views_change=metrics.views_change,
                estimated_revenue=metrics.estimated_revenue,
                engagement_rate=metrics.engagement_rate,
                watch_time_minutes=metrics.watch_time_minutes,
                subscriber_variance=calculate_variance(
                    metrics.subscriber_count, avg_subscribers
                ),
                views_variance=calculate_variance(metrics.total_views, avg_views),
                revenue_variance=calculate_variance(
                    metrics.estimated_revenue, avg_revenue
                ),
                engagement_variance=calculate_variance(
                    metrics.engagement_rate, avg_engagement
                ),
            )
            comparison_items.append(item)

        return ChannelComparisonResponse(
            channels=comparison_items,
            start_date=start_date,
            end_date=end_date,
            average_subscribers=avg_subscribers,
            average_views=avg_views,
            average_revenue=avg_revenue,
            average_engagement=avg_engagement,
        )

    async def get_snapshots_by_date_range(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[AnalyticsSnapshot]:
        """Get snapshots within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            account_ids: Optional list of account IDs

        Returns:
            list[AnalyticsSnapshot]: Snapshots in the range
        """
        return await self.snapshot_repo.get_by_date_range(
            start_date, end_date, account_ids
        )

    async def create_snapshot(
        self,
        account_id: uuid.UUID,
        snapshot_date: date,
        **kwargs,
    ) -> AnalyticsSnapshot:
        """Create or update an analytics snapshot.

        Args:
            account_id: YouTube account UUID
            snapshot_date: Date for the snapshot
            **kwargs: Metrics data

        Returns:
            AnalyticsSnapshot: Created or updated snapshot
        """
        return await self.snapshot_repo.upsert(account_id, snapshot_date, **kwargs)


    async def create_report(
        self,
        user_id: uuid.UUID,
        title: str,
        report_type: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
        include_ai_insights: bool = True,
    ) -> AnalyticsReport:
        """Create a new analytics report.

        Args:
            user_id: User UUID
            title: Report title
            report_type: 'pdf' or 'csv'
            start_date: Start of date range
            end_date: End of date range
            account_ids: Optional list of account IDs
            include_ai_insights: Whether to include AI insights

        Returns:
            AnalyticsReport: Created report
        """
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must be >= start_date")

        report = await self.report_repo.create(
            user_id=user_id,
            title=title,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            account_ids=account_ids,
        )

        # Queue report generation task
        from app.modules.analytics.tasks import generate_report_task
        generate_report_task.delay(str(report.id), include_ai_insights)

        return report

    async def get_report(self, report_id: uuid.UUID) -> AnalyticsReport:
        """Get a report by ID.

        Args:
            report_id: Report UUID

        Returns:
            AnalyticsReport: Report instance

        Raises:
            ReportNotFoundError: If report not found
        """
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ReportNotFoundError(f"Report {report_id} not found")
        return report

    async def get_user_reports(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> list[AnalyticsReport]:
        """Get reports for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of reports

        Returns:
            list[AnalyticsReport]: User's reports
        """
        return await self.report_repo.get_by_user_id(user_id, limit)

    async def generate_ai_insights(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[AIInsight]:
        """Generate AI-powered insights for analytics data.

        Args:
            start_date: Start of date range
            end_date: End of date range
            account_ids: Optional list of account IDs

        Returns:
            list[AIInsight]: Generated insights
        """
        # Get metrics for the period
        current_metrics = await self.snapshot_repo.get_aggregated_metrics(
            start_date, end_date, account_ids
        )

        # Get comparison period
        period_days = (end_date - start_date).days + 1
        comparison_end = start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_days - 1)
        comparison_metrics = await self.snapshot_repo.get_aggregated_metrics(
            comparison_start, comparison_end, account_ids
        )

        insights = []

        # Subscriber growth insight
        sub_change_pct = calculate_percent_change(
            current_metrics["total_subscribers"],
            comparison_metrics["total_subscribers"],
        )
        if abs(sub_change_pct) > 5:
            direction = "increased" if sub_change_pct > 0 else "decreased"
            insights.append(AIInsight(
                category="growth",
                title=f"Subscriber Growth {direction.title()}",
                description=(
                    f"Your subscriber count has {direction} by {abs(sub_change_pct):.1f}% "
                    f"compared to the previous period."
                ),
                recommendation=(
                    "Continue creating engaging content to maintain growth momentum."
                    if sub_change_pct > 0 else
                    "Consider analyzing your recent content to identify what resonates with your audience."
                ),
                confidence=0.85,
                metric_change=sub_change_pct,
                metric_name="subscribers",
            ))

        # Views insight
        views_change_pct = calculate_percent_change(
            current_metrics["total_views"],
            comparison_metrics["total_views"],
        )
        if abs(views_change_pct) > 10:
            direction = "increased" if views_change_pct > 0 else "decreased"
            insights.append(AIInsight(
                category="engagement",
                title=f"View Count {direction.title()}",
                description=(
                    f"Total views have {direction} by {abs(views_change_pct):.1f}% "
                    f"compared to the previous period."
                ),
                recommendation=(
                    "Your content is gaining traction. Consider posting more frequently."
                    if views_change_pct > 0 else
                    "Review your thumbnails and titles to improve click-through rates."
                ),
                confidence=0.80,
                metric_change=views_change_pct,
                metric_name="views",
            ))

        # Revenue insight
        revenue_change_pct = calculate_percent_change(
            current_metrics["total_revenue"],
            comparison_metrics["total_revenue"],
        )
        if current_metrics["total_revenue"] > 0 and abs(revenue_change_pct) > 5:
            direction = "increased" if revenue_change_pct > 0 else "decreased"
            insights.append(AIInsight(
                category="revenue",
                title=f"Revenue {direction.title()}",
                description=(
                    f"Your estimated revenue has {direction} by {abs(revenue_change_pct):.1f}% "
                    f"compared to the previous period."
                ),
                recommendation=(
                    "Consider diversifying revenue streams with memberships or merchandise."
                    if revenue_change_pct > 0 else
                    "Focus on increasing watch time to improve ad revenue."
                ),
                confidence=0.75,
                metric_change=revenue_change_pct,
                metric_name="revenue",
            ))

        # Engagement insight
        if current_metrics["average_engagement_rate"] > 0:
            engagement_change = (
                current_metrics["average_engagement_rate"] -
                comparison_metrics["average_engagement_rate"]
            )
            if abs(engagement_change) > 0.5:
                direction = "improved" if engagement_change > 0 else "declined"
                insights.append(AIInsight(
                    category="engagement",
                    title=f"Engagement Rate {direction.title()}",
                    description=(
                        f"Your engagement rate has {direction} by {abs(engagement_change):.2f}% "
                        f"compared to the previous period."
                    ),
                    recommendation=(
                        "Your audience is more engaged. Keep up the interactive content!"
                        if engagement_change > 0 else
                        "Try adding more calls-to-action and engaging with comments."
                    ),
                    confidence=0.70,
                    metric_change=engagement_change,
                    metric_name="engagement_rate",
                ))

        return insights
