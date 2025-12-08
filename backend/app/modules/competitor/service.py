"""Competitor service for business logic.

Implements competitor tracking, comparison, and analysis.
Requirements: 19.1, 19.2, 19.3, 19.4, 19.5
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.competitor.models import (
    Competitor,
    CompetitorMetric,
    CompetitorContent,
    CompetitorAnalysis,
)
from app.modules.competitor.repository import (
    CompetitorRepository,
    CompetitorMetricRepository,
    CompetitorContentRepository,
    CompetitorAnalysisRepository,
)
from app.modules.competitor.youtube_api import (
    YouTubeCompetitorAPI,
    ChannelNotFoundError,
    YouTubeAPIError,
)
from app.modules.competitor.schemas import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    CompetitorTrendData,
    ComparisonChannelData,
    ComparisonResponse,
    AnalysisInsight,
    AnalysisRecommendation,
)


class CompetitorServiceError(Exception):
    """Base exception for competitor service errors."""
    pass


class CompetitorNotFoundError(CompetitorServiceError):
    """Raised when competitor is not found."""
    pass


class CompetitorAlreadyExistsError(CompetitorServiceError):
    """Raised when competitor already exists."""
    pass


class InvalidDateRangeError(CompetitorServiceError):
    """Raised when date range is invalid."""
    pass


def calculate_variance(value: float, average: float) -> float:
    """Calculate variance from average as percentage."""
    if average == 0:
        return 0.0
    return ((value - average) / average) * 100


def calculate_growth_rate(current: int, previous: int) -> float:
    """Calculate growth rate as percentage."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


