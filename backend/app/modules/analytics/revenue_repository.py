"""Repository for revenue data access.

Implements data access patterns for revenue records, goals, and alerts.
Requirements: 18.1, 18.2, 18.3, 18.4
"""

import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.revenue_models import (
    RevenueRecord,
    RevenueGoal,
    RevenueAlert,
    GoalStatus,
    AlertStatus,
)
from app.modules.analytics.revenue_schemas import (
    RevenueRecordCreate,
    RevenueRecordUpdate,
    RevenueGoalCreate,
    RevenueGoalUpdate,
    RevenueAlertCreate,
)


class RevenueRecordRepository:
    """Repository for RevenueRecord operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: RevenueRecordCreate) -> RevenueRecord:
        """Create a new revenue record."""
        record = RevenueRecord(
            account_id=data.account_id,
            record_date=data.record_date,
            ad_revenue=data.ad_revenue,
            membership_revenue=data.membership_revenue,
            super_chat_revenue=data.super_chat_revenue,
            super_sticker_revenue=data.super_sticker_revenue,
            merchandise_revenue=data.merchandise_revenue,
            youtube_premium_revenue=data.youtube_premium_revenue,
            currency=data.currency,
            estimated_cpm=data.estimated_cpm,
            monetized_playbacks=data.monetized_playbacks,
            playback_based_cpm=data.playback_based_cpm,
        )
        # Calculate total
        record.total_revenue = record.calculate_total()
        
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[RevenueRecord]:
        """Get a revenue record by ID."""
        result = await self.session.execute(
            select(RevenueRecord).where(RevenueRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_and_date(
        self, account_id: uuid.UUID, record_date: date
    ) -> Optional[RevenueRecord]:
        """Get a revenue record by account and date."""
        result = await self.session.execute(
            select(RevenueRecord).where(
                and_(
                    RevenueRecord.account_id == account_id,
                    RevenueRecord.record_date == record_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        account_ids: Optional[List[uuid.UUID]],
        start_date: date,
        end_date: date,
    ) -> List[RevenueRecord]:
        """Get revenue records for accounts within a date range."""
        query = select(RevenueRecord).where(
            and_(
                RevenueRecord.record_date >= start_date,
                RevenueRecord.record_date <= end_date,
            )
        )
        if account_ids:
            query = query.where(RevenueRecord.account_id.in_(account_ids))
        
        query = query.order_by(RevenueRecord.record_date)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_by_date_range(
        self,
        account_ids: Optional[List[uuid.UUID]],
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get aggregated revenue totals for a date range."""
        query = select(
            func.sum(RevenueRecord.ad_revenue).label("ad_revenue"),
            func.sum(RevenueRecord.membership_revenue).label("membership_revenue"),
            func.sum(RevenueRecord.super_chat_revenue).label("super_chat_revenue"),
            func.sum(RevenueRecord.super_sticker_revenue).label("super_sticker_revenue"),
            func.sum(RevenueRecord.merchandise_revenue).label("merchandise_revenue"),
            func.sum(RevenueRecord.youtube_premium_revenue).label("youtube_premium_revenue"),
            func.sum(RevenueRecord.total_revenue).label("total_revenue"),
        ).where(
            and_(
                RevenueRecord.record_date >= start_date,
                RevenueRecord.record_date <= end_date,
            )
        )
        if account_ids:
            query = query.where(RevenueRecord.account_id.in_(account_ids))
        
        result = await self.session.execute(query)
        row = result.one()
        return {
            "ad_revenue": row.ad_revenue or 0.0,
            "membership_revenue": row.membership_revenue or 0.0,
            "super_chat_revenue": row.super_chat_revenue or 0.0,
            "super_sticker_revenue": row.super_sticker_revenue or 0.0,
            "merchandise_revenue": row.merchandise_revenue or 0.0,
            "youtube_premium_revenue": row.youtube_premium_revenue or 0.0,
            "total_revenue": row.total_revenue or 0.0,
        }

    async def get_total_by_account(
        self,
        account_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get aggregated revenue totals for a single account."""
        return await self.get_total_by_date_range([account_id], start_date, end_date)

    async def update(
        self, record_id: uuid.UUID, data: RevenueRecordUpdate
    ) -> Optional[RevenueRecord]:
        """Update a revenue record."""
        record = await self.get_by_id(record_id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        # Recalculate total
        record.total_revenue = record.calculate_total()
        
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def upsert(self, data: RevenueRecordCreate) -> RevenueRecord:
        """Create or update a revenue record."""
        existing = await self.get_by_account_and_date(data.account_id, data.record_date)
        if existing:
            update_data = RevenueRecordUpdate(
                ad_revenue=data.ad_revenue,
                membership_revenue=data.membership_revenue,
                super_chat_revenue=data.super_chat_revenue,
                super_sticker_revenue=data.super_sticker_revenue,
                merchandise_revenue=data.merchandise_revenue,
                youtube_premium_revenue=data.youtube_premium_revenue,
                estimated_cpm=data.estimated_cpm,
                monetized_playbacks=data.monetized_playbacks,
                playback_based_cpm=data.playback_based_cpm,
            )
            return await self.update(existing.id, update_data)
        return await self.create(data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Delete a revenue record."""
        record = await self.get_by_id(record_id)
        if not record:
            return False
        await self.session.delete(record)
        await self.session.commit()
        return True


class RevenueGoalRepository:
    """Repository for RevenueGoal operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, data: RevenueGoalCreate) -> RevenueGoal:
        """Create a new revenue goal."""
        goal = RevenueGoal(
            user_id=user_id,
            account_id=data.account_id,
            name=data.name,
            description=data.description,
            target_amount=data.target_amount,
            currency=data.currency,
            period_type=data.period_type.value,
            start_date=data.start_date,
            end_date=data.end_date,
            notify_at_percentage=data.notify_at_percentage,
        )
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def get_by_id(self, goal_id: uuid.UUID) -> Optional[RevenueGoal]:
        """Get a revenue goal by ID."""
        result = await self.session.execute(
            select(RevenueGoal).where(RevenueGoal.id == goal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[GoalStatus] = None,
    ) -> List[RevenueGoal]:
        """Get all revenue goals for a user."""
        query = select(RevenueGoal).where(RevenueGoal.user_id == user_id)
        if status:
            query = query.where(RevenueGoal.status == status.value)
        query = query.order_by(RevenueGoal.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_goals(self, user_id: uuid.UUID) -> List[RevenueGoal]:
        """Get all active revenue goals for a user."""
        return await self.get_by_user(user_id, GoalStatus.ACTIVE)

    async def update(
        self, goal_id: uuid.UUID, data: RevenueGoalUpdate
    ) -> Optional[RevenueGoal]:
        """Update a revenue goal."""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                setattr(goal, field, value.value)
            else:
                setattr(goal, field, value)
        
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def update_progress(
        self, goal_id: uuid.UUID, current_amount: float
    ) -> Optional[RevenueGoal]:
        """Update goal progress."""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return None

        goal.update_progress(current_amount)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def delete(self, goal_id: uuid.UUID) -> bool:
        """Delete a revenue goal."""
        goal = await self.get_by_id(goal_id)
        if not goal:
            return False
        await self.session.delete(goal)
        await self.session.commit()
        return True


class RevenueAlertRepository:
    """Repository for RevenueAlert operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: RevenueAlertCreate) -> RevenueAlert:
        """Create a new revenue alert."""
        alert = RevenueAlert(
            user_id=data.user_id,
            account_id=data.account_id,
            alert_type=data.alert_type.value,
            severity=data.severity.value,
            title=data.title,
            message=data.message,
            metric_name=data.metric_name,
            previous_value=data.previous_value,
            current_value=data.current_value,
            change_percentage=data.change_percentage,
            ai_analysis=data.ai_analysis,
            ai_recommendations=data.ai_recommendations,
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Optional[RevenueAlert]:
        """Get a revenue alert by ID."""
        result = await self.session.execute(
            select(RevenueAlert).where(RevenueAlert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[AlertStatus] = None,
        limit: int = 50,
    ) -> List[RevenueAlert]:
        """Get revenue alerts for a user."""
        query = select(RevenueAlert).where(RevenueAlert.user_id == user_id)
        if status:
            query = query.where(RevenueAlert.status == status.value)
        query = query.order_by(RevenueAlert.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread alerts for a user."""
        result = await self.session.execute(
            select(func.count(RevenueAlert.id)).where(
                and_(
                    RevenueAlert.user_id == user_id,
                    RevenueAlert.status == AlertStatus.UNREAD.value,
                )
            )
        )
        return result.scalar() or 0

    async def mark_as_read(self, alert_id: uuid.UUID) -> Optional[RevenueAlert]:
        """Mark an alert as read."""
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        alert.mark_as_read()
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def dismiss(self, alert_id: uuid.UUID) -> Optional[RevenueAlert]:
        """Dismiss an alert."""
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        alert.dismiss()
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all alerts as read for a user."""
        alerts = await self.get_by_user(user_id, AlertStatus.UNREAD)
        count = 0
        for alert in alerts:
            alert.mark_as_read()
            count += 1
        await self.session.commit()
        return count
