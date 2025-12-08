"""Notification module for multi-channel delivery.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

from app.modules.notification.router import router as notification_router
from app.modules.notification.service import NotificationService
from app.modules.notification.models import (
    NotificationPreference,
    NotificationLog,
    NotificationBatch,
    EscalationRule,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    EventType,
)

__all__ = [
    "notification_router",
    "NotificationService",
    "NotificationPreference",
    "NotificationLog",
    "NotificationBatch",
    "EscalationRule",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationStatus",
    "EventType",
]