class CompetitorService:
    """Service for competitor operations."""

    def __init__(
        self,
        session: AsyncSession,
        youtube_api: Optional[YouTubeCompetitorAPI] = None,
    ):
        """Initialize service with database session."""
        self.session = session
        self.competitor_repo = CompetitorRepository(session)
        self.metric_repo = CompetitorMetricRepository(session)
        self.content_repo = CompetitorContentRepository(session)
        self.analysis_repo = CompetitorAnalysisRepository(session)
        self._youtube_api = youtube_api

    @property
    def youtube_api(self) -> YouTubeCompetitorAPI:
        """Get YouTube API client."""
        if self._youtube_api is None:
            self._youtube_api = YouTubeCompetitorAPI()
        return self._youtube_api

    # ============================================
    # Competitor CRUD Operations
    # ============================================

    async def add_competitor(
        self,
        user_id: uuid.UUID,
        data: CompetitorCreate,
    ) -> Competitor:
        """Add a new competitor to track.

        Args:
            user_id: User UUID
            data: Competitor creation data

        Returns:
            Competitor: Created competitor

        Raises:
            CompetitorAlreadyExistsError: If competitor already exists
            ChannelNotFoundError: If channel not found on YouTube
        """
        # Check if already tracking this channel
        existing = await self.competitor_repo.get_by_user_and_channel(
            user_id, data.channel_id
        )
        if existing:
            raise CompetitorAlreadyExistsError(
                f"Already tracking channel: {data.channel_id}"
            )

        # Fetch channel data from YouTube
        try:
            channel_data = await self.youtube_api.get_channel_by_id(data.channel_id)
        except ChannelNotFoundError:
            raise
        except YouTubeAPIError as e:
            raise CompetitorServiceError(f"Failed to fetch channel: {str(e)}")

        # Create competitor
        competitor = await self.competitor_repo.create(
            user_id=user_id,
            channel_id=channel_data.channel_id,
            channel_title=channel_data.title,
            channel_description=channel_data.description,
            thumbnail_url=channel_data.thumbnail_url,
            custom_url=channel_data.custom_url,
            country=channel_data.country,
            subscriber_count=channel_data.subscriber_count,
            video_count=channel_data.video_count,
            view_count=channel_data.view_count,
            notes=data.notes,
            tags=data.tags,
            notify_on_new_content=data.notify_on_new_content,
            notify_on_milestone=data.notify_on_milestone,
            last_synced_at=datetime.utcnow(),
        )

        # Create initial metric snapshot
        await self.metric_repo.create(
            competitor_id=competitor.id,
            metric_date=date.today(),
            subscriber_count=channel_data.subscriber_count,
            video_count=channel_data.video_count,
            view_count=channel_data.view_count,
        )

        return competitor

    async def get_competitor(self, competitor_id: uuid.UUID) -> Competitor:
        """Get a competitor by ID.

        Args:
            competitor_id: Competitor UUID

        Returns:
            Competitor: Competitor instance

        Raises:
            CompetitorNotFoundError: If competitor not found
        """
        competitor = await self.competitor_repo.get_by_id(competitor_id)
        if not competitor:
            raise CompetitorNotFoundError(f"Competitor not found: {competitor_id}")
        return competitor

    async def get_user_competitors(
        self,
        user_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[Competitor]:
        """Get all competitors for a user.

        Args:
            user_id: User UUID
            active_only: Only return active competitors

        Returns:
            list[Competitor]: User's competitors
        """
        return await self.competitor_repo.get_by_user(user_id, active_only)

    async def update_competitor(
        self,
        competitor_id: uuid.UUID,
        data: CompetitorUpdate,
    ) -> Competitor:
        """Update a competitor.

        Args:
            competitor_id: Competitor UUID
            data: Update data

        Returns:
            Competitor: Updated competitor

        Raises:
            CompetitorNotFoundError: If competitor not found
        """
        competitor = await self.get_competitor(competitor_id)

        update_data = data.model_dump(exclude_unset=True)
        return await self.competitor_repo.update(competitor, **update_data)

    async def remove_competitor(self, competitor_id: uuid.UUID) -> None:
        """Remove a competitor.

        Args:
            competitor_id: Competitor UUID

        Raises:
            CompetitorNotFoundError: If competitor not found
        """
        competitor = await self.get_competitor(competitor_id)
        await self.competitor_repo.delete(competitor)

    # ============================================
    # Metrics and Tracking
    # ============================================

    async def sync_competitor_metrics(
        self, competitor_id: uuid.UUID
    ) -> Competitor:
        """Sync metrics for a competitor from YouTube.

        Args:
            competitor_id: Competitor UUID

        Returns:
            Competitor: Updated competitor

        Raises:
            CompetitorNotFoundError: If competitor not found
        """
        competitor = await self.get_competitor(competitor_id)

        try:
            channel_data = await self.youtube_api.get_channel_by_id(
                competitor.channel_id
            )
        except YouTubeAPIError as e:
            await self.competitor_repo.update(
                competitor, sync_error=str(e)
            )
            raise CompetitorServiceError(f"Failed to sync: {str(e)}")

        # Get previous metrics for change calculation
        previous_metric = await self.metric_repo.get_latest(competitor_id)

        subscriber_change = 0
        video_change = 0
        view_change = 0

        if previous_metric:
            subscriber_change = (
                channel_data.subscriber_count - previous_metric.subscriber_count
            )
            video_change = channel_data.video_count - previous_metric.video_count
            view_change = channel_data.view_count - previous_metric.view_count

        # Update competitor
        competitor = await self.competitor_repo.update(
            competitor,
            channel_title=channel_data.title,
            channel_description=channel_data.description,
            thumbnail_url=channel_data.thumbnail_url,
            subscriber_count=channel_data.subscriber_count,
            video_count=channel_data.video_count,
            view_count=channel_data.view_count,
            last_synced_at=datetime.utcnow(),
            sync_error=None,
        )

        # Create or update today's metric
        avg_views = (
            channel_data.view_count / channel_data.video_count
            if channel_data.video_count > 0 else 0.0
        )

        await self.metric_repo.upsert(
            competitor_id=competitor_id,
            metric_date=date.today(),
            subscriber_count=channel_data.subscriber_count,
            subscriber_change=subscriber_change,
            video_count=channel_data.video_count,
            video_change=video_change,
            view_count=channel_data.view_count,
            view_change=view_change,
            avg_views_per_video=avg_views,
        )

        return competitor

    async def get_competitor_metrics(
        self,
        competitor_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[CompetitorMetric]:
        """Get metrics for a competitor within a date range.

        Args:
            competitor_id: Competitor UUID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            list[CompetitorMetric]: Metrics within the range
        """
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must be >= start_date")

        return await self.metric_repo.get_by_date_range(
            competitor_id, start_date, end_date
        )

    async def get_trend_data(
        self,
        competitor_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> CompetitorTrendData:
        """Get trend data for a competitor.

        Args:
            competitor_id: Competitor UUID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            CompetitorTrendData: Trend data for charts
        """
        competitor = await self.get_competitor(competitor_id)
        metrics = await self.get_competitor_metrics(
            competitor_id, start_date, end_date
        )

        return CompetitorTrendData(
            competitor_id=competitor_id,
            channel_title=competitor.channel_title,
            dates=[m.metric_date for m in metrics],
            subscriber_counts=[m.subscriber_count for m in metrics],
            view_counts=[m.view_count for m in metrics],
            video_counts=[m.video_count for m in metrics],
            subscriber_changes=[m.subscriber_change for m in metrics],
            view_changes=[m.view_change for m in metrics],
        )

    # ============================================
    # Comparison
    # ============================================

    async def compare_channels(
        self,
        user_id: uuid.UUID,
        competitor_ids: list[uuid.UUID],
        account_ids: Optional[list[uuid.UUID]],
        start_date: date,
        end_date: date,
    ) -> ComparisonResponse:
        """Compare competitors with optional user accounts.

        Args:
            user_id: User UUID
            competitor_ids: List of competitor UUIDs
            account_ids: Optional list of user's account UUIDs
            start_date: Start of date range
            end_date: End of date range

        Returns:
            ComparisonResponse: Comparison data
        """
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must be >= start_date")

        channels: list[ComparisonChannelData] = []

        # Get competitor data
        for comp_id in competitor_ids:
            try:
                competitor = await self.get_competitor(comp_id)
                metrics = await self.get_competitor_metrics(
                    comp_id, start_date, end_date
                )

                # Calculate period totals
                subscriber_change = sum(m.subscriber_change for m in metrics)
                view_change = sum(m.view_change for m in metrics)
                videos_published = sum(m.video_change for m in metrics)

                # Get latest metrics
                latest = metrics[-1] if metrics else None
                subscriber_count = latest.subscriber_count if latest else competitor.subscriber_count
                view_count = latest.view_count if latest else competitor.view_count
                video_count = latest.video_count if latest else competitor.video_count

                # Calculate growth rate
                first = metrics[0] if metrics else None
                growth_rate = 0.0
                if first and first.subscriber_count > 0:
                    growth_rate = calculate_growth_rate(
                        subscriber_count, first.subscriber_count
                    )

                avg_views = view_count / video_count if video_count > 0 else 0.0

                channels.append(ComparisonChannelData(
                    channel_id=competitor.channel_id,
                    channel_title=competitor.channel_title,
                    is_competitor=True,
                    thumbnail_url=competitor.thumbnail_url,
                    subscriber_count=subscriber_count,
                    video_count=video_count,
                    view_count=view_count,
                    subscriber_change=subscriber_change,
                    view_change=view_change,
                    videos_published=videos_published,
                    avg_views_per_video=avg_views,
                    growth_rate=growth_rate,
                ))
            except CompetitorNotFoundError:
                continue

        # TODO: Add user's own accounts if account_ids provided
        # This would require integration with the account module

        # Calculate averages
        if channels:
            avg_subscribers = sum(c.subscriber_count for c in channels) / len(channels)
            avg_views = sum(c.view_count for c in channels) / len(channels)
            avg_growth = sum(c.growth_rate for c in channels) / len(channels)

            # Calculate variances
            for channel in channels:
                channel.subscriber_variance = calculate_variance(
                    channel.subscriber_count, avg_subscribers
                )
                channel.view_variance = calculate_variance(
                    channel.view_count, avg_views
                )
        else:
            avg_subscribers = 0.0
            avg_views = 0.0
            avg_growth = 0.0

        return ComparisonResponse(
            channels=channels,
            start_date=start_date,
            end_date=end_date,
            average_subscribers=avg_subscribers,
            average_views=avg_views,
            average_growth_rate=avg_growth,
        )


    # ============================================
    # Content Notifications (Requirements: 19.3)
    # ============================================

    async def check_new_content(
        self, competitor_id: uuid.UUID
    ) -> list[CompetitorContent]:
        """Check for new content from a competitor.

        Args:
            competitor_id: Competitor UUID

        Returns:
            list[CompetitorContent]: Newly discovered content

        Raises:
            CompetitorNotFoundError: If competitor not found
        """
        competitor = await self.get_competitor(competitor_id)

        # Determine cutoff time (24 hours ago or last check)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        if competitor.last_content_check_at:
            cutoff = competitor.last_content_check_at

        try:
            videos = await self.youtube_api.get_recent_videos(
                competitor.channel_id,
                max_results=10,
                published_after=cutoff,
            )
        except YouTubeAPIError as e:
            raise CompetitorServiceError(f"Failed to fetch videos: {str(e)}")

        new_content = []
        for video in videos:
            # Check if we already have this content
            exists = await self.content_repo.exists(
                competitor_id, video.video_id
            )
            if exists:
                continue

            # Create new content record
            content = await self.content_repo.create(
                competitor_id=competitor_id,
                video_id=video.video_id,
                title=video.title,
                description=video.description,
                thumbnail_url=video.thumbnail_url,
                content_type=video.content_type,
                view_count=video.view_count,
                like_count=video.like_count,
                comment_count=video.comment_count,
                duration_seconds=video.duration_seconds,
                published_at=video.published_at or datetime.utcnow(),
                tags=video.tags,
                category_id=video.category_id,
            )
            new_content.append(content)

        # Update last check time
        await self.competitor_repo.update(
            competitor, last_content_check_at=datetime.utcnow()
        )

        return new_content

    async def get_pending_notifications(self) -> list[CompetitorContent]:
        """Get content items that need notification.

        Returns:
            list[CompetitorContent]: Content needing notification
        """
        return await self.content_repo.get_pending_notifications()

    async def mark_content_notified(
        self, content_id: uuid.UUID
    ) -> CompetitorContent:
        """Mark content as notified.

        Args:
            content_id: Content UUID

        Returns:
            CompetitorContent: Updated content
        """
        content = await self.content_repo.get_by_id(content_id)
        if not content:
            raise CompetitorServiceError(f"Content not found: {content_id}")
        return await self.content_repo.mark_notified(content)

    async def get_competitor_content(
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
        return await self.content_repo.get_by_competitor(competitor_id, limit)

    # ============================================
    # AI Recommendations (Requirements: 19.4)
    # ============================================

    async def generate_analysis(
        self,
        user_id: uuid.UUID,
        competitor_ids: list[uuid.UUID],
        analysis_type: str,
        start_date: date,
        end_date: date,
    ) -> CompetitorAnalysis:
        """Generate AI-powered competitor analysis.

        Args:
            user_id: User UUID
            competitor_ids: List of competitor UUIDs
            analysis_type: Type of analysis
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            CompetitorAnalysis: Generated analysis
        """
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must be >= start_date")

        # Gather competitor data
        competitors_data = []
        for comp_id in competitor_ids:
            try:
                competitor = await self.get_competitor(comp_id)
                metrics = await self.get_competitor_metrics(
                    comp_id, start_date, end_date
                )
                content = await self.get_competitor_content(comp_id, limit=20)
                competitors_data.append({
                    "competitor": competitor,
                    "metrics": metrics,
                    "content": content,
                })
            except CompetitorNotFoundError:
                continue

        if not competitors_data:
            raise CompetitorServiceError("No valid competitors found")

        # Generate insights and recommendations
        insights = self._generate_insights(competitors_data, analysis_type)
        recommendations = self._generate_recommendations(
            competitors_data, analysis_type
        )
        summary = self._generate_summary(competitors_data, analysis_type)

        # Build trend data
        trend_data = self._build_trend_data(competitors_data)

        # Create analysis record
        analysis = await self.analysis_repo.create(
            user_id=user_id,
            competitor_ids=competitor_ids,
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            insights=[i.model_dump() for i in insights],
            recommendations=[r.model_dump() for r in recommendations],
            trend_data=trend_data,
        )

        return analysis

    def _generate_insights(
        self,
        competitors_data: list[dict],
        analysis_type: str,
    ) -> list[AnalysisInsight]:
        """Generate insights from competitor data.

        Args:
            competitors_data: List of competitor data dicts
            analysis_type: Type of analysis

        Returns:
            list[AnalysisInsight]: Generated insights
        """
        insights = []

        for data in competitors_data:
            competitor = data["competitor"]
            metrics = data["metrics"]
            content = data["content"]

            if not metrics:
                continue

            # Growth insight
            first_metric = metrics[0]
            last_metric = metrics[-1]

            if first_metric.subscriber_count > 0:
                growth_rate = calculate_growth_rate(
                    last_metric.subscriber_count,
                    first_metric.subscriber_count,
                )

                if abs(growth_rate) > 5:
                    direction = "growing" if growth_rate > 0 else "declining"
                    insights.append(AnalysisInsight(
                        category="growth",
                        title=f"{competitor.channel_title} is {direction}",
                        description=(
                            f"Subscriber count changed by {growth_rate:.1f}% "
                            f"during the analysis period."
                        ),
                        importance="high" if abs(growth_rate) > 10 else "medium",
                        metric_name="subscriber_growth",
                        metric_value=last_metric.subscriber_count,
                        metric_change=growth_rate,
                    ))

            # Content frequency insight
            if content:
                recent_count = len([
                    c for c in content
                    if c.published_at and c.published_at.date() >= metrics[0].metric_date
                ])
                if recent_count > 0:
                    insights.append(AnalysisInsight(
                        category="content",
                        title=f"{competitor.channel_title} content activity",
                        description=(
                            f"Published {recent_count} videos during the analysis period."
                        ),
                        importance="medium",
                        metric_name="videos_published",
                        metric_value=recent_count,
                    ))

            # Engagement insight
            if last_metric.avg_views_per_video > 0:
                insights.append(AnalysisInsight(
                    category="engagement",
                    title=f"{competitor.channel_title} average performance",
                    description=(
                        f"Average views per video: {last_metric.avg_views_per_video:,.0f}"
                    ),
                    importance="medium",
                    metric_name="avg_views_per_video",
                    metric_value=last_metric.avg_views_per_video,
                ))

        return insights

    def _generate_recommendations(
        self,
        competitors_data: list[dict],
        analysis_type: str,
    ) -> list[AnalysisRecommendation]:
        """Generate recommendations from competitor data.

        Args:
            competitors_data: List of competitor data dicts
            analysis_type: Type of analysis

        Returns:
            list[AnalysisRecommendation]: Generated recommendations
        """
        recommendations = []

        # Analyze content patterns
        all_content = []
        for data in competitors_data:
            all_content.extend(data.get("content", []))

        if all_content:
            # Content timing recommendation
            recommendations.append(AnalysisRecommendation(
                category="timing",
                title="Optimize upload schedule",
                description=(
                    "Analyze competitor upload patterns to find optimal posting times."
                ),
                action_items=[
                    "Review competitor upload schedules",
                    "Identify gaps in content timing",
                    "Test different posting times",
                ],
                priority="medium",
                estimated_impact="Potential 10-20% increase in initial views",
                confidence=0.7,
            ))

            # Content type recommendation
            video_types = {}
            for content in all_content:
                ct = content.content_type
                video_types[ct] = video_types.get(ct, 0) + 1

            if video_types:
                most_common = max(video_types, key=video_types.get)
                recommendations.append(AnalysisRecommendation(
                    category="content",
                    title=f"Consider {most_common} content",
                    description=(
                        f"Competitors are focusing on {most_common} content. "
                        f"Consider if this format fits your strategy."
                    ),
                    action_items=[
                        f"Analyze top-performing {most_common} content",
                        "Identify successful patterns",
                        "Test similar content format",
                    ],
                    priority="high",
                    estimated_impact="Align with market trends",
                    confidence=0.75,
                ))

        # Growth recommendation
        growing_competitors = []
        for data in competitors_data:
            metrics = data.get("metrics", [])
            if len(metrics) >= 2:
                growth = calculate_growth_rate(
                    metrics[-1].subscriber_count,
                    metrics[0].subscriber_count,
                )
                if growth > 5:
                    growing_competitors.append(data["competitor"].channel_title)

        if growing_competitors:
            recommendations.append(AnalysisRecommendation(
                category="growth",
                title="Study fast-growing competitors",
                description=(
                    f"These competitors are growing quickly: {', '.join(growing_competitors[:3])}. "
                    f"Analyze their strategies."
                ),
                action_items=[
                    "Review their recent content",
                    "Analyze their engagement tactics",
                    "Identify differentiating factors",
                ],
                priority="high",
                estimated_impact="Learn from successful strategies",
                confidence=0.8,
            ))

        return recommendations

    def _generate_summary(
        self,
        competitors_data: list[dict],
        analysis_type: str,
    ) -> str:
        """Generate analysis summary.

        Args:
            competitors_data: List of competitor data dicts
            analysis_type: Type of analysis

        Returns:
            str: Summary text
        """
        num_competitors = len(competitors_data)
        total_subscribers = sum(
            d["competitor"].subscriber_count for d in competitors_data
        )
        avg_subscribers = total_subscribers / num_competitors if num_competitors > 0 else 0

        return (
            f"Analysis of {num_competitors} competitor(s) with combined "
            f"{total_subscribers:,} subscribers (average: {avg_subscribers:,.0f}). "
            f"This {analysis_type} analysis provides insights into competitor "
            f"performance and actionable recommendations for your channel strategy."
        )

    def _build_trend_data(self, competitors_data: list[dict]) -> dict:
        """Build trend data for visualization.

        Args:
            competitors_data: List of competitor data dicts

        Returns:
            dict: Trend data for charts
        """
        trend_data = {"channels": []}

        for data in competitors_data:
            competitor = data["competitor"]
            metrics = data["metrics"]

            channel_trend = {
                "channel_id": competitor.channel_id,
                "channel_title": competitor.channel_title,
                "dates": [m.metric_date.isoformat() for m in metrics],
                "subscribers": [m.subscriber_count for m in metrics],
                "views": [m.view_count for m in metrics],
                "videos": [m.video_count for m in metrics],
            }
            trend_data["channels"].append(channel_trend)

        return trend_data

    # ============================================
    # Export (Requirements: 19.5)
    # ============================================

    async def export_analysis(
        self,
        user_id: uuid.UUID,
        competitor_ids: list[uuid.UUID],
        start_date: date,
        end_date: date,
        export_format: str,
        include_trend_data: bool = True,
        include_insights: bool = True,
    ) -> CompetitorAnalysis:
        """Export competitor analysis.

        Args:
            user_id: User UUID
            competitor_ids: List of competitor UUIDs
            start_date: Start of analysis period
            end_date: End of analysis period
            export_format: Export format (pdf, csv, json)
            include_trend_data: Include trend data
            include_insights: Include AI insights

        Returns:
            CompetitorAnalysis: Analysis with export info
        """
        # Generate analysis first
        analysis = await self.generate_analysis(
            user_id=user_id,
            competitor_ids=competitor_ids,
            analysis_type="comparison",
            start_date=start_date,
            end_date=end_date,
        )

        # Queue export task
        from app.modules.competitor.tasks import export_analysis_task
        export_analysis_task.delay(
            str(analysis.id),
            export_format,
            include_trend_data,
            include_insights,
        )

        return analysis

    async def get_analysis(self, analysis_id: uuid.UUID) -> CompetitorAnalysis:
        """Get an analysis by ID.

        Args:
            analysis_id: Analysis UUID

        Returns:
            CompetitorAnalysis: Analysis instance

        Raises:
            CompetitorServiceError: If analysis not found
        """
        analysis = await self.analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise CompetitorServiceError(f"Analysis not found: {analysis_id}")
        return analysis

    async def get_user_analyses(
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
        return await self.analysis_repo.get_by_user(user_id, limit)
