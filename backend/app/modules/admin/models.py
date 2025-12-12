"""Admin models for database entities.

Requirements: 1.1, 1.4 - Admin Authentication & Authorization
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5 - Content Moderation
Requirements: 14.1 - Promotional Tools (Discount Codes)
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DiscountType(str, Enum):
    """Discount code types.
    
    Requirements: 14.1 - Percentage or fixed discount
    """
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class AdminRole(str, Enum):
    """Admin role types."""
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AdminPermission(str, Enum):
    """Admin permission types."""
    # User management
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    IMPERSONATE_USERS = "impersonate_users"
    
    # Billing management
    VIEW_BILLING = "view_billing"
    MANAGE_BILLING = "manage_billing"
    PROCESS_REFUNDS = "process_refunds"
    
    # System management
    VIEW_SYSTEM = "view_system"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_CONFIG = "manage_config"
    
    # Moderation
    VIEW_MODERATION = "view_moderation"
    MANAGE_MODERATION = "manage_moderation"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    
    # Compliance
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_COMPLIANCE = "manage_compliance"
    
    # Admin management (super_admin only)
    MANAGE_ADMINS = "manage_admins"


# Default permissions per role
DEFAULT_PERMISSIONS = {
    AdminRole.ADMIN: [
        AdminPermission.VIEW_USERS,
        AdminPermission.MANAGE_USERS,
        AdminPermission.VIEW_BILLING,
        AdminPermission.VIEW_SYSTEM,
        AdminPermission.VIEW_MODERATION,
        AdminPermission.MANAGE_MODERATION,
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_AUDIT_LOGS,
    ],
    AdminRole.SUPER_ADMIN: [p for p in AdminPermission],  # All permissions
}


class Admin(Base):
    """Admin model for administrative users.
    
    Requirements: 1.1, 1.4 - Admin role verification and management
    """

    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AdminRole.ADMIN.value
    )
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    def has_permission(self, permission: AdminPermission) -> bool:
        """Check if admin has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if admin has the permission
        """
        return permission.value in self.permissions
    
    def has_any_permission(self, permissions: list[AdminPermission]) -> bool:
        """Check if admin has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if admin has any of the permissions
        """
        return any(p.value in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: list[AdminPermission]) -> bool:
        """Check if admin has all of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if admin has all of the permissions
        """
        return all(p.value in self.permissions for p in permissions)
    
    @property
    def is_super_admin(self) -> bool:
        """Check if admin is a super admin."""
        return self.role == AdminRole.SUPER_ADMIN.value


class DiscountCode(Base):
    """Discount code model for promotional campaigns.
    
    Requirements: 14.1 - Create discount codes with percentage or fixed discount,
    validity period, and usage limit.
    
    Property 15: Discount Code Validation
    - Code is valid only if current_date is between valid_from and valid_until
    - Code is valid only if usage_count < usage_limit (when usage_limit is set)
    """

    __tablename__ = "discount_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DiscountType.PERCENTAGE.value
    )
    discount_value: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    applicable_plans: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def is_valid(self, current_date: Optional[datetime] = None) -> bool:
        """Check if discount code is currently valid.
        
        Property 15: Discount Code Validation
        - Code is valid only if current_date is between valid_from and valid_until
        - Code is valid only if usage_count < usage_limit (when usage_limit is set)
        
        Args:
            current_date: Date to check validity against (defaults to now)
            
        Returns:
            bool: True if code is valid
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Check if code is active
        if not self.is_active:
            return False
        
        # Check date validity
        if current_date < self.valid_from or current_date > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        
        return True

    def calculate_discount(self, original_price: float) -> float:
        """Calculate the discounted price.
        
        Args:
            original_price: Original price before discount
            
        Returns:
            float: Discount amount
        """
        if self.discount_type == DiscountType.PERCENTAGE.value:
            return original_price * (self.discount_value / 100)
        else:  # FIXED
            return min(self.discount_value, original_price)


# ==================== Content Moderation Models (Requirements 6.1-6.5) ====================


class ContentType(str, Enum):
    """Types of content that can be reported.
    
    Requirements: 6.1 - Content moderation queue
    """
    VIDEO = "video"
    COMMENT = "comment"
    STREAM = "stream"
    THUMBNAIL = "thumbnail"
    CHANNEL = "channel"


