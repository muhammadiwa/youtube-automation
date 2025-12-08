"""Notification Service for multi-channel delivery.

Implements notification sending, batching, prioritization, and escalation.
Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from app.modules.notification.repository import (
    NotificationPreferenceRepository,
    NotificationLogRepository,
    NotificationBatchRepository,
    EscalationRuleRepository,
)
from app.modules.notification.schemas import (
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationLogInfo,
    NotificationLogListResponse,
    NotificationLogFilters,
    NotificationAcknowledgeRequest,
    NotificationAcknowledgeResponse,
    EscalationRuleCreate,
    EscalationRuleUpdate,
    EscalationRuleResponse,
    DeliveryTimingStats,
    DeliveryTimingResponse,
    NotificationChannel as SchemaChannel,
    NotificationPriority as SchemaPriority,
)
from app.modules.notification.channels import (
    EmailChannel,
    SMSChannel,
    SlackChannel,
    TelegramChannel,
    ChannelDeliveryResult,
)


class NotificationService:
    """Service for notification management and delivery.
    
    Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
    """

    # SLA threshold for delivery timing (Requirements: 23.1)
    SLA_THRESHOLD_SECONDS = 60.0

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pref_repo = NotificationPreferenceRepository(session)
        self.log_repo = NotificationLogRepository(session)
        self.batch_repo = NotificationBatchRepository(session)
        self.escalation_repo = EscalationRuleRepository(session)
        
        # Initialize delivery channels
        self.channels = {
            NotificationChannel.EMAIL.value: EmailChannel(),
            NotificationChannel.SMS.value: SMSChannel(),
            NotificationChannel.SLACK.value: SlackChannel(),
            NotificationChannel.TELEGRAM.value: TelegramChannel(),
        }

    # ==================== Notification Sending (23.1) ====================

    async def send_notification(
        self,
        request: NotificationSendRequest,
    ) -> NotificationSendResponse:
        """Send notification to user via configured channels.
        
        Requirements: 23.1 - Deliver within 60 seconds
        Requirements: 23.2 - Use preferences per account and event type
        """
        notification_ids = []
        channels_used = []
        
        # Get user preferences for this event type
        preference = await self.pref_repo.get_preference_for_event(
            user_id=request.user_id,
            event_type=request.event_type,
            account_id=request.account_id,
        )
        
        # Determine which channels to use
        if request.channels:
            # Use explicitly specified channels
            target_channels = [c.value for c in request.channels]
        elif preference:
            # Use channels from preferences
            target_channels = preference.get_enabled_channels()
        else:
            # Default to email only
            target_channels = [NotificationChannel.EMAIL.value]
        
        # Check for batching (Requirements: 23.3)
        batch_id = None
        is_batched = False
        if preference and preference.batch_enabled:
            batch = await self._get_or_create_batch(
                request.user_id,
                request.priority.value,
            )
            batch_id = batch.id
            is_batched = True
        
        # Create notification logs for each channel
        for channel in target_channels:
            recipient = self._get_recipient_for_channel(channel, preference)
            if not recipient:
                continue
            
            log = await self.log_repo.create_log(
                user_id=request.user_id,
                event_type=request.event_type,
                title=request.title,
                message=request.message,
                channel=channel,
                recipient=recipient,
                priority=request.priority.value,
                account_id=request.account_id,
                event_id=request.event_id,
                payload=request.payload,
                batch_id=batch_id,
                is_batched=is_batched,
            )
            
            notification_ids.append(log.id)
            channels_used.append(channel)
            
            # If not batched, deliver immediately
            if not is_batched:
                await self._deliver_notification(log)
        
        # Check for escalation rules (Requirements: 23.4)
        if request.priority == SchemaPriority.CRITICAL:
            await self._check_escalation(
                request.user_id,
                request.event_type,
                notification_ids,
            )
        
        return NotificationSendResponse(
            notification_ids=notification_ids,
            channels_used=channels_used,
            queued_at=datetime.utcnow(),
            message=f"Notification queued for {len(channels_used)} channel(s)",
        )

    async def _deliver_notification(self, log) -> bool:
        """Deliver a single notification.
        
        Requirements: 23.1 - Deliver within 60 seconds
        """
        channel_handler = self.channels.get(log.channel)
        if not channel_handler:
            await self.log_repo.update_status(
                log.id,
                NotificationStatus.FAILED.value,
                error=f"Unknown channel: {log.channel}",
            )
            return False
        
        # Mark as sending
        await self.log_repo.update_status(log.id, NotificationStatus.SENDING.value)
        
        # Attempt delivery
        result = await channel_handler.deliver(
            recipient=log.recipient,
            title=log.title,
            message=log.message,
            payload=log.payload,
        )
        
        if result.success:
            await self.log_repo.mark_delivered(log.id)
            return True
        else:
            # Check if we should retry
            if log.attempts < log.max_attempts:
                await self.log_repo.update_status(
                    log.id,
                    NotificationStatus.PENDING.value,
                    error=result.error,
                )
            else:
                await self.log_repo.update_status(
                    log.id,
                    NotificationStatus.FAILED.value,
                    error=result.error,
                )
            return False

    def _get_recipient_for_channel(
        self,
        channel: str,
        preference,
    ) -> Optional[str]:
        """Get recipient address for a channel from preferences."""
        if not preference:
            return None
        
        if channel == NotificationChannel.EMAIL.value:
            return preference.email_address
        elif channel == NotificationChannel.SMS.value:
            return preference.phone_number
        elif channel == NotificationChannel.SLACK.value:
            return preference.slack_webhook_url
        elif channel == NotificationChannel.TELEGRAM.value:
            return preference.telegram_chat_id
        
        return None

    # ==================== Batching (23.3) ====================

    async def _get_or_create_batch(
        self,
        user_id: uuid.UUID,
        priority: str,
    ):
        """Get existing pending batch or create new one.
        
        Requirements: 23.3 - Batch simultaneous alerts
        """
        pending_batches = await self.batch_repo.get_pending_batches(user_id)
        
        # Find batch with matching priority
        for batch in pending_batches:
            if batch.priority == priority:
                await self.batch_repo.increment_count(batch.id)
                return batch
        
        # Create new batch
        return await self.batch_repo.create_batch(user_id, priority)

    async def process_batches(self, user_id: uuid.UUID) -> int:
        """Process pending notification batches.
        
        Requirements: 23.3 - Batch simultaneous alerts
        """
        pending_batches = await self.batch_repo.get_pending_batches(user_id)
        processed_count = 0
        
        for batch in pending_batches:
            # Get all notifications in this batch
            logs, _ = await self.log_repo.list_logs(
                user_id=user_id,
                limit=1000,
                offset=0,
            )
            
            batch_logs = [l for l in logs if l.batch_id == batch.id]
            
            # Deliver all notifications in batch
            for log in batch_logs:
                await self._deliver_notification(log)
                processed_count += 1
            
            # Mark batch as processed
            await self.batch_repo.mark_processed(batch.id)
        
        return processed_count

    # ==================== Escalation (23.4) ====================

    async def _check_escalation(
        self,
        user_id: uuid.UUID,
        event_type: str,
        notification_ids: list[uuid.UUID],
    ) -> None:
        """Check and apply escalation rules for critical notifications.
        
        Requirements: 23.4 - Multi-channel escalation for critical issues
        """
        rules = await self.escalation_repo.get_rules_for_event(user_id, event_type)
        
        for rule in rules:
            if not rule.escalation_levels:
                continue
            
            # Mark notifications as escalated
            for notif_id in notification_ids:
                log = await self.log_repo.get_log_by_id(notif_id)
                if log:
                    log.is_escalated = True
                    log.escalation_level = 1
                    await self.session.commit()

    async def escalate_notification(
        self,
        notification_id: uuid.UUID,
    ) -> Optional[list[uuid.UUID]]:
        """Escalate a notification to the next level.
        
        Requirements: 23.4 - Multi-channel escalation
        """
        log = await self.log_repo.get_log_by_id(notification_id)
        if not log or not log.is_escalated:
            return None
        
        # Get escalation rules
        rules = await self.escalation_repo.get_rules_for_event(
            log.user_id,
            log.event_type,
        )
        
        if not rules:
            return None
        
        rule = rules[0]  # Use first matching rule
        next_level = log.escalation_level + 1
        
        # Find next escalation level
        level_config = None
        for level in rule.escalation_levels:
            if level.get("level") == next_level:
                level_config = level
                break
        
        if not level_config:
            return None  # No more escalation levels
        
        # Create notifications for escalation channels
        new_notification_ids = []
        for channel in level_config.get("channels", []):
            preference = await self.pref_repo.get_preference_for_event(
                log.user_id,
                log.event_type,
                log.account_id,
            )
            
            recipient = self._get_recipient_for_channel(channel, preference)
            if not recipient:
                continue
            
            new_log = await self.log_repo.create_log(
                user_id=log.user_id,
                event_type=log.event_type,
                title=f"[ESCALATED] {log.title}",
                message=log.message,
                channel=channel,
                recipient=recipient,
                priority=NotificationPriority.CRITICAL.value,
                account_id=log.account_id,
                event_id=log.event_id,
                payload=log.payload,
            )
            
            new_log.is_escalated = True
            new_log.escalation_level = next_level
            new_log.parent_notification_id = notification_id
            await self.session.commit()
            
            # Deliver immediately
            await self._deliver_notification(new_log)
            new_notification_ids.append(new_log.id)
        
        return new_notification_ids


    # ==================== Acknowledgment (23.5) ====================

    async def acknowledge_notification(
        self,
        request: NotificationAcknowledgeRequest,
    ) -> Optional[NotificationAcknowledgeResponse]:
        """Acknowledge a notification.
        
        Requirements: 23.5 - Mark alerts resolved, log response time
        """
        log = await self.log_repo.acknowledge(
            request.notification_id,
            request.acknowledged_by,
        )
        
        if not log:
            return None
        
        return NotificationAcknowledgeResponse(
            notification_id=log.id,
            acknowledged=log.acknowledged,
            acknowledged_at=log.acknowledged_at,
            response_time_seconds=log.response_time_seconds,
        )

    # ==================== Preferences Management (23.2) ====================

    async def create_preference(
        self,
        user_id: uuid.UUID,
        data: NotificationPreferenceCreate,
    ) -> NotificationPreferenceResponse:
        """Create notification preference.
        
        Requirements: 23.2 - Store settings per account and event type
        """
        preference = await self.pref_repo.create_preference(
            user_id=user_id,
            event_type=data.event_type,
            account_id=data.account_id,
            email_enabled=data.email_enabled,
            sms_enabled=data.sms_enabled,
            slack_enabled=data.slack_enabled,
            telegram_enabled=data.telegram_enabled,
            email_address=data.email_address,
            phone_number=data.phone_number,
            slack_webhook_url=data.slack_webhook_url,
            telegram_chat_id=data.telegram_chat_id,
            batch_enabled=data.batch_enabled,
            batch_interval_seconds=data.batch_interval_seconds,
            quiet_hours_enabled=data.quiet_hours_enabled,
            quiet_hours_start=data.quiet_hours_start,
            quiet_hours_end=data.quiet_hours_end,
        )
        
        return self._preference_to_response(preference)

    async def get_user_preferences(
        self,
        user_id: uuid.UUID,
        event_type: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
    ) -> list[NotificationPreferenceResponse]:
        """Get user's notification preferences."""
        preferences = await self.pref_repo.get_user_preferences(
            user_id, event_type, account_id
        )
        return [self._preference_to_response(p) for p in preferences]

    async def update_preference(
        self,
        preference_id: uuid.UUID,
        data: NotificationPreferenceUpdate,
    ) -> Optional[NotificationPreferenceResponse]:
        """Update notification preference."""
        preference = await self.pref_repo.update_preference(
            preference_id,
            **data.model_dump(exclude_unset=True),
        )
        
        if not preference:
            return None
        
        return self._preference_to_response(preference)

    async def delete_preference(self, preference_id: uuid.UUID) -> bool:
        """Delete notification preference."""
        return await self.pref_repo.delete_preference(preference_id)

    # ==================== Escalation Rules Management (23.4) ====================

    async def create_escalation_rule(
        self,
        user_id: uuid.UUID,
        data: EscalationRuleCreate,
    ) -> EscalationRuleResponse:
        """Create escalation rule.
        
        Requirements: 23.4 - Multi-channel escalation for critical issues
        """
        rule = await self.escalation_repo.create_rule(
            user_id=user_id,
            name=data.name,
            event_types=data.event_types,
            escalation_levels=[level.model_dump() for level in data.escalation_levels],
        )
        
        return self._rule_to_response(rule)

    async def get_user_escalation_rules(
        self,
        user_id: uuid.UUID,
    ) -> list[EscalationRuleResponse]:
        """Get user's escalation rules."""
        rules = await self.escalation_repo.get_user_rules(user_id)
        return [self._rule_to_response(r) for r in rules]

    async def update_escalation_rule(
        self,
        rule_id: uuid.UUID,
        data: EscalationRuleUpdate,
    ) -> Optional[EscalationRuleResponse]:
        """Update escalation rule."""
        update_data = data.model_dump(exclude_unset=True)
        
        if "escalation_levels" in update_data and update_data["escalation_levels"]:
            update_data["escalation_levels"] = [
                level.model_dump() if hasattr(level, "model_dump") else level
                for level in update_data["escalation_levels"]
            ]
        
        rule = await self.escalation_repo.update_rule(rule_id, **update_data)
        
        if not rule:
            return None
        
        return self._rule_to_response(rule)

    async def delete_escalation_rule(self, rule_id: uuid.UUID) -> bool:
        """Delete escalation rule."""
        return await self.escalation_repo.delete_rule(rule_id)

    # ==================== Notification Logs ====================

    async def get_notification_logs(
        self,
        user_id: uuid.UUID,
        filters: NotificationLogFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> NotificationLogListResponse:
        """Get notification logs with filters."""
        offset = (page - 1) * page_size
        
        logs, total = await self.log_repo.list_logs(
            user_id=user_id,
            status=filters.status.value if filters.status else None,
            channel=filters.channel.value if filters.channel else None,
            event_type=filters.event_type,
            account_id=filters.account_id,
            created_after=filters.created_after,
            created_before=filters.created_before,
            acknowledged=filters.acknowledged,
            limit=page_size,
            offset=offset,
        )
        
        return NotificationLogListResponse(
            logs=[self._log_to_info(l) for l in logs],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(logs)) < total,
        )

    async def get_delivery_timing_stats(
        self,
        user_id: Optional[uuid.UUID] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> DeliveryTimingResponse:
        """Get delivery timing statistics.
        
        Requirements: 23.1 - Track delivery within 60 seconds
        """
        stats = await self.log_repo.get_delivery_stats(
            user_id, created_after, created_before
        )
        
        return DeliveryTimingResponse(
            stats=DeliveryTimingStats(
                total_notifications=stats["total_notifications"],
                delivered_count=stats["delivered_count"],
                failed_count=stats["failed_count"],
                avg_delivery_time_seconds=stats["avg_delivery_time_seconds"],
                max_delivery_time_seconds=stats["max_delivery_time_seconds"],
                min_delivery_time_seconds=stats["min_delivery_time_seconds"],
                within_sla_count=stats["within_sla_count"],
                sla_compliance_percent=stats["sla_compliance_percent"],
                sla_threshold_seconds=self.SLA_THRESHOLD_SECONDS,
            ),
            generated_at=datetime.utcnow(),
        )

    # ==================== Helper Methods ====================

    def _preference_to_response(self, preference) -> NotificationPreferenceResponse:
        """Convert preference model to response schema."""
        return NotificationPreferenceResponse(
            id=preference.id,
            user_id=preference.user_id,
            account_id=preference.account_id,
            event_type=preference.event_type,
            email_enabled=preference.email_enabled,
            sms_enabled=preference.sms_enabled,
            slack_enabled=preference.slack_enabled,
            telegram_enabled=preference.telegram_enabled,
            email_address=preference.email_address,
            phone_number=preference.phone_number,
            slack_webhook_url=preference.slack_webhook_url,
            telegram_chat_id=preference.telegram_chat_id,
            batch_enabled=preference.batch_enabled,
            batch_interval_seconds=preference.batch_interval_seconds,
            quiet_hours_enabled=preference.quiet_hours_enabled,
            quiet_hours_start=preference.quiet_hours_start,
            quiet_hours_end=preference.quiet_hours_end,
            created_at=preference.created_at,
            updated_at=preference.updated_at,
        )

    def _rule_to_response(self, rule) -> EscalationRuleResponse:
        """Convert rule model to response schema."""
        return EscalationRuleResponse(
            id=rule.id,
            user_id=rule.user_id,
            name=rule.name,
            event_types=rule.event_types,
            escalation_levels=rule.escalation_levels,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    def _log_to_info(self, log) -> NotificationLogInfo:
        """Convert log model to info schema."""
        return NotificationLogInfo(
            id=log.id,
            user_id=log.user_id,
            account_id=log.account_id,
            event_type=log.event_type,
            event_id=log.event_id,
            title=log.title,
            message=log.message,
            channel=log.channel,
            recipient=log.recipient,
            priority=log.priority,
            status=log.status,
            created_at=log.created_at,
            queued_at=log.queued_at,
            sent_at=log.sent_at,
            delivered_at=log.delivered_at,
            delivery_time_seconds=log.delivery_time_seconds,
            attempts=log.attempts,
            last_error=log.last_error,
            acknowledged=log.acknowledged,
            acknowledged_at=log.acknowledged_at,
            response_time_seconds=log.response_time_seconds,
            is_batched=log.is_batched,
            is_escalated=log.is_escalated,
            escalation_level=log.escalation_level,
        )


# Standalone functions for delivery timing validation

def is_delivered_within_sla(
    created_at: datetime,
    delivered_at: datetime,
    sla_seconds: float = 60.0,
) -> bool:
    """Check if notification was delivered within SLA.
    
    Requirements: 23.1 - Deliver within 60 seconds
    
    Args:
        created_at: When notification was created
        delivered_at: When notification was delivered
        sla_seconds: SLA threshold in seconds (default 60)
        
    Returns:
        True if delivered within SLA, False otherwise
    """
    if not created_at or not delivered_at:
        return False
    
    delivery_time = (delivered_at - created_at).total_seconds()
    return delivery_time <= sla_seconds


def calculate_delivery_time(
    created_at: datetime,
    delivered_at: datetime,
) -> float:
    """Calculate delivery time in seconds.
    
    Args:
        created_at: When notification was created
        delivered_at: When notification was delivered
        
    Returns:
        Delivery time in seconds
    """
    if not created_at or not delivered_at:
        return 0.0
    
    return (delivered_at - created_at).total_seconds()
