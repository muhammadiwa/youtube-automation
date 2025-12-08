"""Audit logging for sensitive actions."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class AuditAction(str, Enum):
    """Types of auditable actions."""

    # Authentication
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"

    # Password
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"

    # 2FA
    TWO_FA_SETUP = "2fa_setup"
    TWO_FA_ENABLE = "2fa_enable"
    TWO_FA_DISABLE = "2fa_disable"
    TWO_FA_BACKUP_REGENERATE = "2fa_backup_regenerate"

    # Account
    ACCOUNT_UPDATE = "account_update"
    ACCOUNT_DELETE = "account_delete"

    # YouTube Account
    YOUTUBE_ACCOUNT_CONNECT = "youtube_account_connect"
    YOUTUBE_ACCOUNT_DISCONNECT = "youtube_account_disconnect"
    YOUTUBE_TOKEN_REFRESH = "youtube_token_refresh"

    # Admin
    ADMIN_ACTION = "admin_action"


class AuditLog(Base):
    """Audit log model for tracking sensitive actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class AuditLogEntry(BaseModel):
    """Pydantic model for audit log entries."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    details: dict | None
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime


class AuditLogger:
    """In-memory audit logger for tracking sensitive actions.

    In production, this would write to database and/or external logging service.
    """

    _logs: list[AuditLogEntry] = []

    @classmethod
    def log(
        cls,
        action: AuditAction | str,
        user_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogEntry:
        """Log an audit event.

        Args:
            action: Type of action being logged
            user_id: User performing the action (if known)
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            AuditLogEntry: The created log entry
        """
        action_str = action.value if isinstance(action, AuditAction) else action

        entry = AuditLogEntry(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action_str,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )

        cls._logs.append(entry)
        return entry

    @classmethod
    def get_logs(
        cls,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get audit logs with optional filtering.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            limit: Maximum number of logs to return

        Returns:
            list[AuditLogEntry]: Matching log entries
        """
        logs = cls._logs

        if user_id is not None:
            logs = [log for log in logs if log.user_id == user_id]

        if action is not None:
            logs = [log for log in logs if log.action == action]

        # Return most recent first
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    @classmethod
    def get_logs_for_user(cls, user_id: uuid.UUID, limit: int = 100) -> list[AuditLogEntry]:
        """Get all audit logs for a specific user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of logs to return

        Returns:
            list[AuditLogEntry]: User's audit log entries
        """
        return cls.get_logs(user_id=user_id, limit=limit)

    @classmethod
    def get_logs_by_action(cls, action: str, limit: int = 100) -> list[AuditLogEntry]:
        """Get all audit logs for a specific action type.

        Args:
            action: Action type to filter by
            limit: Maximum number of logs to return

        Returns:
            list[AuditLogEntry]: Matching audit log entries
        """
        return cls.get_logs(action=action, limit=limit)

    @classmethod
    def clear(cls) -> None:
        """Clear all logs (for testing)."""
        cls._logs.clear()

    @classmethod
    def count(cls) -> int:
        """Get total number of logs.

        Returns:
            int: Number of log entries
        """
        return len(cls._logs)


# Convenience functions for common audit events
def audit_login(
    user_id: uuid.UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
) -> AuditLogEntry:
    """Log a login attempt."""
    action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
    return AuditLogger.log(
        action=action,
        user_id=user_id,
        details={"success": success},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def audit_logout(
    user_id: uuid.UUID,
    ip_address: str | None = None,
) -> AuditLogEntry:
    """Log a logout."""
    return AuditLogger.log(
        action=AuditAction.LOGOUT,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_password_change(
    user_id: uuid.UUID,
    ip_address: str | None = None,
) -> AuditLogEntry:
    """Log a password change."""
    return AuditLogger.log(
        action=AuditAction.PASSWORD_CHANGE,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_2fa_action(
    user_id: uuid.UUID,
    action: AuditAction,
    ip_address: str | None = None,
) -> AuditLogEntry:
    """Log a 2FA-related action."""
    return AuditLogger.log(
        action=action,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_sensitive_action(
    user_id: uuid.UUID,
    action: str,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLogEntry:
    """Log any sensitive action."""
    return AuditLogger.log(
        action=action,
        user_id=user_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
