"""Celery tasks for analytics report generation and YouTube sync.

Implements background tasks for PDF/CSV report generation and analytics sync.
Requirements: 17.1, 17.2, 17.3, 17.4
"""

import csv
import io
import logging
import os
import uuid
from datetime import date, timedelta

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import celery_session_maker
from app.core.datetime_utils import utcnow
from app.core.storage import storage_service

logger = logging.getLogger(__name__)


# ============================================================================
# Analytics Sync Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_account_analytics(self, account_id: str):
    """Sync analytics data for a single YouTube account.

    Args:
        account_id: YouTube account UUID as string
    """
    import asyncio
    try:
        asyncio.run(_sync_account_analytics_async(account_id))
    except Exception as exc:
        logger.error(f"Failed to sync analytics for account {account_id}: {exc}")
        raise self.retry(exc=exc)


async def _sync_account_analytics_async(account_id: str):
    """Async implementation of single account analytics sync."""
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount
    from app.modules.analytics.youtube_api import YouTubeAnalyticsClient, YouTubeAnalyticsError
    from app.modules.analytics.repository import AnalyticsRepository
    from app.modules.account.service import AccountService

    async with celery_session_maker() as session:
        # Get account with token
        result = await session.execute(
            select(YouTubeAccount).where(YouTubeAccount.id == uuid.UUID(account_id))
        )
        account = result.scalar_one_or_none()

        if not account:
            logger.warning(f"Account {account_id} not found")
            return

        if account.status != "active":
            logger.info(f"Skipping inactive account {account_id}")
            return

        # Refresh token if needed
        account_service = AccountService(session)
        try:
            access_token = await account_service.get_valid_access_token(account)
        except Exception as e:
            logger.error(f"Failed to get valid token for account {account_id}: {e}")
            return

        # Initialize YouTube API client
        client = YouTubeAnalyticsClient(access_token)

        # Get date range (last 30 days)
        end_date = date.today() - timedelta(days=1)  # Yesterday (data may not be ready for today)
        start_date = end_date - timedelta(days=29)

        try:
            # Fetch channel statistics from Data API
            channel_stats = await client.get_channel_statistics(account.channel_id)
            
            # Fetch analytics from Analytics API
            analytics = await client.get_channel_analytics(
                account.channel_id, start_date, end_date
            )
            
            # Fetch traffic sources
            traffic_sources = await client.get_traffic_sources(
                account.channel_id, start_date, end_date
            )
            
            # Fetch demographics
            demographics = await client.get_demographics(
                account.channel_id, start_date, end_date
            )
            
            # Fetch top videos
            top_videos = await client.get_top_videos(
                account.channel_id, start_date, end_date, max_results=10
            )

            # Get previous snapshot for calculating changes
            repo = AnalyticsRepository(session)
            prev_snapshot = await repo.get_by_account_and_date(
                uuid.UUID(account_id), end_date - timedelta(days=1)
            )

            # Calculate changes
            subscriber_change = 0
            views_change = 0
            if prev_snapshot:
                subscriber_change = channel_stats["subscriber_count"] - prev_snapshot.subscriber_count
                views_change = analytics["views"] - prev_snapshot.total_views

            # Create or update snapshot for today
            snapshot = await repo.upsert(
                account_id=uuid.UUID(account_id),
                snapshot_date=end_date,
                subscriber_count=channel_stats["subscriber_count"],
                subscriber_change=subscriber_change,
                total_views=analytics["views"],
                views_change=views_change,
                total_videos=channel_stats["video_count"],
                total_likes=analytics["likes"],
                total_comments=analytics["comments"],
                total_shares=analytics.get("shares", 0),
                average_view_duration=analytics["average_view_duration"],
                watch_time_minutes=analytics["watch_time_minutes"],
                engagement_rate=_calculate_engagement_rate(
                    analytics["likes"], analytics["comments"], analytics["views"]
                ),
                traffic_sources=traffic_sources,
                demographics=demographics,
                top_videos=top_videos,
            )

            # Update account stats
            account.subscriber_count = channel_stats["subscriber_count"]
            account.video_count = channel_stats["video_count"]
            account.view_count = channel_stats["view_count"]
            account.last_sync_at = utcnow()
            account.last_error = None

            await session.commit()
            logger.info(f"Successfully synced analytics for account {account_id}")

        except YouTubeAnalyticsError as e:
            logger.error(f"YouTube API error for account {account_id}: {e}")
            account.last_error = str(e)
            await session.commit()
            raise


def _calculate_engagement_rate(likes: int, comments: int, views: int) -> float:
    """Calculate engagement rate as percentage."""
    if views == 0:
        return 0.0
    return ((likes + comments) / views) * 100


@celery_app.task(bind=True)
def sync_all_accounts_analytics(self):
    """Sync analytics for all active YouTube accounts.
    
    This task is scheduled to run daily.
    """
    import asyncio
    asyncio.run(_sync_all_accounts_async())


async def _sync_all_accounts_async():
    """Async implementation of all accounts analytics sync."""
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount

    async with celery_session_maker() as session:
        # Get all active accounts
        result = await session.execute(
            select(YouTubeAccount).where(YouTubeAccount.status == "active")
        )
        accounts = result.scalars().all()

        logger.info(f"Starting analytics sync for {len(accounts)} accounts")

        for account in accounts:
            # Queue individual sync task for each account
            sync_account_analytics.delay(str(account.id))

        logger.info(f"Queued analytics sync for {len(accounts)} accounts")


# ============================================================================
# Report Generation Tasks
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def generate_report_task(self, report_id: str, include_ai_insights: bool = True):
    """Generate analytics report in background.

    Args:
        report_id: Report UUID as string
        include_ai_insights: Whether to include AI insights
    """
    import asyncio
    asyncio.run(_generate_report_async(report_id, include_ai_insights))


