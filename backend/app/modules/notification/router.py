"""FastAPI router for Notification Service.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.notification.service import NotificationService
from app.modules.notification.schemas import (
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationLogListResponse,
    NotificationLogFilters,
    NotificationAcknowledgeRequest,
    NotificationAcknowledgeResponse,
    EscalationRuleCreate,
    EscalationRuleUpdate,
    EscalationRuleResponse,
    DeliveryTimingResponse,
    NotificationStatus,
    NotificationChannel,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Dependency to get notification service."""
    return NotificationService(db)


# ==================== User Notifications (Frontend API) ====================

@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    type: Optional[str] = Query(None),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    """Get notifications for the current user.
    
    Returns notifications from notification_logs table.
    """
    from sqlalchemy import select, func, desc
    from app.modules.notification.models import NotificationLog
    
    # For now, show all notifications (no user filter)
    # In production, this should filter by authenticated user
    user_id = None
    
    # Build query
    query = select(NotificationLog).order_by(desc(NotificationLog.created_at))
    
    if user_id:
        query = query.where(NotificationLog.user_id == user_id)
    
    if unread_only:
        query = query.where(NotificationLog.acknowledged == False)
    
    if type:
        query = query.where(NotificationLog.event_type == type)
    
    # Get total count
    count_query = select(func.count()).select_from(NotificationLog)
    if user_id:
        count_query = count_query.where(NotificationLog.user_id == user_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get unread count
    unread_query = select(func.count()).select_from(NotificationLog).where(NotificationLog.acknowledged == False)
    if user_id:
        unread_query = unread_query.where(NotificationLog.user_id == user_id)
    
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Map to response format
    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "type": log.event_type.replace(".", "_") if log.event_type else "system_alert",
            "title": log.title,
            "message": log.message,
            "priority": log.priority,
            "read": log.acknowledged,
            "action_url": log.payload.get("action_url") if log.payload else None,
            "metadata": log.payload,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
    
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
    }


