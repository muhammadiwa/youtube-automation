"""Repository for Notification Service database operations.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import (
    NotificationPreference,
    NotificationLog,
    NotificationBatch,
    EscalationRule,
    NotificationStatus,
    NotificationPriority,
)


class NotificationPreferenceRepository:
    """Repository for notification preferences.
    
    Requirements: 23.2 - Store settings per account and event type
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_preference(
        self,
        user_id: uuid.UUID,
        event_type: str,
        account_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> NotificationPreference:
        """Create a new notification preference."""
        preference = NotificationPreference(
            user_id=user_id,
            event_type=event_type,
            account_id=account_id,
            **kwargs,
        )
        self.session.add(preference)
        await self.session.commit()
        await self.session.refresh(preference)
        return preference

    async def get_preference_by_id(
        self, preference_id: uuid.UUID
    ) -> Optional[NotificationPreference]:
        """Get preference by ID."""
        result = await self.session.execute(
            select(NotificationPreference).where(NotificationPreference.id == preference_id)
        )
        return result.scalar_one_or_none()

    async def get_user_preferences(
        self,
        user_id: uuid.UUID,
        event_type: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
    ) -> list[NotificationPreference]:
        """Get user's notification preferences."""
        query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        
        if event_type:
            query = query.where(NotificationPreference.event_type == event_type)
        
        if account_id:
            query = query.where(
                or_(
                    NotificationPreference.account_id == account_id,
                    NotificationPreference.account_id.is_(None),
                )
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_preference_for_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        account_id: Optional[uuid.UUID] = None,
    ) -> Optional[NotificationPreference]:
        """Get specific preference for an event type.
        
        Returns account-specific preference if exists, otherwise global preference.
        """
        # First try account-specific preference
        if account_id:
            result = await self.session.execute(
                select(NotificationPreference).where(
                    and_(
                        NotificationPreference.user_id == user_id,
                        NotificationPreference.event_type == event_type,
                        NotificationPreference.account_id == account_id,
                    )
                )
            )
            pref = result.scalar_one_or_none()
            if pref:
                return pref
        
        # Fall back to global preference
        result = await self.session.execute(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.event_type == event_type,
                    NotificationPreference.account_id.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_preference(
        self,
        preference_id: uuid.UUID,
        **kwargs,
    ) -> Optional[NotificationPreference]:
        """Update a notification preference."""
        preference = await self.get_preference_by_id(preference_id)
        if not preference:
            return None
        
        for key, value in kwargs.items():
            if hasattr(preference, key) and value is not None:
                setattr(preference, key, value)
        
        await self.session.commit()
        await self.session.refresh(preference)
        return preference

    async def delete_preference(self, preference_id: uuid.UUID) -> bool:
        """Delete a notification preference."""
        preference = await self.get_preference_by_id(preference_id)
        if not preference:
            return False
        
        await self.session.delete(preference)
        await self.session.commit()
        return True


class NotificationLogRepository:
    """Repository for notification logs.
    
    Requirements: 23.1, 23.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        user_id: uuid.UUID,
        event_type: str,
        title: str,
        message: str,
        channel: str,
        recipient: str,
        priority: str = NotificationPriority.NORMAL.value,
        account_id: Optional[uuid.UUID] = None,
        event_id: Optional[uuid.UUID] = None,
        payload: Optional[dict] = None,
        batch_id: Optional[uuid.UUID] = None,
        is_batched: bool = False,
    ) -> NotificationLog:
        """Create a new notification log entry."""
        log = NotificationLog(
            user_id=user_id,
            event_type=event_type,
            title=title,
            message=message,
            channel=channel,
            recipient=recipient,
            priority=priority,
            account_id=account_id,
            event_id=event_id,
            payload=payload,
            batch_id=batch_id,
            is_batched=is_batched,
            status=NotificationStatus.PENDING.value,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_log_by_id(self, log_id: uuid.UUID) -> Optional[NotificationLog]:
        """Get notification log by ID."""
        result = await self.session.execute(
            select(NotificationLog).where(NotificationLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        log_id: uuid.UUID,
        status: str,
        error: Optional[str] = None,
    ) -> Optional[NotificationLog]:
        """Update notification status."""
        log = await self.get_log_by_id(log_id)
        if not log:
            return None
        
        log.status = status
        log.attempts += 1
        
        if error:
            log.last_error = error
        
        if status == NotificationStatus.QUEUED.value:
            log.queued_at = datetime.utcnow()
        elif status == NotificationStatus.SENDING.value:
            log.sent_at = datetime.utcnow()
        elif status == NotificationStatus.DELIVERED.value:
            log.delivered_at = datetime.utcnow()
            log.delivery_time_seconds = log.calculate_delivery_time()
        
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def mark_delivered(
        self,
        log_id: uuid.UUID,
        delivered_at: Optional[datetime] = None,
    ) -> Optional[NotificationLog]:
        """Mark notification as delivered and calculate delivery time.
        
        Requirements: 23.1 - Track delivery timing
        """
        log = await self.get_log_by_id(log_id)
        if not log:
            return None
        
        log.status = NotificationStatus.DELIVERED.value
        log.delivered_at = delivered_at or datetime.utcnow()
        log.delivery_time_seconds = log.calculate_delivery_time()
        
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def acknowledge(
        self,
        log_id: uuid.UUID,
        acknowledged_by: uuid.UUID,
    ) -> Optional[NotificationLog]:
        """Acknowledge a notification.
        
        Requirements: 23.5 - Mark alerts resolved, log response time
        """
        log = await self.get_log_by_id(log_id)
        if not log:
            return None
        
        log.acknowledged = True
        log.acknowledged_at = datetime.utcnow()
        log.acknowledged_by = acknowledged_by
        log.response_time_seconds = log.calculate_response_time()
        log.status = NotificationStatus.ACKNOWLEDGED.value
        
        await self.session.commit()
        await self.session.refresh(log)
        return log


    async def list_logs(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        event_type: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[NotificationLog], int]:
        """List notification logs with filters."""
        query = select(NotificationLog).where(NotificationLog.user_id == user_id)
        count_query = select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user_id
        )
        
        if status:
            query = query.where(NotificationLog.status == status)
            count_query = count_query.where(NotificationLog.status == status)
        
        if channel:
            query = query.where(NotificationLog.channel == channel)
            count_query = count_query.where(NotificationLog.channel == channel)
        
        if event_type:
            query = query.where(NotificationLog.event_type == event_type)
            count_query = count_query.where(NotificationLog.event_type == event_type)
        
        if account_id:
            query = query.where(NotificationLog.account_id == account_id)
            count_query = count_query.where(NotificationLog.account_id == account_id)
        
        if created_after:
            query = query.where(NotificationLog.created_at >= created_after)
            count_query = count_query.where(NotificationLog.created_at >= created_after)
        
        if created_before:
            query = query.where(NotificationLog.created_at <= created_before)
            count_query = count_query.where(NotificationLog.created_at <= created_before)
        
        if acknowledged is not None:
            query = query.where(NotificationLog.acknowledged == acknowledged)
            count_query = count_query.where(NotificationLog.acknowledged == acknowledged)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(NotificationLog.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        logs = list(result.scalars().all())
        
        return logs, total

    async def get_pending_notifications(
        self, limit: int = 100
    ) -> list[NotificationLog]:
        """Get pending notifications for processing."""
        result = await self.session.execute(
            select(NotificationLog)
            .where(NotificationLog.status == NotificationStatus.PENDING.value)
            .order_by(
                # Priority order: critical > high > normal > low
                NotificationLog.priority.desc(),
                NotificationLog.created_at.asc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_delivery_stats(
        self,
        user_id: Optional[uuid.UUID] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> dict:
        """Get delivery timing statistics.
        
        Requirements: 23.1 - Track delivery within 60 seconds
        """
        query = select(NotificationLog)
        
        if user_id:
            query = query.where(NotificationLog.user_id == user_id)
        
        if created_after:
            query = query.where(NotificationLog.created_at >= created_after)
        
        if created_before:
            query = query.where(NotificationLog.created_at <= created_before)
        
        result = await self.session.execute(query)
        logs = list(result.scalars().all())
        
        total = len(logs)
        delivered = [l for l in logs if l.status == NotificationStatus.DELIVERED.value]
        failed = [l for l in logs if l.status == NotificationStatus.FAILED.value]
        
        delivery_times = [
            l.delivery_time_seconds for l in delivered
            if l.delivery_time_seconds is not None
        ]
        
        within_sla = [t for t in delivery_times if t <= 60.0]
        
        return {
            "total_notifications": total,
            "delivered_count": len(delivered),
            "failed_count": len(failed),
            "avg_delivery_time_seconds": (
                sum(delivery_times) / len(delivery_times) if delivery_times else None
            ),
            "max_delivery_time_seconds": max(delivery_times) if delivery_times else None,
            "min_delivery_time_seconds": min(delivery_times) if delivery_times else None,
            "within_sla_count": len(within_sla),
            "sla_compliance_percent": (
                (len(within_sla) / len(delivered) * 100) if delivered else 0.0
            ),
        }


class NotificationBatchRepository:
    """Repository for notification batches.
    
    Requirements: 23.3 - Batch simultaneous alerts
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_batch(
        self,
        user_id: uuid.UUID,
        priority: str = NotificationPriority.NORMAL.value,
    ) -> NotificationBatch:
        """Create a new notification batch."""
        batch = NotificationBatch(
            user_id=user_id,
            priority=priority,
            notification_count=0,
        )
        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[NotificationBatch]:
        """Get batch by ID."""
        result = await self.session.execute(
            select(NotificationBatch).where(NotificationBatch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def increment_count(self, batch_id: uuid.UUID) -> Optional[NotificationBatch]:
        """Increment notification count in batch."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        batch.notification_count += 1
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def mark_processed(self, batch_id: uuid.UUID) -> Optional[NotificationBatch]:
        """Mark batch as processed."""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        batch.status = NotificationStatus.DELIVERED.value
        batch.processed_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def get_pending_batches(
        self, user_id: uuid.UUID
    ) -> list[NotificationBatch]:
        """Get pending batches for a user."""
        result = await self.session.execute(
            select(NotificationBatch).where(
                and_(
                    NotificationBatch.user_id == user_id,
                    NotificationBatch.status == NotificationStatus.PENDING.value,
                )
            )
        )
        return list(result.scalars().all())


class EscalationRuleRepository:
    """Repository for escalation rules.
    
    Requirements: 23.4 - Multi-channel escalation for critical issues
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rule(
        self,
        user_id: uuid.UUID,
        name: str,
        event_types: list[str],
        escalation_levels: list[dict],
    ) -> EscalationRule:
        """Create a new escalation rule."""
        rule = EscalationRule(
            user_id=user_id,
            name=name,
            event_types=event_types,
            escalation_levels=escalation_levels,
        )
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def get_rule_by_id(self, rule_id: uuid.UUID) -> Optional[EscalationRule]:
        """Get rule by ID."""
        result = await self.session.execute(
            select(EscalationRule).where(EscalationRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_user_rules(self, user_id: uuid.UUID) -> list[EscalationRule]:
        """Get all escalation rules for a user."""
        result = await self.session.execute(
            select(EscalationRule).where(EscalationRule.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_rules_for_event(
        self, user_id: uuid.UUID, event_type: str
    ) -> list[EscalationRule]:
        """Get active escalation rules for an event type."""
        result = await self.session.execute(
            select(EscalationRule).where(
                and_(
                    EscalationRule.user_id == user_id,
                    EscalationRule.is_active == True,
                )
            )
        )
        rules = list(result.scalars().all())
        
        # Filter rules that include this event type
        return [r for r in rules if event_type in r.event_types]

    async def update_rule(
        self,
        rule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[EscalationRule]:
        """Update an escalation rule."""
        rule = await self.get_rule_by_id(rule_id)
        if not rule:
            return None
        
        for key, value in kwargs.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)
        
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        """Delete an escalation rule."""
        rule = await self.get_rule_by_id(rule_id)
        if not rule:
            return False
        
        await self.session.delete(rule)
        await self.session.commit()
        return True
