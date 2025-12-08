"""Competitor repository for database operations.

Implements CRUD operations for competitors, metrics, content, and analyses.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.competitor.models import (
    Competitor,
    CompetitorMetric,
    CompetitorContent,
    CompetitorAnalysis,
)


class CompetitorRepository:
    """Repository for Competitor CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        channel_id: str,
        channel_title: str,
        **kwargs,
    ) -> Competitor:
        """Create a new competitor.

        Args:
            user_id: User UUID
            channel_id: YouTube channel ID
            channel_title: Channel title
            **kwargs: Additional fields

        Returns:
            Competitor: Created competitor instance
        """
        competitor = Competitor(
            user_id=user_id,
            channel_id=channel_id,
            channel_title=channel_title,
            **kwargs,
        )
        self.session.add(competitor)
        await self.session.flush()
        return competitor

    async def get_by_id(self, competitor_id: uuid.UUID) -> Optional[Competitor]:
        """Get competitor by ID."""
        result = await self.session.execute(
            select(Competitor).where(Competitor.id == competitor_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_channel(
        self, user_id: uuid.UUID, channel_id: str
    ) -> Optional[Competitor]:
        """Get competitor by user and channel ID."""
        result = await self.session.execute(
            select(Competitor).where(
                and_(
                    Competitor.user_id == user_id,
                    Competitor.channel_id == channel_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        active_only: bool = False,
        limit: int = 100,
    ) -> list[Competitor]:
        """Get all competitors for a user.

        Args:
            user_id: User UUID
            active_only: Only return active competitors
            limit: Maximum number of results

        Returns:
            list[Competitor]: User's competitors
        """
        query = select(Competitor).where(Competitor.user_id == user_id)
        if active_only:
            query = query.where(Competitor.is_active == True)
        query = query.order_by(desc(Competitor.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_for_content_check(
        self, check_interval_hours: int = 24
    ) -> list[Competitor]:
        """Get competitors that need content checking.

        Args:
            check_interval_hours: Hours since last check

        Returns:
            list[Competitor]: Competitors needing content check
        """
        cutoff = datetime.utcnow().replace(
            hour=datetime.utcnow().hour - check_interval_hours
        )
        query = select(Competitor).where(
            and_(
                Competitor.is_active == True,
                Competitor.notify_on_new_content == True,
                (
                    (Competitor.last_content_check_at == None) |
                    (Competitor.last_content_check_at < cutoff)
                ),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, competitor: Competitor, **kwargs
    ) -> Competitor:
        """Update a competitor.

        Args:
            competitor: Competitor instance
            **kwargs: Fields to update

        Returns:
            Competitor: Updated competitor
        """
        for key, value in kwargs.items():
            if hasattr(competitor, key):
                setattr(competitor, key, value)
        await self.session.flush()
        return competitor

    async def delete(self, competitor: Competitor) -> None:
        """Delete a competitor."""
        await self.session.delete(competitor)
        await self.session.flush()


class CompetitorMetricRepository:
    """Repository for CompetitorMetric CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        competitor_id: uuid.UUID,
        metric_date: date,
        **kwargs,
    ) -> CompetitorMetric:
        """Create a new metric snapshot.

        Args:
            competitor_id: Competitor UUID
            metric_date: Date for the snapshot
            **kwargs: Metric values

        Returns:
            CompetitorMetric: Created metric instance
        """
        metric = CompetitorMetric(
            competitor_id=competitor_id,
            metric_date=metric_date,
            **kwargs,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_by_competitor_and_date(
        self, competitor_id: uuid.UUID, metric_date: date
    ) -> Optional[CompetitorMetric]:
        """Get metric for a specific competitor and date."""
        result = await self.session.execute(
            select(CompetitorMetric).where(
                and_(
                    CompetitorMetric.competitor_id == competitor_id,
                    CompetitorMetric.metric_date == metric_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        competitor_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[CompetitorMetric]:
        """Get metrics for a competitor within a date range.

        Args:
            competitor_id: Competitor UUID
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            list[CompetitorMetric]: Metrics within the date range
        """
        result = await self.session.execute(
            select(CompetitorMetric)
            .where(
                and_(
                    CompetitorMetric.competitor_id == competitor_id,
                    CompetitorMetric.metric_date >= start_date,
                    CompetitorMetric.metric_date <= end_date,
                )
            )
            .order_by(CompetitorMetric.metric_date)
        )
        return list(result.scalars().all())

    async def get_latest(
        self, competitor_id: uuid.UUID
    ) -> Optional[CompetitorMetric]:
        """Get the latest metric for a competitor."""
        result = await self.session.execute(
            select(CompetitorMetric)
            .where(CompetitorMetric.competitor_id == competitor_id)
            .order_by(desc(CompetitorMetric.metric_date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        competitor_id: uuid.UUID,
        metric_date: date,
        **kwargs,
    ) -> CompetitorMetric:
        """Create or update a metric for a competitor and date.

        Args:
            competitor_id: Competitor UUID
            metric_date: Date for the snapshot
            **kwargs: Metric values

        Returns:
            CompetitorMetric: Created or updated metric
        """
        existing = await self.get_by_competitor_and_date(competitor_id, metric_date)
        if existing:
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            return existing
        return await self.create(competitor_id, metric_date, **kwargs)


class CompetitorContentRepository:
    """Repository for CompetitorContent CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        competitor_id: uuid.UUID,
        video_id: str,
        title: str,
        published_at: datetime,
        **kwargs,
    ) -> CompetitorContent:
        """Create a new content item.

        Args:
            competitor_id: Competitor UUID
            video_id: YouTube video ID
            title: Video title
            published_at: Publication datetime
            **kwargs: Additional fields

        Returns:
            CompetitorContent: Created content instance
        """
        content = CompetitorContent(
            competitor_id=competitor_id,
            video_id=video_id,
            title=title,
            published_at=published_at,
            **kwargs,
        )
        self.session.add(content)
        await self.session.flush()
        return content

    async def get_by_id(self, content_id: uuid.UUID) -> Optional[CompetitorContent]:
        """Get content by ID."""
        result = await self.session.execute(
            select(CompetitorContent).where(CompetitorContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_by_competitor_and_video(
        self, competitor_id: uuid.UUID, video_id: str
    ) -> Optional[CompetitorContent]:
        """Get content by competitor and video ID."""
        result = await self.session.execute(
            select(CompetitorContent).where(
                and_(
                    CompetitorContent.competitor_id == competitor_id,
                    CompetitorContent.video_id == video_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_competitor(
        self,
        competitor_id: uuid.UUID,
        limit: int = 50,
    ) -> list[CompetitorContent]:
        """Get content for a competitor.

        Args:
            competitor_id: Competitor UUID
            limit: Maximum number of results

        Returns:
            list[CompetitorContent]: Competitor's content
        """
        result = await self.session.execute(
            select(CompetitorContent)
            .where(CompetitorContent.competitor_id == competitor_id)
            .order_by(desc(CompetitorContent.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_notifications(self) -> list[CompetitorContent]:
        """Get content items that need notification.

        Returns:
            list[CompetitorContent]: Content needing notification
        """
        result = await self.session.execute(
            select(CompetitorContent)
            .where(CompetitorContent.notification_sent == False)
            .order_by(CompetitorContent.discovered_at)
        )
        return list(result.scalars().all())

    async def mark_notified(
        self, content: CompetitorContent
    ) -> CompetitorContent:
        """Mark content as notified.

        Args:
            content: Content instance

        Returns:
            CompetitorContent: Updated content
        """
        content.notification_sent = True
        content.notification_sent_at = datetime.utcnow()
        await self.session.flush()
        return content

    async def exists(
        self, competitor_id: uuid.UUID, video_id: str
    ) -> bool:
        """Check if content already exists.

        Args:
            competitor_id: Competitor UUID
            video_id: YouTube video ID

        Returns:
            bool: True if content exists
        """
        result = await self.get_by_competitor_and_video(competitor_id, video_id)
        return result is not None


class CompetitorAnalysisRepository:
    """Repository for CompetitorAnalysis CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        competitor_ids: list[uuid.UUID],
        analysis_type: str,
        start_date: date,
        end_date: date,
        summary: str,
        insights: list,
        recommendations: list,
        **kwargs,
    ) -> CompetitorAnalysis:
        """Create a new analysis.

        Args:
            user_id: User UUID
            competitor_ids: List of competitor UUIDs
            analysis_type: Type of analysis
            start_date: Start of analysis period
            end_date: End of analysis period
            summary: Analysis summary
            insights: List of insights
            recommendations: List of recommendations
            **kwargs: Additional fields

        Returns:
            CompetitorAnalysis: Created analysis instance
        """
        analysis = CompetitorAnalysis(
            user_id=user_id,
            competitor_ids=[str(cid) for cid in competitor_ids],
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            completed_at=datetime.utcnow(),
            **kwargs,
        )
        self.session.add(analysis)
        await self.session.flush()
        return analysis

    async def get_by_id(self, analysis_id: uuid.UUID) -> Optional[CompetitorAnalysis]:
        """Get analysis by ID."""
        result = await self.session.execute(
            select(CompetitorAnalysis).where(CompetitorAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[CompetitorAnalysis]:
        """Get analyses for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of results

        Returns:
            list[CompetitorAnalysis]: User's analyses
        """
        result = await self.session.execute(
            select(CompetitorAnalysis)
            .where(CompetitorAnalysis.user_id == user_id)
            .order_by(desc(CompetitorAnalysis.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_export(
        self,
        analysis: CompetitorAnalysis,
        file_path: str,
        export_format: str,
    ) -> CompetitorAnalysis:
        """Update analysis with export info.

        Args:
            analysis: Analysis instance
            file_path: Path to exported file
            export_format: Export format

        Returns:
            CompetitorAnalysis: Updated analysis
        """
        analysis.export_file_path = file_path
        analysis.export_format = export_format
        await self.session.flush()
        return analysis

    async def delete(self, analysis: CompetitorAnalysis) -> None:
        """Delete an analysis."""
        await self.session.delete(analysis)
        await self.session.flush()