@router.get("/unread/count")
async def get_unread_count(
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications."""
    from sqlalchemy import select, func
    from app.modules.notification.models import NotificationLog
    
    query = select(func.count()).select_from(NotificationLog).where(NotificationLog.acknowledged == False)
    result = await db.execute(query)
    count = result.scalar() or 0
    
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    from sqlalchemy import select
    from app.modules.notification.models import NotificationLog
    
    result = await db.execute(
        select(NotificationLog).where(NotificationLog.id == notification_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    log.acknowledged = True
    log.acknowledged_at = datetime.utcnow()
    await db.commit()
    
    return {
        "id": str(log.id),
        "user_id": str(log.user_id),
        "type": log.event_type.replace(".", "_") if log.event_type else "system_alert",
        "title": log.title,
        "message": log.message,
        "priority": log.priority,
        "read": log.acknowledged,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.post("/read-all")
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    from sqlalchemy import update
    from app.modules.notification.models import NotificationLog
    
    await db.execute(
        update(NotificationLog)
        .where(NotificationLog.acknowledged == False)
        .values(acknowledged=True, acknowledged_at=datetime.utcnow())
    )
    await db.commit()
    
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    from sqlalchemy import select, delete
    from app.modules.notification.models import NotificationLog
    
    result = await db.execute(
        select(NotificationLog).where(NotificationLog.id == notification_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await db.execute(
        delete(NotificationLog).where(NotificationLog.id == notification_id)
    )
    await db.commit()
    
    return {"message": "Notification deleted"}


@router.delete("/clear")
async def clear_all_notifications(
    db: AsyncSession = Depends(get_db),
):
    """Clear all notifications."""
    from sqlalchemy import delete
    from app.modules.notification.models import NotificationLog
    
    await db.execute(delete(NotificationLog))
    await db.commit()
    
    return {"message": "All notifications cleared"}


# ==================== Send Notifications (23.1) ====================

@router.post("/send", response_model=NotificationSendResponse)
async def send_notification(
    request: NotificationSendRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """Send a notification to a user.
    
    Requirements: 23.1 - Deliver within 60 seconds
    """
    return await service.send_notification(request)


# ==================== Notification Preferences (23.2) ====================

@router.post("/preferences", response_model=NotificationPreferenceResponse)
async def create_preference(
    user_id: uuid.UUID,
    data: NotificationPreferenceCreate,
    service: NotificationService = Depends(get_notification_service),
):
    """Create notification preference for a user.
    
    Requirements: 23.2 - Store settings per account and event type
    """
    return await service.create_preference(user_id, data)


@router.get("/preferences/{user_id}", response_model=list[NotificationPreferenceResponse])
async def get_user_preferences(
    user_id: uuid.UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account"),
    service: NotificationService = Depends(get_notification_service),
):
    """Get user's notification preferences.
    
    Requirements: 23.2
    """
    return await service.get_user_preferences(user_id, event_type, account_id)


@router.put("/preferences/{preference_id}", response_model=NotificationPreferenceResponse)
async def update_preference(
    preference_id: uuid.UUID,
    data: NotificationPreferenceUpdate,
    service: NotificationService = Depends(get_notification_service),
):
    """Update notification preference.
    
    Requirements: 23.2
    """
    result = await service.update_preference(preference_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Preference not found")
    return result


@router.delete("/preferences/{preference_id}")
async def delete_preference(
    preference_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    """Delete notification preference."""
    success = await service.delete_preference(preference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"message": "Preference deleted"}


# ==================== Notification Logs ====================

@router.get("/logs/{user_id}", response_model=NotificationLogListResponse)
async def get_notification_logs(
    user_id: uuid.UUID,
    status: Optional[NotificationStatus] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    event_type: Optional[str] = Query(None),
    account_id: Optional[uuid.UUID] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification logs for a user."""
    filters = NotificationLogFilters(
        status=status,
        channel=channel,
        event_type=event_type,
        account_id=account_id,
        created_after=created_after,
        created_before=created_before,
        acknowledged=acknowledged,
    )
    return await service.get_notification_logs(user_id, filters, page, page_size)


# ==================== Acknowledgment (23.5) ====================

@router.post("/acknowledge", response_model=NotificationAcknowledgeResponse)
async def acknowledge_notification(
    request: NotificationAcknowledgeRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """Acknowledge a notification.
    
    Requirements: 23.5 - Mark alerts resolved, log response time
    """
    result = await service.acknowledge_notification(request)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result


# ==================== Escalation Rules (23.4) ====================

@router.post("/escalation-rules", response_model=EscalationRuleResponse)
async def create_escalation_rule(
    user_id: uuid.UUID,
    data: EscalationRuleCreate,
    service: NotificationService = Depends(get_notification_service),
):
    """Create escalation rule.
    
    Requirements: 23.4 - Multi-channel escalation for critical issues
    """
    return await service.create_escalation_rule(user_id, data)


@router.get("/escalation-rules/{user_id}", response_model=list[EscalationRuleResponse])
async def get_escalation_rules(
    user_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    """Get user's escalation rules.
    
    Requirements: 23.4
    """
    return await service.get_user_escalation_rules(user_id)


@router.put("/escalation-rules/{rule_id}", response_model=EscalationRuleResponse)
async def update_escalation_rule(
    rule_id: uuid.UUID,
    data: EscalationRuleUpdate,
    service: NotificationService = Depends(get_notification_service),
):
    """Update escalation rule.
    
    Requirements: 23.4
    """
    result = await service.update_escalation_rule(rule_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found")
    return result


@router.delete("/escalation-rules/{rule_id}")
async def delete_escalation_rule(
    rule_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    """Delete escalation rule."""
    success = await service.delete_escalation_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


# ==================== Delivery Stats (23.1) ====================

@router.get("/stats/delivery", response_model=DeliveryTimingResponse)
async def get_delivery_stats(
    user_id: Optional[uuid.UUID] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification delivery timing statistics.
    
    Requirements: 23.1 - Track delivery within 60 seconds
    """
    return await service.get_delivery_timing_stats(
        user_id, created_after, created_before
    )


# ==================== Notification Channels ====================

@router.get("/channels")
async def get_notification_channels(
    db: AsyncSession = Depends(get_db),
):
    """Get available notification channels and their status.
    
    Returns list of channels with their enabled status.
    """
    # Return available channels
    # In production, this would check actual configuration status
    channels = [
        {
            "type": "email",
            "enabled": True,
            "config": {}
        },
        {
            "type": "telegram",
            "enabled": False,
            "config": {}
        }
    ]
    return channels


@router.post("/channels/{channel_type}")
async def configure_channel(
    channel_type: str,
    config: dict,
    db: AsyncSession = Depends(get_db),
):
    """Configure a notification channel.
    
    Args:
        channel_type: Type of channel (email, telegram)
        config: Channel-specific configuration
    """
    # Validate channel type
    valid_channels = ["email", "telegram", "slack", "sms"]
    if channel_type not in valid_channels:
        raise HTTPException(status_code=400, detail=f"Invalid channel type: {channel_type}")
    
    # In production, save config to database
    # For now, return success
    return {
        "type": channel_type,
        "enabled": True,
        "config": config
    }


@router.post("/channels/{channel_type}/test")
async def test_channel(
    channel_type: str,
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
):
    """Send a test notification to verify channel configuration.
    
    Args:
        channel_type: Type of channel to test (email, telegram)
    """
    from app.modules.notification.channels import (
        EmailChannel,
        TelegramChannel,
    )
    
    # Get test recipient from request or use default
    test_recipient = "test@example.com"
    
    if channel_type == "email":
        channel = EmailChannel()
        result = await channel.deliver(
            recipient=test_recipient,
            title="Test Notification",
            message="This is a test notification from YouTube Automation Platform.",
        )
    elif channel_type == "telegram":
        channel = TelegramChannel()
        result = await channel.deliver(
            recipient="test_chat_id",
            title="Test Notification",
            message="This is a test notification from YouTube Automation Platform.",
        )
    else:
        return {"success": False, "message": f"Channel {channel_type} not supported for testing"}
    
    return {
        "success": result.success,
        "message": "Test notification sent!" if result.success else result.error or "Failed to send"
    }


@router.delete("/channels/{channel_type}")
async def disable_channel(
    channel_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Disable a notification channel.
    
    Args:
        channel_type: Type of channel to disable
    """
    # In production, update database to disable channel
    return {"message": f"Channel {channel_type} disabled"}


# ==================== Batch Processing (23.3) ====================

@router.post("/batches/{user_id}/process")
async def process_batches(
    user_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    """Process pending notification batches for a user.
    
    Requirements: 23.3 - Batch simultaneous alerts
    """
    processed_count = await service.process_batches(user_id)
    return {"processed_count": processed_count}


# ==================== Escalation (23.4) ====================

@router.post("/escalate/{notification_id}")
async def escalate_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
):
    """Escalate a notification to the next level.
    
    Requirements: 23.4 - Multi-channel escalation
    """
    new_ids = await service.escalate_notification(notification_id)
    if new_ids is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot escalate: notification not found or not escalatable",
        )
    return {"escalated_notification_ids": new_ids}
