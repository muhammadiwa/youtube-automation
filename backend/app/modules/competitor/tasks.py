"""Celery tasks for competitor module.

Implements background tasks for competitor sync, content checking, and notifications.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

import uuid
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import async_session_maker


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="competitor.sync_all_competitors",
)
def sync_all_competitors_task(self):
    """Sync metrics for all active competitors.

    This task should be scheduled to run periodically (e.g., daily).
    """
    import asyncio
    asyncio.run(_sync_all_competitors())


async def _sync_all_competitors():
    """Async implementation of sync all competitors."""
    from app.modules.competitor.repository import CompetitorRepository
    from app.modules.competitor.service import CompetitorService

    async with async_session_maker() as session:
        try:
            repo = CompetitorRepository(session)
            service = CompetitorService(session)

            # Get all active competitors
            # We need to get all users' competitors
            from sqlalchemy import select
            from app.modules.competitor.models import Competitor

            result = await session.execute(
                select(Competitor).where(Competitor.is_active == True)
            )
            competitors = list(result.scalars().all())

            for competitor in competitors:
                try:
                    await service.sync_competitor_metrics(competitor.id)
                except Exception as e:
                    # Log error but continue with other competitors
                    print(f"Failed to sync competitor {competitor.id}: {e}")

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="competitor.sync_competitor",
)
def sync_competitor_task(self, competitor_id: str):
    """Sync metrics for a single competitor.

    Args:
        competitor_id: Competitor UUID string
    """
    import asyncio
    asyncio.run(_sync_competitor(competitor_id))


async def _sync_competitor(competitor_id: str):
    """Async implementation of sync competitor."""
    from app.modules.competitor.service import CompetitorService

    async with async_session_maker() as session:
        try:
            service = CompetitorService(session)
            await service.sync_competitor_metrics(uuid.UUID(competitor_id))
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="competitor.check_new_content",
)
def check_new_content_task(self):
    """Check for new content from all competitors.

    This task should be scheduled to run periodically (e.g., every few hours).
    Detects new competitor content and creates notifications.
    Requirements: 19.3
    """
    import asyncio
    asyncio.run(_check_new_content())


async def _check_new_content():
    """Async implementation of check new content."""
    from app.modules.competitor.repository import CompetitorRepository
    from app.modules.competitor.service import CompetitorService

    async with async_session_maker() as session:
        try:
            repo = CompetitorRepository(session)
            service = CompetitorService(session)

            # Get competitors that need content checking
            competitors = await repo.get_for_content_check(check_interval_hours=24)

            for competitor in competitors:
                try:
                    new_content = await service.check_new_content(competitor.id)
                    if new_content:
                        # Queue notification task for each new content
                        for content in new_content:
                            send_content_notification_task.delay(str(content.id))
                except Exception as e:
                    # Log error but continue with other competitors
                    print(f"Failed to check content for {competitor.id}: {e}")

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="competitor.send_content_notification",
)
def send_content_notification_task(self, content_id: str):
    """Send notification for new competitor content.

    Args:
        content_id: CompetitorContent UUID string

    Requirements: 19.3 - Notify within 24 hours
    """
    import asyncio
    asyncio.run(_send_content_notification(content_id))


async def _send_content_notification(content_id: str):
    """Async implementation of send content notification."""
    from app.modules.competitor.repository import (
        CompetitorContentRepository,
        CompetitorRepository,
    )
    from app.modules.competitor.service import CompetitorService

    async with async_session_maker() as session:
        try:
            content_repo = CompetitorContentRepository(session)
            competitor_repo = CompetitorRepository(session)
            service = CompetitorService(session)

            # Get content
            content = await content_repo.get_by_id(uuid.UUID(content_id))
            if not content:
                return

            # Check if already notified
            if content.notification_sent:
                return

            # Get competitor
            competitor = await competitor_repo.get_by_id(content.competitor_id)
            if not competitor or not competitor.notify_on_new_content:
                return

            # Build notification data
            notification_data = {
                "type": "competitor_new_content",
                "competitor_id": str(competitor.id),
                "competitor_name": competitor.channel_title,
                "content_id": str(content.id),
                "video_id": content.video_id,
                "title": content.title,
                "thumbnail_url": content.thumbnail_url,
                "published_at": content.published_at.isoformat() if content.published_at else None,
                "content_type": content.content_type,
                "user_id": str(competitor.user_id),
            }

            # Send notification (integrate with notification service)
            # For now, we'll just mark as notified
            # In production, this would call the notification service
            await _send_notification(competitor.user_id, notification_data)

            # Mark content as notified
            await service.mark_content_notified(content.id)

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise


async def _send_notification(user_id: uuid.UUID, data: dict):
    """Send notification to user.

    Integrates with the notification service to send competitor updates.

    Args:
        user_id: User UUID
        data: Notification data
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.core.database import async_session_maker
        from app.modules.notification.integration import NotificationIntegrationService
        
        async with async_session_maker() as session:
            notification_service = NotificationIntegrationService(session)
            await notification_service.notify_competitor_update(
                user_id=user_id,
                competitor_name=data.get("competitor_name", "Unknown"),
                update_type=data.get("content_type", "new_content"),
                details=data.get("title", "New content published"),
            )
            logger.info(f"Competitor notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send competitor notification: {e}")


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="competitor.export_analysis",
)
def export_analysis_task(
    self,
    analysis_id: str,
    export_format: str,
    include_trend_data: bool = True,
    include_insights: bool = True,
):
    """Export competitor analysis to file.

    Args:
        analysis_id: CompetitorAnalysis UUID string
        export_format: Export format (pdf, csv, json)
        include_trend_data: Include trend data
        include_insights: Include AI insights

    Requirements: 19.5
    """
    import asyncio
    asyncio.run(_export_analysis(
        analysis_id, export_format, include_trend_data, include_insights
    ))