async def _generate_report_async(report_id: str, include_ai_insights: bool):
    """Async implementation of report generation."""
    from app.modules.analytics.repository import (
        AnalyticsRepository,
        AnalyticsReportRepository,
    )
    from app.modules.analytics.service import AnalyticsService

    async with celery_session_maker() as session:
        report_repo = AnalyticsReportRepository(session)
        report = await report_repo.get_by_id(uuid.UUID(report_id))

        if not report:
            return

        try:
            # Update status to generating
            await report_repo.update_status(report, "generating")
            await session.commit()

            # Get analytics data
            service = AnalyticsService(session)
            account_ids = (
                [uuid.UUID(aid) for aid in report.account_ids]
                if report.account_ids else None
            )

            snapshots = await service.get_snapshots_by_date_range(
                report.start_date, report.end_date, account_ids
            )

            # Generate AI insights if requested
            ai_insights = None
            if include_ai_insights:
                insights = await service.generate_ai_insights(
                    report.start_date, report.end_date, account_ids
                )
                ai_insights = {
                    "insights": [
                        {
                            "category": i.category,
                            "title": i.title,
                            "description": i.description,
                            "recommendation": i.recommendation,
                            "confidence": i.confidence,
                            "metric_change": i.metric_change,
                            "metric_name": i.metric_name,
                        }
                        for i in insights
                    ],
                    "generated_at": utcnow().isoformat(),
                }

            # Generate report file
            if report.report_type == "csv":
                file_content, file_size = generate_csv_report(snapshots)
                file_ext = "csv"
            else:
                file_content, file_size = generate_pdf_report(
                    snapshots, ai_insights, report.title
                )
                file_ext = "pdf"

            # Save to storage
            file_name = f"reports/{report.user_id}/{report.id}.{file_ext}"
            file_path = await storage_service.save_file(
                file_content, file_name, f"application/{file_ext}"
            )

            # Update report with results
            await report_repo.update_status(
                report,
                status="completed",
                file_path=file_path,
                file_size=file_size,
                ai_insights=ai_insights,
            )
            await session.commit()

        except Exception as e:
            await report_repo.update_status(
                report,
                status="failed",
                error_message=str(e),
            )
            await session.commit()
            raise


def generate_csv_report(snapshots: list) -> tuple[bytes, int]:
    """Generate CSV report from snapshots.

    Args:
        snapshots: List of AnalyticsSnapshot objects

    Returns:
        tuple: (file content as bytes, file size)
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Date",
        "Account ID",
        "Subscribers",
        "Subscriber Change",
        "Views",
        "Views Change",
        "Videos",
        "Likes",
        "Comments",
        "Engagement Rate",
        "Watch Time (min)",
        "Revenue",
        "Ad Revenue",
        "Membership Revenue",
        "Super Chat Revenue",
        "Merchandise Revenue",
    ])

    # Data rows
    for snapshot in snapshots:
        writer.writerow([
            snapshot.snapshot_date.isoformat(),
            str(snapshot.account_id),
            snapshot.subscriber_count,
            snapshot.subscriber_change,
            snapshot.total_views,
            snapshot.views_change,
            snapshot.total_videos,
            snapshot.total_likes,
            snapshot.total_comments,
            f"{snapshot.engagement_rate:.2f}",
            snapshot.watch_time_minutes,
            f"{snapshot.estimated_revenue:.2f}",
            f"{snapshot.ad_revenue:.2f}",
            f"{snapshot.membership_revenue:.2f}",
            f"{snapshot.super_chat_revenue:.2f}",
            f"{snapshot.merchandise_revenue:.2f}",
        ])

    content = output.getvalue().encode("utf-8")
    return content, len(content)


def generate_pdf_report(
    snapshots: list,
    ai_insights: dict | None,
    title: str,
) -> tuple[bytes, int]:
    """Generate PDF report from snapshots.

    Note: This is a simplified implementation. In production,
    use a proper PDF library like reportlab or weasyprint.

    Args:
        snapshots: List of AnalyticsSnapshot objects
        ai_insights: AI-generated insights
        title: Report title

    Returns:
        tuple: (file content as bytes, file size)
    """
    # For now, generate a simple text-based report
    # In production, use reportlab or similar for proper PDF
    lines = []
    lines.append(f"Analytics Report: {title}")
    lines.append("=" * 50)
    lines.append("")

    if snapshots:
        lines.append(f"Period: {snapshots[0].snapshot_date} to {snapshots[-1].snapshot_date}")
        lines.append(f"Total Snapshots: {len(snapshots)}")
        lines.append("")

        # Summary
        total_views = sum(s.total_views for s in snapshots)
        total_revenue = sum(s.estimated_revenue for s in snapshots)
        avg_engagement = (
            sum(s.engagement_rate for s in snapshots) / len(snapshots)
            if snapshots else 0
        )

        lines.append("Summary")
        lines.append("-" * 30)
        lines.append(f"Total Views: {total_views:,}")
        lines.append(f"Total Revenue: ${total_revenue:,.2f}")
        lines.append(f"Average Engagement Rate: {avg_engagement:.2f}%")
        lines.append("")

    # AI Insights
    if ai_insights and ai_insights.get("insights"):
        lines.append("AI-Powered Insights")
        lines.append("-" * 30)
        for insight in ai_insights["insights"]:
            lines.append(f"\n{insight['title']}")
            lines.append(f"  {insight['description']}")
            if insight.get("recommendation"):
                lines.append(f"  Recommendation: {insight['recommendation']}")
        lines.append("")

    content = "\n".join(lines).encode("utf-8")
    return content, len(content)
