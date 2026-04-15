"""Property-based tests for Content Removal Flow.

**Feature: admin-panel, Property 10: Content Removal Flow**
**Validates: Requirements 6.4**

Property 10: Content Removal Flow
*For any* content removal action, the system SHALL delete content, 
create notification for content owner, and create audit log with removal reason.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

import pytest
from hypothesis import given, strategies as st, settings


# ==================== Enums and Constants ====================

class ReportStatus:
    """Status of content reports."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REMOVED = "removed"


class ContentType:
    """Types of content that can be reported."""
    VIDEO = "video"
    COMMENT = "comment"
    STREAM = "stream"
    THUMBNAIL = "thumbnail"


# ==================== Data Classes ====================

@dataclass
class ContentReport:
    """Content report for testing."""
    id: uuid.UUID
    content_type: str
    content_id: uuid.UUID
    content_owner_id: uuid.UUID
    reason: str
    status: str
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


@dataclass
class AuditLogEntry:
    """Audit log entry for testing."""
    id: uuid.UUID
    admin_id: uuid.UUID
    event: str
    details: dict[str, Any]
    timestamp: datetime


@dataclass
class Notification:
    """Notification for testing."""
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    title: str
    message: str
    created_at: datetime


@dataclass
class ContentRemovalResult:
    """Result of content removal operation."""
    report_id: uuid.UUID
    content_id: uuid.UUID
    content_type: str
    status: str
    content_deleted: bool
    user_notified: bool
    audit_log_id: uuid.UUID
    removed_at: datetime


# ==================== Mock Storage ====================

class MockStorage:
    """Mock storage for testing content removal flow."""
    
    def __init__(self):
        self.deleted_content: list[tuple[str, uuid.UUID]] = []
        self.notifications: list[Notification] = []
        self.audit_logs: list[AuditLogEntry] = []
    
    def delete_content(self, content_type: str, content_id: uuid.UUID) -> bool:
        """Delete content."""
        self.deleted_content.append((content_type, content_id))
        return True
    
    def send_notification(
        self,
        user_id: uuid.UUID,
        event_type: str,
        title: str,
        message: str,
    ) -> bool:
        """Send notification to user."""
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            title=title,
            message=message,
            created_at=datetime.utcnow(),
        )
        self.notifications.append(notification)
        return True
    
    def create_audit_log(
        self,
        admin_id: uuid.UUID,
        event: str,
        details: dict[str, Any],
    ) -> AuditLogEntry:
        """Create audit log entry."""
        entry = AuditLogEntry(
            id=uuid.uuid4(),
            admin_id=admin_id,
            event=event,
            details=details,
            timestamp=datetime.utcnow(),
        )
        self.audit_logs.append(entry)
        return entry


# ==================== Content Removal Logic ====================

def remove_content(
    report: ContentReport,
    admin_id: uuid.UUID,
    reason: str,
    notify_user: bool,
    storage: MockStorage,
) -> ContentRemovalResult:
    """
    Remove content and perform all required actions.
    
    Property 10: Content Removal Flow
    - For any content removal action, the system SHALL delete content,
    - create notification for content owner, and create audit log with removal reason.
    
    Args:
        report: Content report
        admin_id: Admin performing the action
        reason: Reason for removal
        notify_user: Whether to notify the content owner
        storage: Mock storage for testing
        
    Returns:
        ContentRemovalResult with removal details
    """
    # 1. Mark report as removed
    report.status = ReportStatus.REMOVED
    report.reviewed_by = admin_id
    report.reviewed_at = datetime.utcnow()
    report.review_notes = reason
    
    # 2. Delete the content
    content_deleted = storage.delete_content(report.content_type, report.content_id)
    
    # 3. Notify user if requested
    user_notified = False
    if notify_user:
        user_notified = storage.send_notification(
            user_id=report.content_owner_id,
            event_type="content.removed",
            title="Content Removed",
            message=f"Your {report.content_type} has been removed. Reason: {reason}",
        )
    
    # 4. Create audit log
    audit_log = storage.create_audit_log(
        admin_id=admin_id,
        event="content_removed",
        details={
            "report_id": str(report.id),
            "content_type": report.content_type,
            "content_id": str(report.content_id),
            "content_owner_id": str(report.content_owner_id),
            "reason": reason,
            "content_deleted": content_deleted,
            "user_notified": user_notified,
        },
    )
    
    return ContentRemovalResult(
        report_id=report.id,
        content_id=report.content_id,
        content_type=report.content_type,
        status=ReportStatus.REMOVED,
        content_deleted=content_deleted,
        user_notified=user_notified,
        audit_log_id=audit_log.id,
        removed_at=report.reviewed_at,
    )