class ReportSeverity(str, Enum):
    """Severity levels for content reports.
    
    Requirements: 6.1 - Sorted by severity
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus(str, Enum):
    """Status of content reports.
    
    Requirements: 6.3, 6.4 - Approve or remove content
    """
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REMOVED = "removed"


class ContentReport(Base):
    """Content Report model for moderation queue.
    
    Requirements: 6.1 - Display reported content sorted by severity and report count
    Requirements: 6.2 - Show content details, reporter info, and report reason
    Requirements: 6.3 - Approve content (dismiss reports, mark as reviewed)
    Requirements: 6.4 - Remove content (delete content, notify user, log action)
    
    Property 9: Moderation Queue Sorting
    - Results SHALL be sorted by severity (critical > high > medium > low) 
    - Then by report_count descending
    
    Property 10: Content Removal Flow
    - For any content removal action, the system SHALL delete content, 
    - create notification for content owner, and create audit log with removal reason.
    """

    __tablename__ = "content_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Content identification
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    content_preview: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    content_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Reporter information
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Report details
    reason: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    reason_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    additional_info: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    
    # Severity and aggregation
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReportSeverity.MEDIUM.value, index=True
    )
    report_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReportStatus.PENDING.value, index=True
    )
    
    # Review information
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def severity_order(self) -> int:
        """Get numeric severity order for sorting.
        
        Property 9: Moderation Queue Sorting
        - critical > high > medium > low
        
        Returns:
            int: Severity order (higher = more severe)
        """
        severity_map = {
            ReportSeverity.LOW.value: 1,
            ReportSeverity.MEDIUM.value: 2,
            ReportSeverity.HIGH.value: 3,
            ReportSeverity.CRITICAL.value: 4,
        }
        return severity_map.get(self.severity, 0)

    def mark_as_reviewed(
        self,
        admin_id: uuid.UUID,
        status: ReportStatus,
        notes: Optional[str] = None,
    ) -> None:
        """Mark report as reviewed.
        
        Args:
            admin_id: Admin who reviewed the report
            status: New status (approved or removed)
            notes: Optional review notes
        """
        self.reviewed_by = admin_id
        self.reviewed_at = datetime.utcnow()
        self.status = status.value
        if notes:
            self.review_notes = notes

    def __repr__(self) -> str:
        return f"<ContentReport(id={self.id}, type={self.content_type}, severity={self.severity})>"


class UserWarning(Base):
    """User Warning model for tracking warnings issued to users.
    
    Requirements: 6.5 - Send warning notification and increment user warning count
    
    Property 11: User Warning Counter
    - For any user warning action, the user's warning_count SHALL increment by 1
    - A UserWarning record SHALL be created
    """

    __tablename__ = "user_warnings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Warning details
    reason: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    warning_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    # Related report (if warning is from moderation)
    related_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserWarning(id={self.id}, user_id={self.user_id}, warning_number={self.warning_number})>"


# ==================== System Configuration Models (Requirements 19-29) ====================


class ConfigCategory(str, Enum):
    """Categories for system configuration.
    
    Requirements: 19-29 - Global Configuration Management
    """
    AUTH = "auth"
    UPLOAD = "upload"
    STREAMING = "streaming"
    AI = "ai"
    MODERATION = "moderation"
    NOTIFICATION = "notification"
    JOBS = "jobs"
    QUOTA = "quota"
    PLANS = "plans"
    EMAIL_TEMPLATES = "email_templates"
    FEATURE_FLAGS = "feature_flags"
    BRANDING = "branding"


# ==================== Dashboard Export Models (Requirements 2.5) ====================


class ExportStatus(str, Enum):
    """Status of dashboard export jobs.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported export formats.
    
    Requirements: 2.5 - CSV or PDF export
    """
    CSV = "csv"
    PDF = "pdf"


class DashboardExport(Base):
    """Dashboard Export model for tracking export jobs.
    
    Requirements: 2.5 - Generate CSV or PDF report with selected metrics
    """

    __tablename__ = "dashboard_exports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Export configuration
    format: Mapped[str] = mapped_column(
        String(10), nullable=False, default=ExportFormat.CSV.value
    )
    metrics: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), nullable=False
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    include_charts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExportStatus.PENDING.value, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    download_url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<DashboardExport(id={self.id}, format={self.format}, status={self.status})>"


class SystemConfig(Base):
    """System Configuration model for global platform settings.
    
    Requirements: 19-29 - Global Configuration Management
    - Stores all configurable parameters grouped by category
    - Logs modifications with previous value
    - Supports various config types: auth, upload, streaming, AI, moderation, etc.
    """

    __tablename__ = "system_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    value: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key}, category={self.category})>"


# ==================== Support & Communication Models (Requirements 10.1-10.5) ====================


class TicketStatus(str, Enum):
    """Status of support tickets.
    
    Requirements: 10.1 - Support ticket status tracking
    """
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Priority levels for support tickets.
    
    Requirements: 10.1 - Support ticket priority
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(Base):
    """Support Ticket model for user support requests.
    
    Requirements: 10.1 - Display all tickets with status, priority, user, and last update
    Requirements: 10.2 - Respond to ticket via email and update ticket status
    """

    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Ticket details
    subject: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    
    # Status and priority
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TicketStatus.OPEN.value, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TicketPriority.MEDIUM.value, index=True
    )
    
    # Assignment
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Relationships
    messages: Mapped[list["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, subject={self.subject}, status={self.status})>"


class TicketMessage(Base):
    """Ticket Message model for conversation thread.
    
    Requirements: 10.2 - Respond to ticket and track conversation
    """

    __tablename__ = "ticket_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Sender information
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    sender_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'user' or 'admin'
    )
    
    # Message content
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    
    # Attachments (stored as JSON array of file URLs)
    attachments: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationship
    ticket: Mapped["SupportTicket"] = relationship(
        "SupportTicket", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<TicketMessage(id={self.id}, ticket_id={self.ticket_id}, sender_type={self.sender_type})>"


class BroadcastStatus(str, Enum):
    """Status of broadcast messages.
    
    Requirements: 10.3 - Broadcast message status
    """
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class BroadcastMessage(Base):
    """Broadcast Message model for mass communication.
    
    Requirements: 10.3 - Send broadcast targeting by plan, status, or all users with scheduling
    """

    __tablename__ = "broadcast_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Message content
    subject: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    content_html: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Targeting
    target_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="all"  # 'all', 'plan', 'status'
    )
    target_plans: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    target_statuses: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    
    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BroadcastStatus.DRAFT.value, index=True
    )
    sent_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    failed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    
    # Admin who created
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<BroadcastMessage(id={self.id}, subject={self.subject}, status={self.status})>"


class Announcement(Base):
    """Announcement model for dashboard banners.
    
    Requirements: 10.5 - Display banner in user dashboard with dismiss option
    """

    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Announcement content
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    
    # Display settings
    announcement_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info"  # 'info', 'warning', 'success', 'error'
    )
    is_dismissible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    
    # Targeting (optional)
    target_plans: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )
    
    # Scheduling
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    
    # Admin who created
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def is_visible(self, current_date: Optional[datetime] = None) -> bool:
        """Check if announcement is currently visible.
        
        Args:
            current_date: Date to check visibility against (defaults to now)
            
        Returns:
            bool: True if announcement is visible
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if current_date < self.start_date:
            return False
        
        if self.end_date and current_date > self.end_date:
            return False
        
        return True

    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title={self.title}, is_active={self.is_active})>"


