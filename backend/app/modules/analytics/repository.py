"""Analytics repository for database operations.

Implements CRUD operations for analytics snapshots with aggregation support.
Requirements: 17.1, 17.2
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, func as sql_func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import AnalyticsSnapshot, AnalyticsReport


class AnalyticsRepository:
    """Repository for AnalyticsSnapshot CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        account_id: uuid.UUID,
        snapshot_date: date,
        **kwargs,
    ) -> AnalyticsSnapshot:
        """Create a new analytics snapshot.

        Args:
            account_id: YouTube account UUID
            snapshot_date: Date for the snapshot
            **kwargs: Additional metrics

        Returns:
            AnalyticsSnapshot: Created snapshot instance
        """
        snapshot = AnalyticsSnapshot(
            account_id=account_id,
            snapshot_date=snapshot_date,
            **kwargs,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_by_id(self, snapshot_id: uuid.UUID) -> Optional[AnalyticsSnapshot]:
        """Get snapshot by ID."""
        result = await self.session.execute(
            select(AnalyticsSnapshot).where(AnalyticsSnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()


    async def get_by_account_and_date(
        self, account_id: uuid.UUID, snapshot_date: date
    ) -> Optional[AnalyticsSnapshot]:
        """Get snapshot for a specific account and date."""
        result = await self.session.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.account_id == account_id,
                    AnalyticsSnapshot.snapshot_date == snapshot_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_account_date_range(
        self,
        account_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[AnalyticsSnapshot]:
        """Get snapshots for an account within a date range.

        Args:
            account_id: YouTube account UUID
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            list[AnalyticsSnapshot]: Snapshots within the date range
        """
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.account_id == account_id,
                    AnalyticsSnapshot.snapshot_date >= start_date,
                    AnalyticsSnapshot.snapshot_date <= end_date,
                )
            )
            .order_by(AnalyticsSnapshot.snapshot_date)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[AnalyticsSnapshot]:
        """Get snapshots within a date range, optionally filtered by accounts.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            account_ids: Optional list of account IDs to filter

        Returns:
            list[AnalyticsSnapshot]: Snapshots within the date range
        """
        query = select(AnalyticsSnapshot).where(
            and_(
                AnalyticsSnapshot.snapshot_date >= start_date,
                AnalyticsSnapshot.snapshot_date <= end_date,
            )
        )
        if account_ids:
            query = query.where(AnalyticsSnapshot.account_id.in_(account_ids))
        query = query.order_by(
            AnalyticsSnapshot.account_id, AnalyticsSnapshot.snapshot_date
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_aggregated_metrics(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> dict:
        """Get aggregated metrics across accounts for a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            account_ids: Optional list of account IDs to filter

        Returns:
            dict: Aggregated metrics
        """
        query = select(
            sql_func.sum(AnalyticsSnapshot.subscriber_count).label("total_subscribers"),
            sql_func.sum(AnalyticsSnapshot.subscriber_change).label("subscriber_change"),
            sql_func.sum(AnalyticsSnapshot.total_views).label("total_views"),
            sql_func.sum(AnalyticsSnapshot.views_change).label("views_change"),
            sql_func.sum(AnalyticsSnapshot.total_videos).label("total_videos"),
            sql_func.sum(AnalyticsSnapshot.total_likes).label("total_likes"),
            sql_func.sum(AnalyticsSnapshot.total_comments).label("total_comments"),
            sql_func.avg(AnalyticsSnapshot.engagement_rate).label("avg_engagement_rate"),
            sql_func.sum(AnalyticsSnapshot.watch_time_minutes).label("total_watch_time"),
            sql_func.sum(AnalyticsSnapshot.estimated_revenue).label("total_revenue"),
        ).where(
            and_(
                AnalyticsSnapshot.snapshot_date >= start_date,
                AnalyticsSnapshot.snapshot_date <= end_date,
            )
        )
        if account_ids:
            query = query.where(AnalyticsSnapshot.account_id.in_(account_ids))

        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_subscribers": row.total_subscribers or 0,
            "subscriber_change": row.subscriber_change or 0,
            "total_views": row.total_views or 0,
            "views_change": row.views_change or 0,
            "total_videos": row.total_videos or 0,
            "total_likes": row.total_likes or 0,
            "total_comments": row.total_comments or 0,
            "average_engagement_rate": float(row.avg_engagement_rate or 0),
            "total_watch_time_minutes": row.total_watch_time or 0,
            "total_revenue": float(row.total_revenue or 0),
        }

    async def get_latest_snapshot_per_account(
        self,
        account_ids: list[uuid.UUID],
        before_date: Optional[date] = None,
    ) -> dict[uuid.UUID, AnalyticsSnapshot]:
        """Get the latest snapshot for each account.

        Args:
            account_ids: List of account IDs
            before_date: Optional date to get snapshot before

        Returns:
            dict: Mapping of account_id to latest snapshot
        """
        result = {}
        for account_id in account_ids:
            query = (
                select(AnalyticsSnapshot)
                .where(AnalyticsSnapshot.account_id == account_id)
            )
            if before_date:
                query = query.where(AnalyticsSnapshot.snapshot_date < before_date)
            query = query.order_by(AnalyticsSnapshot.snapshot_date.desc()).limit(1)
            
            snapshot_result = await self.session.execute(query)
            snapshot = snapshot_result.scalar_one_or_none()
            if snapshot:
                result[account_id] = snapshot
        return result

    async def upsert(
        self,
        account_id: uuid.UUID,
        snapshot_date: date,
        **kwargs,
    ) -> AnalyticsSnapshot:
        """Create or update a snapshot for an account and date.

        Args:
            account_id: YouTube account UUID
            snapshot_date: Date for the snapshot
            **kwargs: Metrics to update

        Returns:
            AnalyticsSnapshot: Created or updated snapshot
        """
        existing = await self.get_by_account_and_date(account_id, snapshot_date)
        if existing:
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            return existing
        return await self.create(account_id, snapshot_date, **kwargs)

    async def delete(self, snapshot: AnalyticsSnapshot) -> None:
        """Delete a snapshot."""
        await self.session.delete(snapshot)
        await self.session.flush()


class AnalyticsReportRepository:
    """Repository for AnalyticsReport CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        report_type: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> AnalyticsReport:
        """Create a new analytics report."""
        report = AnalyticsReport(
            user_id=user_id,
            title=title,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            account_ids=[str(aid) for aid in account_ids] if account_ids else None,
            status="pending",
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> Optional[AnalyticsReport]:
        """Get report by ID."""
        result = await self.session.execute(
            select(AnalyticsReport).where(AnalyticsReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> list[AnalyticsReport]:
        """Get reports for a user."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.user_id == user_id)
            .order_by(AnalyticsReport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        report: AnalyticsReport,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        ai_insights: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> AnalyticsReport:
        """Update report status and related fields."""
        report.status = status
        if file_path:
            report.file_path = file_path
        if file_size:
            report.file_size = file_size
        if ai_insights:
            report.ai_insights = ai_insights
        if error_message:
            report.error_message = error_message
        if status == "completed":
            report.completed_at = datetime.utcnow()
        await self.session.flush()
        return report

    async def delete(self, report: AnalyticsReport) -> None:
        """Delete a report."""
        await self.session.delete(report)
        await self.session.flush()
