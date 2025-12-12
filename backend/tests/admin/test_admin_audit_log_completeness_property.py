"""Property-based tests for admin audit log completeness.

**Feature: admin-panel, Property 3: Admin Audit Log Completeness**
**Validates: Requirements 1.3, 8.1**

For any admin action (create, update, delete, view sensitive data), an audit log entry 
SHALL be created containing admin_id, timestamp, ip_address, action, resource_type, 
resource_id, and details.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from hypothesis import given, settings, strategies as st, assume
import pytest


class AdminAuditEvent(str, Enum):
    """Types of admin audit events."""
    # Authentication events
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGIN_FAILED = "admin_login_failed"
    ADMIN_2FA_VERIFIED = "admin_2fa_verified"
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
    AUDIT_LOG_EXPORTED = "audit_log_exported"


@dataclass
class AuditLogEntry:
    """Audit log entry for admin actions."""
    id: uuid.UUID
    admin_id: uuid.UUID
    admin_user_id: uuid.UUID
    event: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


class AdminAuditLogger:
    """
    Audit logger for admin actions.
    
    This class implements the core logic for Property 3: Admin Audit Log Completeness.
    For any admin action, an audit log entry SHALL be created containing admin_id, 
    timestamp, ip_address, action, resource_type, resource_id, and details.
    """
    
    def __init__(self):
        """Initialize the audit logger."""
        self._logs: list[AuditLogEntry] = []
    
    def log(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Log an admin action.
        
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
        
        entry = AuditLogEntry(
            id=uuid.uuid4(),
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event.value,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=audit_details,
        )
        
        self._logs.append(entry)
        return entry
    
    def log_user_action(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        target_user_id: uuid.UUID,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Log an admin action on a user.
        
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
        
        return self.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            resource_type="user",
            resource_id=str(target_user_id),
            details=action_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_config_change(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogEntry:
        """
        Log a system configuration change.
        
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
        return self.log(
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
    
    def get_logs(self) -> list[AuditLogEntry]:
        """Get all audit logs."""
        return self._logs.copy()
    
    def get_logs_for_admin(self, admin_id: uuid.UUID) -> list[AuditLogEntry]:
        """Get audit logs for a specific admin."""
        return [log for log in self._logs if log.admin_id == admin_id]
    
    def clear(self) -> None:
        """Clear all logs (for testing)."""
        self._logs.clear()


def validate_audit_log_completeness(entry: AuditLogEntry) -> tuple[bool, list[str]]:
    """
    Validate that an audit log entry contains all required fields.
    
    Requirements 1.3, 8.1: Log all admin actions with admin_id, timestamp, 
    IP address, and action details.
    
    Args:
        entry: Audit log entry to validate
        
    Returns:
        tuple: (is_valid, list of missing/invalid fields)
    """
    errors = []
    
    # Required fields per Requirements 1.3, 8.1
    if entry.id is None:
        errors.append("id is required")
    
    if entry.admin_id is None:
        errors.append("admin_id is required")
    
    if entry.admin_user_id is None:
        errors.append("admin_user_id is required")
    
    if entry.timestamp is None:
        errors.append("timestamp is required")
    
    if not entry.event:
        errors.append("event/action is required")
    
    # Details must contain the event type
    if entry.details is None or "event" not in entry.details:
        errors.append("details must contain event type")
    
    # Details must contain admin_id
    if entry.details is None or "admin_id" not in entry.details:
        errors.append("details must contain admin_id")
    
    return (len(errors) == 0, errors)


# Strategies for generating test data
uuid_strategy = st.uuids()
event_strategy = st.sampled_from(list(AdminAuditEvent))
ip_address_strategy = st.one_of(
    st.none(),
    st.from_regex(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", fullmatch=True),
)
user_agent_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Zs"))),
)
resource_type_strategy = st.one_of(
    st.none(),
    st.sampled_from(["user", "admin", "subscription", "payment", "content", "config", "report"]),
)
config_key_strategy = st.sampled_from([
    "jwt_access_token_expire_minutes",
    "password_min_length",
    "max_login_attempts",
    "ai_monthly_budget_usd",
    "max_concurrent_streams",
])
config_value_strategy = st.one_of(
    st.integers(min_value=0, max_value=10000),
    st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.text(min_size=1, max_size=50),
)


class TestAdminAuditLogCompleteness:
    """
    Property tests for admin audit log completeness.
    
    **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
    **Validates: Requirements 1.3, 8.1**
    """

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
        ip_address=ip_address_strategy,
        user_agent=user_agent_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_contains_required_fields(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action, the audit log entry SHALL contain admin_id, 
        timestamp, action (event), and details with event type.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        is_valid, errors = validate_audit_log_completeness(entry)
        
        assert is_valid, f"Audit log entry missing required fields: {errors}"
        assert entry.admin_id == admin_id
        assert entry.admin_user_id == admin_user_id
        assert entry.event == event.value
        assert entry.timestamp is not None
        assert entry.details["event"] == event.value
        assert entry.details["admin_id"] == str(admin_id)

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
        resource_type=st.sampled_from(["user", "admin", "subscription", "payment", "content"]),
        resource_id=uuid_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_contains_resource_info(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action on a resource, the audit log entry SHALL contain
        resource_type and resource_id.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            resource_type=resource_type,
            resource_id=str(resource_id),
        )
        
        assert entry.resource_type == resource_type
        assert entry.resource_id == str(resource_id)
        assert entry.details["resource_type"] == resource_type
        assert entry.details["resource_id"] == str(resource_id)

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        target_user_id=uuid_strategy,
        event=st.sampled_from([
            AdminAuditEvent.USER_VIEWED,
            AdminAuditEvent.USER_SUSPENDED,
            AdminAuditEvent.USER_ACTIVATED,
            AdminAuditEvent.USER_IMPERSONATED,
            AdminAuditEvent.USER_PASSWORD_RESET,
            AdminAuditEvent.USER_WARNING_ISSUED,
        ]),
        ip_address=ip_address_strategy,
    )
    @settings(max_examples=100)
    def test_user_action_audit_log_completeness(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        event: AdminAuditEvent,
        ip_address: Optional[str],
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action on a user, the audit log entry SHALL contain
        target_user_id, resource_type='user', and resource_id.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log_user_action(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            target_user_id=target_user_id,
            ip_address=ip_address,
        )
        
        is_valid, errors = validate_audit_log_completeness(entry)
        
        assert is_valid, f"Audit log entry missing required fields: {errors}"
        assert entry.resource_type == "user"
        assert entry.resource_id == str(target_user_id)
        assert entry.details["target_user_id"] == str(target_user_id)

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        config_key=config_key_strategy,
        old_value=config_value_strategy,
        new_value=config_value_strategy,
        ip_address=ip_address_strategy,
    )
    @settings(max_examples=100)
    def test_config_change_audit_log_completeness(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str],
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any system configuration change, the audit log entry SHALL contain
        config_key, old_value, and new_value.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log_config_change(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            config_key=config_key,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        
        is_valid, errors = validate_audit_log_completeness(entry)
        
        assert is_valid, f"Audit log entry missing required fields: {errors}"
        assert entry.event == AdminAuditEvent.SYSTEM_CONFIG_CHANGED.value
        assert entry.resource_type == "config"
        assert entry.resource_id == config_key
        assert entry.details["config_key"] == config_key
        assert entry.details["old_value"] == str(old_value)
        assert entry.details["new_value"] == str(new_value)

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        num_actions=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_all_actions_logged(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        num_actions: int,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any sequence of admin actions, ALL actions SHALL be logged.
        """
        logger = AdminAuditLogger()
        events = list(AdminAuditEvent)
        
        for i in range(num_actions):
            event = events[i % len(events)]
            logger.log(
                admin_id=admin_id,
                admin_user_id=admin_user_id,
                event=event,
            )
        
        logs = logger.get_logs()
        assert len(logs) == num_actions

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
    )
    @settings(max_examples=100)
    def test_timestamp_is_set(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action, the timestamp SHALL be set to the current time.
        """
        logger = AdminAuditLogger()
        before = datetime.utcnow()
        
        entry = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
        )
        
        after = datetime.utcnow()
        
        assert entry.timestamp is not None
        assert before <= entry.timestamp <= after

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
        ip_address=st.from_regex(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            fullmatch=True
        ),
    )
    @settings(max_examples=100)
    def test_ip_address_preserved(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        ip_address: str,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action with IP address, the IP address SHALL be preserved
        in the audit log entry.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            ip_address=ip_address,
        )
        
        assert entry.ip_address == ip_address

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
        extra_details=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L",))),
            values=st.one_of(st.text(min_size=1, max_size=50), st.integers(), st.booleans()),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_additional_details_preserved(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
        extra_details: dict[str, Any],
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action with additional details, all details SHALL be
        preserved in the audit log entry.
        """
        logger = AdminAuditLogger()
        
        entry = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
            details=extra_details,
        )
        
        # All extra details should be in the entry details
        for key, value in extra_details.items():
            assert key in entry.details
            assert entry.details[key] == value

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
    )
    @settings(max_examples=100)
    def test_logs_retrievable_by_admin(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin, their audit logs SHALL be retrievable by admin_id.
        """
        logger = AdminAuditLogger()
        
        # Log some actions for this admin
        for event in [AdminAuditEvent.ADMIN_LOGIN, AdminAuditEvent.USER_VIEWED]:
            logger.log(
                admin_id=admin_id,
                admin_user_id=admin_user_id,
                event=event,
            )
        
        # Log action for different admin
        other_admin_id = uuid.uuid4()
        logger.log(
            admin_id=other_admin_id,
            admin_user_id=uuid.uuid4(),
            event=AdminAuditEvent.ADMIN_LOGIN,
        )
        
        # Retrieve logs for our admin
        admin_logs = logger.get_logs_for_admin(admin_id)
        
        assert len(admin_logs) == 2
        assert all(log.admin_id == admin_id for log in admin_logs)

    @given(
        admin_id=uuid_strategy,
        admin_user_id=uuid_strategy,
        event=event_strategy,
    )
    @settings(max_examples=100)
    def test_unique_log_id(
        self,
        admin_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        event: AdminAuditEvent,
    ) -> None:
        """
        **Feature: admin-panel, Property 3: Admin Audit Log Completeness**
        
        For any admin action, the audit log entry SHALL have a unique ID.
        """
        logger = AdminAuditLogger()
        
        entry1 = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
        )
        
        entry2 = logger.log(
            admin_id=admin_id,
            admin_user_id=admin_user_id,
            event=event,
        )
        
        assert entry1.id != entry2.id