class UserCommunication(Base):
    """User Communication model for tracking all user interactions.
    
    Requirements: 10.4 - View all emails, notifications, and support interactions
    """

    __tablename__ = "user_communications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Communication type
    communication_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True  # 'email', 'notification', 'support', 'broadcast'
    )
    
    # Reference to related entity
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True  # 'ticket', 'broadcast', 'notification'
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    
    # Communication details
    subject: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    content_preview: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    
    # Direction
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False, default="outbound"  # 'inbound', 'outbound'
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"  # 'sent', 'delivered', 'read', 'failed'
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserCommunication(id={self.id}, user_id={self.user_id}, type={self.communication_type})>"


# ==================== Trial Code Models (Requirements 14.4) ====================


class TrialCode(Base):
    """Trial code model for extended trial promotions.
    
    Requirements: 14.4 - Create extended trial codes
    """

    __tablename__ = "trial_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    trial_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    applicable_plans: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=list
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def is_valid(self, current_date: Optional[datetime] = None) -> bool:
        """Check if trial code is currently valid.
        
        Args:
            current_date: Date to check validity against (defaults to now)
            
        Returns:
            bool: True if code is valid
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Check if code is active
        if not self.is_active:
            return False
        
        # Check date validity
        if current_date < self.valid_from or current_date > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        
        return True

    def __repr__(self) -> str:
        return f"<TrialCode(id={self.id}, code={self.code}, days={self.trial_days})>"
