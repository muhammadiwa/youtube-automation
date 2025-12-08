"""Celery tasks for analytics report generation.

Implements background tasks for PDF/CSV report generation.
Requirements: 17.3, 17.4
"""

import csv
import io
import os
import uuid
from datetime import datetime

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import async_session_maker
from app.core.storage import storage_service


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

    async with async_session_maker() as session:
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
                    "generated_at": datetime.utcnow().isoformat(),
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