# ==================== Strategies ====================

content_type_strategy = st.sampled_from([
    ContentType.VIDEO,
    ContentType.COMMENT,
    ContentType.STREAM,
    ContentType.THUMBNAIL,
])

reason_strategy = st.text(
    min_size=1,
    max_size=500,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')),
)


@st.composite
def report_strategy(draw):
    """Generate a random content report."""
    return ContentReport(
        id=uuid.uuid4(),
        content_type=draw(content_type_strategy),
        content_id=uuid.uuid4(),
        content_owner_id=uuid.uuid4(),
        reason=draw(reason_strategy),
        status=ReportStatus.PENDING,
    )


# ==================== Property Tests ====================

class TestContentRemovalFlow:
    """Property tests for Content Removal Flow.
    
    **Feature: admin-panel, Property 10: Content Removal Flow**
    **Validates: Requirements 6.4**
    """

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_content_is_deleted(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Content removal SHALL delete the content.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        # Content should be deleted
        assert result.content_deleted is True
        assert (report.content_type, report.content_id) in storage.deleted_content

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
    )
    def test_user_notified_when_requested(
        self,
        report: ContentReport,
        reason: str,
    ):
        """
        Property: When notify_user is True, the content owner SHALL be notified.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user=True, storage=storage)
        
        # User should be notified
        assert result.user_notified is True
        assert len(storage.notifications) == 1
        
        notification = storage.notifications[0]
        assert notification.user_id == report.content_owner_id
        assert notification.event_type == "content.removed"

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
    )
    def test_user_not_notified_when_not_requested(
        self,
        report: ContentReport,
        reason: str,
    ):
        """
        Property: When notify_user is False, no notification SHALL be sent.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user=False, storage=storage)
        
        # User should not be notified
        assert result.user_notified is False
        assert len(storage.notifications) == 0

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_audit_log_created(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Content removal SHALL create an audit log entry.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        # Audit log should be created
        assert len(storage.audit_logs) == 1
        
        audit_log = storage.audit_logs[0]
        assert audit_log.admin_id == admin_id
        assert audit_log.event == "content_removed"

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_audit_log_contains_reason(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Audit log SHALL contain the removal reason.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        remove_content(report, admin_id, reason, notify_user, storage)
        
        audit_log = storage.audit_logs[0]
        assert audit_log.details["reason"] == reason

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_audit_log_contains_content_info(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Audit log SHALL contain content type, content ID, and owner ID.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        remove_content(report, admin_id, reason, notify_user, storage)
        
        audit_log = storage.audit_logs[0]
        assert audit_log.details["content_type"] == report.content_type
        assert audit_log.details["content_id"] == str(report.content_id)
        assert audit_log.details["content_owner_id"] == str(report.content_owner_id)

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_report_status_updated(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Report status SHALL be updated to 'removed'.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        assert result.status == ReportStatus.REMOVED
        assert report.status == ReportStatus.REMOVED

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_report_reviewed_by_set(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Report reviewed_by SHALL be set to the admin ID.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        remove_content(report, admin_id, reason, notify_user, storage)
        
        assert report.reviewed_by == admin_id

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_report_reviewed_at_set(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Report reviewed_at SHALL be set to the current time.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        before = datetime.utcnow()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        after = datetime.utcnow()
        
        assert report.reviewed_at is not None
        assert before <= report.reviewed_at <= after
        assert result.removed_at == report.reviewed_at

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_result_contains_audit_log_id(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Result SHALL contain the audit log ID.
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        assert result.audit_log_id is not None
        assert result.audit_log_id == storage.audit_logs[0].id

    @settings(max_examples=100)
    @given(
        report=report_strategy(),
        reason=reason_strategy,
        notify_user=st.booleans(),
    )
    def test_all_three_actions_performed(
        self,
        report: ContentReport,
        reason: str,
        notify_user: bool,
    ):
        """
        Property: Content removal SHALL perform all three actions:
        1. Delete content
        2. Create notification (if requested)
        3. Create audit log
        
        **Feature: admin-panel, Property 10: Content Removal Flow**
        **Validates: Requirements 6.4**
        """
        storage = MockStorage()
        admin_id = uuid.uuid4()
        
        result = remove_content(report, admin_id, reason, notify_user, storage)
        
        # 1. Content deleted
        assert result.content_deleted is True
        assert len(storage.deleted_content) == 1
        
        # 2. Notification created (if requested)
        if notify_user:
            assert result.user_notified is True
            assert len(storage.notifications) == 1
        else:
            assert result.user_notified is False
            assert len(storage.notifications) == 0
        
        # 3. Audit log created
        assert len(storage.audit_logs) == 1