async def _export_analysis(
    analysis_id: str,
    export_format: str,
    include_trend_data: bool,
    include_insights: bool,
):
    """Async implementation of export analysis.

    Requirements: 19.5 - Export analysis with trend data and insights
    """
    from app.modules.competitor.repository import CompetitorAnalysisRepository
    from app.core.storage import storage_service

    async with async_session_maker() as session:
        try:
            repo = CompetitorAnalysisRepository(session)

            # Get analysis
            analysis = await repo.get_by_id(uuid.UUID(analysis_id))
            if not analysis:
                return

            # Generate export content based on format
            if export_format == "json":
                content = _generate_json_export(
                    analysis, include_trend_data, include_insights
                )
                content_type = "application/json"
                extension = "json"
            elif export_format == "csv":
                content = _generate_csv_export(
                    analysis, include_trend_data, include_insights
                )
                content_type = "text/csv"
                extension = "csv"
            elif export_format == "pdf":
                content = _generate_pdf_export(
                    analysis, include_trend_data, include_insights
                )
                content_type = "application/pdf"
                extension = "pdf"
            else:
                # Default to JSON for unknown formats
                content = _generate_json_export(
                    analysis, include_trend_data, include_insights
                )
                content_type = "application/json"
                extension = "json"

            # Save to storage
            filename = f"competitor_analysis_{analysis_id}.{extension}"
            file_path = f"exports/competitor/{filename}"

            # Upload to storage
            await storage_service.upload_file(
                file_path,
                content.encode() if isinstance(content, str) else content,
                content_type,
            )

            # Update analysis with export info
            await repo.update_export(analysis, file_path, export_format)

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise


def _generate_pdf_export(
    analysis,
    include_trend_data: bool,
    include_insights: bool,
) -> bytes:
    """Generate PDF export content with trend data and strategic insights.

    Args:
        analysis: CompetitorAnalysis instance
        include_trend_data: Include trend data
        include_insights: Include insights

    Returns:
        bytes: PDF content

    Requirements: 19.5 - Include trend data and insights
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, ListFlowable, ListItem
        )
    except ImportError:
        # Fallback to JSON if reportlab not available
        return _generate_json_export(analysis, include_trend_data, include_insights).encode()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a1a2e'),
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e'),
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#0f3460'),
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        leading=14,
    )

    story = []

    # Title
    story.append(Paragraph("Competitor Analysis Report", title_style))
    story.append(Spacer(1, 12))

    # Metadata table
    metadata = [
        ["Analysis Type:", analysis.analysis_type.title()],
        ["Period:", f"{analysis.start_date} to {analysis.end_date}"],
        ["Generated:", analysis.created_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["Competitors:", str(len(analysis.competitor_ids))],
    ]
    
    metadata_table = Table(metadata, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(analysis.summary, body_style))
    story.append(Spacer(1, 20))

    # Strategic Insights
    if include_insights and analysis.insights:
        story.append(Paragraph("Strategic Insights", heading_style))
        
        # Group insights by importance
        high_importance = [i for i in analysis.insights if i.get("importance") == "high"]
        medium_importance = [i for i in analysis.insights if i.get("importance") == "medium"]
        low_importance = [i for i in analysis.insights if i.get("importance") == "low"]
        
        for importance, insights in [("High Priority", high_importance), 
                                      ("Medium Priority", medium_importance),
                                      ("Low Priority", low_importance)]:
            if insights:
                story.append(Paragraph(importance, subheading_style))
                for insight in insights:
                    title = insight.get("title", "")
                    desc = insight.get("description", "")
                    metric_change = insight.get("metric_change")
                    
                    insight_text = f"<b>{title}</b>: {desc}"
                    if metric_change is not None:
                        change_color = "green" if metric_change > 0 else "red"
                        insight_text += f" (<font color='{change_color}'>{metric_change:+.1f}%</font>)"
                    
                    story.append(Paragraph(f"• {insight_text}", body_style))
        
        story.append(Spacer(1, 20))

    # Recommendations
    if include_insights and analysis.recommendations:
        story.append(Paragraph("Actionable Recommendations", heading_style))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_recs = sorted(
            analysis.recommendations,
            key=lambda x: priority_order.get(x.get("priority", "medium"), 1)
        )
        
        for i, rec in enumerate(sorted_recs, 1):
            priority = rec.get("priority", "medium").upper()
            title = rec.get("title", "")
            desc = rec.get("description", "")
            confidence = rec.get("confidence", 0) * 100
            
            story.append(Paragraph(
                f"<b>{i}. [{priority}] {title}</b>",
                subheading_style
            ))
            story.append(Paragraph(desc, body_style))
            
            # Action items
            action_items = rec.get("action_items", [])
            if action_items:
                story.append(Paragraph("<i>Action Items:</i>", body_style))
                for item in action_items:
                    story.append(Paragraph(f"  → {item}", body_style))
            
            impact = rec.get("estimated_impact")
            if impact:
                story.append(Paragraph(
                    f"<i>Estimated Impact:</i> {impact} (Confidence: {confidence:.0f}%)",
                    body_style
                ))
            
            story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))

    # Trend Data
    if include_trend_data and analysis.trend_data:
        story.append(PageBreak())
        story.append(Paragraph("Trend Analysis", heading_style))
        
        channels = analysis.trend_data.get("channels", [])
        
        if channels:
            # Summary table
            story.append(Paragraph("Channel Performance Summary", subheading_style))
            
            summary_data = [["Channel", "Subscribers", "Growth %", "Views", "Videos"]]
            
            for channel in channels:
                subscribers = channel.get("subscribers", [])
                views = channel.get("views", [])
                videos = channel.get("videos", [])
                
                end_subs = subscribers[-1] if subscribers else 0
                start_subs = subscribers[0] if subscribers else 0
                growth = ((end_subs - start_subs) / start_subs * 100) if start_subs > 0 else 0
                
                summary_data.append([
                    channel.get("channel_title", "")[:30],
                    f"{end_subs:,}",
                    f"{growth:+.1f}%",
                    f"{views[-1]:,}" if views else "0",
                    str(videos[-1]) if videos else "0",
                ])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1.2*inch, 0.8*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _generate_json_export(
    analysis,
    include_trend_data: bool,
    include_insights: bool,
) -> str:
    """Generate JSON export content with trend data and strategic insights.

    Args:
        analysis: CompetitorAnalysis instance
        include_trend_data: Include trend data
        include_insights: Include insights

    Returns:
        str: JSON string

    Requirements: 19.5 - Include trend data and insights
    """
    export_data = {
        "report_metadata": {
            "analysis_id": str(analysis.id),
            "analysis_type": analysis.analysis_type,
            "period": {
                "start_date": analysis.start_date.isoformat(),
                "end_date": analysis.end_date.isoformat(),
            },
            "generated_at": analysis.created_at.isoformat(),
            "competitor_count": len(analysis.competitor_ids),
        },
        "executive_summary": analysis.summary,
        "competitor_ids": analysis.competitor_ids,
    }

    if include_insights:
        # Organize insights by category for better readability
        categorized_insights = {}
        for insight in analysis.insights:
            category = insight.get("category", "general")
            if category not in categorized_insights:
                categorized_insights[category] = []
            categorized_insights[category].append({
                "title": insight.get("title", ""),
                "description": insight.get("description", ""),
                "importance": insight.get("importance", "medium"),
                "metric": {
                    "name": insight.get("metric_name"),
                    "value": insight.get("metric_value"),
                    "change": insight.get("metric_change"),
                } if insight.get("metric_name") else None,
            })
        export_data["insights"] = categorized_insights

        # Organize recommendations by priority
        prioritized_recommendations = {"high": [], "medium": [], "low": []}
        for rec in analysis.recommendations:
            priority = rec.get("priority", "medium")
            prioritized_recommendations[priority].append({
                "category": rec.get("category", ""),
                "title": rec.get("title", ""),
                "description": rec.get("description", ""),
                "action_items": rec.get("action_items", []),
                "estimated_impact": rec.get("estimated_impact"),
                "confidence": rec.get("confidence", 0.0),
            })
        export_data["strategic_recommendations"] = prioritized_recommendations

    if include_trend_data and analysis.trend_data:
        # Enhance trend data with calculated metrics
        enhanced_trend_data = _enhance_trend_data(analysis.trend_data)
        export_data["trend_analysis"] = enhanced_trend_data

    return json.dumps(export_data, indent=2, default=str)


def _enhance_trend_data(trend_data: dict) -> dict:
    """Enhance trend data with calculated metrics and analysis.

    Args:
        trend_data: Raw trend data

    Returns:
        dict: Enhanced trend data with additional metrics
    """
    enhanced = {"channels": [], "aggregate_metrics": {}}
    
    all_subscriber_growth = []
    all_view_growth = []
    
    for channel in trend_data.get("channels", []):
        subscribers = channel.get("subscribers", [])
        views = channel.get("views", [])
        videos = channel.get("videos", [])
        dates = channel.get("dates", [])
        
        # Calculate growth metrics
        subscriber_growth = 0.0
        view_growth = 0.0
        avg_daily_subscriber_change = 0.0
        avg_daily_view_change = 0.0
        
        if len(subscribers) >= 2 and subscribers[0] > 0:
            subscriber_growth = ((subscribers[-1] - subscribers[0]) / subscribers[0]) * 100
            avg_daily_subscriber_change = (subscribers[-1] - subscribers[0]) / max(len(subscribers) - 1, 1)
            all_subscriber_growth.append(subscriber_growth)
        
        if len(views) >= 2 and views[0] > 0:
            view_growth = ((views[-1] - views[0]) / views[0]) * 100
            avg_daily_view_change = (views[-1] - views[0]) / max(len(views) - 1, 1)
            all_view_growth.append(view_growth)
        
        # Calculate video publishing rate
        video_change = videos[-1] - videos[0] if len(videos) >= 2 else 0
        days = len(dates) if dates else 1
        publishing_rate = video_change / max(days, 1)
        
        enhanced_channel = {
            "channel_id": channel.get("channel_id", ""),
            "channel_title": channel.get("channel_title", ""),
            "time_series": {
                "dates": dates,
                "subscribers": subscribers,
                "views": views,
                "videos": videos,
            },
            "growth_metrics": {
                "subscriber_growth_percent": round(subscriber_growth, 2),
                "view_growth_percent": round(view_growth, 2),
                "avg_daily_subscriber_change": round(avg_daily_subscriber_change, 0),
                "avg_daily_view_change": round(avg_daily_view_change, 0),
                "videos_published": video_change,
                "publishing_rate_per_day": round(publishing_rate, 2),
            },
            "current_metrics": {
                "subscribers": subscribers[-1] if subscribers else 0,
                "views": views[-1] if views else 0,
                "videos": videos[-1] if videos else 0,
            },
        }
        enhanced["channels"].append(enhanced_channel)
    
    # Calculate aggregate metrics
    if all_subscriber_growth:
        enhanced["aggregate_metrics"]["avg_subscriber_growth"] = round(
            sum(all_subscriber_growth) / len(all_subscriber_growth), 2
        )
        enhanced["aggregate_metrics"]["max_subscriber_growth"] = round(max(all_subscriber_growth), 2)
        enhanced["aggregate_metrics"]["min_subscriber_growth"] = round(min(all_subscriber_growth), 2)
    
    if all_view_growth:
        enhanced["aggregate_metrics"]["avg_view_growth"] = round(
            sum(all_view_growth) / len(all_view_growth), 2
        )
    
    enhanced["aggregate_metrics"]["total_channels_analyzed"] = len(enhanced["channels"])
    
    return enhanced


def _generate_csv_export(
    analysis,
    include_trend_data: bool,
    include_insights: bool,
) -> str:
    """Generate CSV export content with trend data and strategic insights.

    Args:
        analysis: CompetitorAnalysis instance
        include_trend_data: Include trend data
        include_insights: Include insights

    Returns:
        str: CSV string

    Requirements: 19.5 - Include trend data and insights
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write report header
    writer.writerow(["=" * 60])
    writer.writerow(["COMPETITOR ANALYSIS REPORT"])
    writer.writerow(["=" * 60])
    writer.writerow([])
    writer.writerow(["Report Metadata"])
    writer.writerow(["Analysis ID", str(analysis.id)])
    writer.writerow(["Analysis Type", analysis.analysis_type])
    writer.writerow(["Period", f"{analysis.start_date} to {analysis.end_date}"])
    writer.writerow(["Generated", analysis.created_at.isoformat()])
    writer.writerow(["Competitors Analyzed", len(analysis.competitor_ids)])
    writer.writerow([])

    # Write executive summary
    writer.writerow(["-" * 60])
    writer.writerow(["EXECUTIVE SUMMARY"])
    writer.writerow(["-" * 60])
    writer.writerow([analysis.summary])
    writer.writerow([])

    # Write strategic insights
    if include_insights and analysis.insights:
        writer.writerow(["-" * 60])
        writer.writerow(["STRATEGIC INSIGHTS"])
        writer.writerow(["-" * 60])
        writer.writerow(["Category", "Title", "Description", "Importance", "Metric Name", "Metric Value", "Change %"])
        for insight in analysis.insights:
            writer.writerow([
                insight.get("category", ""),
                insight.get("title", ""),
                insight.get("description", ""),
                insight.get("importance", ""),
                insight.get("metric_name", ""),
                insight.get("metric_value", ""),
                insight.get("metric_change", ""),
            ])
        writer.writerow([])

    # Write actionable recommendations
    if include_insights and analysis.recommendations:
        writer.writerow(["-" * 60])
        writer.writerow(["ACTIONABLE RECOMMENDATIONS"])
        writer.writerow(["-" * 60])
        writer.writerow(["Priority", "Category", "Title", "Description", "Action Items", "Estimated Impact", "Confidence"])
        for rec in analysis.recommendations:
            action_items = "; ".join(rec.get("action_items", []))
            writer.writerow([
                rec.get("priority", ""),
                rec.get("category", ""),
                rec.get("title", ""),
                rec.get("description", ""),
                action_items,
                rec.get("estimated_impact", ""),
                f"{rec.get('confidence', 0) * 100:.0f}%",
            ])
        writer.writerow([])

    # Write trend data with growth analysis
    if include_trend_data and analysis.trend_data:
        writer.writerow(["-" * 60])
        writer.writerow(["TREND ANALYSIS"])
        writer.writerow(["-" * 60])
        writer.writerow([])
        
        channels = analysis.trend_data.get("channels", [])
        
        # Write summary table first
        writer.writerow(["Channel Performance Summary"])
        writer.writerow(["Channel", "Start Subscribers", "End Subscribers", "Growth %", "Start Views", "End Views", "View Growth %", "Videos Published"])
        
        for channel in channels:
            subscribers = channel.get("subscribers", [])
            views = channel.get("views", [])
            videos = channel.get("videos", [])
            
            start_subs = subscribers[0] if subscribers else 0
            end_subs = subscribers[-1] if subscribers else 0
            sub_growth = ((end_subs - start_subs) / start_subs * 100) if start_subs > 0 else 0
            
            start_views = views[0] if views else 0
            end_views = views[-1] if views else 0
            view_growth = ((end_views - start_views) / start_views * 100) if start_views > 0 else 0
            
            videos_published = (videos[-1] - videos[0]) if len(videos) >= 2 else 0
            
            writer.writerow([
                channel.get("channel_title", ""),
                start_subs,
                end_subs,
                f"{sub_growth:.2f}%",
                start_views,
                end_views,
                f"{view_growth:.2f}%",
                videos_published,
            ])
        writer.writerow([])
        
        # Write detailed time series for each channel
        for channel in channels:
            writer.writerow([f"Detailed Metrics: {channel.get('channel_title', '')}"])
            writer.writerow(["Date", "Subscribers", "Daily Sub Change", "Views", "Daily View Change", "Videos"])
            dates = channel.get("dates", [])
            subscribers = channel.get("subscribers", [])
            views = channel.get("views", [])
            videos = channel.get("videos", [])
            
            for i in range(len(dates)):
                sub_change = (subscribers[i] - subscribers[i-1]) if i > 0 and i < len(subscribers) else 0
                view_change = (views[i] - views[i-1]) if i > 0 and i < len(views) else 0
                
                writer.writerow([
                    dates[i] if i < len(dates) else "",
                    subscribers[i] if i < len(subscribers) else "",
                    sub_change,
                    views[i] if i < len(views) else "",
                    view_change,
                    videos[i] if i < len(videos) else "",
                ])
            writer.writerow([])

    writer.writerow(["=" * 60])
    writer.writerow(["END OF REPORT"])
    writer.writerow(["=" * 60])

    return output.getvalue()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="competitor.generate_ai_analysis",
)
def generate_ai_analysis_task(
    self,
    user_id: str,
    competitor_ids: list[str],
    analysis_type: str,
    start_date: str,
    end_date: str,
):
    """Generate AI-powered competitor analysis.

    Args:
        user_id: User UUID string
        competitor_ids: List of competitor UUID strings
        analysis_type: Type of analysis
        start_date: Start date ISO string
        end_date: End date ISO string

    Requirements: 19.4
    """
    import asyncio
    from datetime import date as date_type

    asyncio.run(_generate_ai_analysis(
        user_id,
        competitor_ids,
        analysis_type,
        date_type.fromisoformat(start_date),
        date_type.fromisoformat(end_date),
    ))


async def _generate_ai_analysis(
    user_id: str,
    competitor_ids: list[str],
    analysis_type: str,
    start_date,
    end_date,
):
    """Async implementation of generate AI analysis."""
    from app.modules.competitor.service import CompetitorService

    async with async_session_maker() as session:
        try:
            service = CompetitorService(session)

            await service.generate_analysis(
                user_id=uuid.UUID(user_id),
                competitor_ids=[uuid.UUID(cid) for cid in competitor_ids],
                analysis_type=analysis_type,
                start_date=start_date,
                end_date=end_date,
            )

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
