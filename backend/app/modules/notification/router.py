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
