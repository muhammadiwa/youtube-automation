"""Admin audit logging service.

Requirements: 1.3, 8.1 - Log all admin actions with admin_id, timestamp, IP, action details
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from app.modules.auth.audit import AuditLogger, AuditAction, AuditLogEntry


class AdminAuditEvent(str, Enum):
    """Types of admin audit events."""
    
    # Authentication events
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGIN_FAILED = "admin_login_failed"
    ADMIN_2FA_VERIFIED = "admin_2fa_verified"
    ADMIN_2FA_FAILED = "admin_2fa_failed"
    ADMIN_SESSION_CREATED = "admin_session_created"
    ADMIN_SESSION_EXPIRED = "admin_session_expired"
    ADMIN_ACCESS_DENIED = "admin_access_denied"
    
    # Admin management events
    ADMIN_CREATED = "admin_created"
    ADMIN_UPDATED = "admin_updated"
    ADMIN_DEACTIVATED = "admin_deactivated"
    ADMIN_PERMISSIONS_CHANGED = "admin_permissions_changed"
    
    # User management events
    USER_VIEWED = "user_viewed"
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    USER_IMPERSONATED = "user_impersonated"
    USER_PASSWORD_RESET = "user_password_reset"
    USER_WARNING_ISSUED = "user_warning_issued"
    
    # Billing events
    SUBSCRIPTION_MODIFIED = "subscription_modified"
    REFUND_PROCESSED = "refund_processed"
    DISCOUNT_CODE_CREATED = "discount_code_created"
    
    # Moderation events
    CONTENT_APPROVED = "content_approved"
    CONTENT_REMOVED = "content_removed"
    
    # System events
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    FEATURE_FLAG_TOGGLED = "feature_flag_toggled"
    
    # Compliance events
    DATA_EXPORT_PROCESSED = "data_export_processed"
    DELETION_REQUEST_PROCESSED = "deletion_request_processed"
    DELETION_REQUEST_CANCELLED = "deletion_request_cancelled"
    AUDIT_LOG_EXPORTED = "audit_log_exported"
    
    # Terms of Service events (Requirements 15.4)
    TERMS_CREATED = "terms_created"
    TERMS_ACTIVATED = "terms_activated"
    
    # Compliance Report events (Requirements 15.5)
    COMPLIANCE_REPORT_GENERATED = "compliance_report_generated"
    
    # Backup & Disaster Recovery events (Requirements 18.1-18.5)
    BACKUP_CREATED = "backup_created"
    BACKUP_COMPLETED = "backup_completed"
    BACKUP_FAILED = "backup_failed"
    BACKUP_SCHEDULE_UPDATED = "backup_schedule_updated"
    RESTORE_REQUESTED = "restore_requested"
    RESTORE_APPROVED = "restore_approved"
    RESTORE_REJECTED = "restore_rejected"
    RESTORE_COMPLETED = "restore_completed"
    RESTORE_FAILED = "restore_failed"


class AdminAuditEntry(BaseModel):
    """Schema for admin audit log entry."""
    
    id: uuid.UUID
    admin_id: uuid.UUID
    admin_user_id: uuid.UUID
    event: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime


class AdminAuditService:
    """Service for logging admin actions.
    
    Requirements: 1.3 - Log all admin actions with admin_id, timestamp, IP, action details
    
    This service provides comprehensive audit logging for all admin operations,
    ensuring compliance with audit requirements.
    """
    
    @classmethod
    def log(
        cls,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an admin action (in-memory only, for backward compatibility).
        
        Args:
            admin_id: Admin record ID
            admin_user_id: User ID of the admin
            event: Type of admin event
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource being acted upon
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuditLogEntry: The created audit log entry
        """
        # Build comprehensive details
        audit_details = {
            "event": event.value,
            "admin_id": str(admin_id),
        }
        
        if resource_type:
            audit_details["resource_type"] = resource_type
        if resource_id:
            audit_details["resource_id"] = str(resource_id)
        if details:
            audit_details.update(details)
        
        # Log using the central AuditLogger
        return AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_user_id,
            details=audit_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @classmethod
    async def log_to_db(
        cls,
        session,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log an admin action to database.
        
        Args:
            session: Database session
            admin_id: Admin record ID
            admin_user_id: User ID of the admin
            event: Type of admin event
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource being acted upon
            details: Additional details about the action
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuditLog: The created database audit log entry
        """
        from app.modules.auth.audit import AuditLog
        
        # Build comprehensive details
        audit_details = {
            "event": event.value,
            "admin_id": str(admin_id),
        }
        
        if resource_type:
            audit_details["resource_type"] = resource_type
        if resource_id:
            audit_details["resource_id"] = str(resource_id)
        if details:
            audit_details.update(details)
        
        # Create database entry
        db_log = AuditLog(
            user_id=admin_user_id,
            action=AuditAction.ADMIN_ACTION.value,
            details=audit_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        session.add(db_log)
        await session.commit()
        await session.refresh(db_log)
        
        return db_log
    
    @classmethod
    def log_authentication(
        cls,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        success: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an admin authentication event.
        
        Args:
            admin_id: Admin record ID
            admin_user_id: User ID of the admin
            event: Authentication event type
            success: Whether authentication succeeded
            reason: Reason for failure (if applicable)
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuditLogEntry: The created audit log entry
        """
        details = {
            "success": success,
        }
        if reason:
            details["reason"] = reason
        
        return cls.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @classmethod
    def log_user_action(
        cls,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        target_user_id: uuid.UUID,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log an admin action on a user.
        
        Args:
            admin_id: Admin record ID
            admin_user_id: User ID of the admin
            event: User action event type
            target_user_id: ID of the user being acted upon
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuditLogEntry: The created audit log entry
        """
        action_details = details or {}
        action_details["target_user_id"] = str(target_user_id)
        
        return cls.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            resource_type="user",
            resource_id=str(target_user_id),
            details=action_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @classmethod
    def log_config_change(
        cls,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """Log a system configuration change.
        
        Args:
            admin_id: Admin record ID
            admin_user_id: User ID of the admin
            config_key: Configuration key being changed
            old_value: Previous value
            new_value: New value
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            AuditLogEntry: The created audit log entry
        """
        return cls.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=AdminAuditEvent.SYSTEM_CONFIG_CHANGED,
            resource_type="config",
            resource_id=config_key,
            details={
                "config_key": config_key,
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    @classmethod
    def get_admin_logs(
        cls,
        admin_user_id: Optional[uuid.UUID] = None,
        event: Optional[AdminAuditEvent] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get admin audit logs with optional filtering.
        
        Args:
            admin_user_id: Filter by admin user ID
            event: Filter by event type
            limit: Maximum number of logs to return
            
        Returns:
            list[AuditLogEntry]: Matching audit log entries
        """
        logs = AuditLogger.get_logs(
            user_id=admin_user_id,
            action=AuditAction.ADMIN_ACTION.value,
            limit=limit,
        )
        
        # Filter by event if specified
        if event:
            logs = [
                log for log in logs
                if log.details and log.details.get("event") == event.value
            ]
        
        return logs
