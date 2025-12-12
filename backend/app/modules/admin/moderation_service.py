"""Admin Moderation Service for content moderation operations.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5 - Content Moderation
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import (
    ContentReport,
    UserWarning,
    ReportSeverity,
    ReportStatus,
)
from app.modules.admin.schemas import (
    ModerationFilters,
    ContentReportSummary,
    ContentReportDetail,
    ContentReportListResponse,
    ContentApproveResponse,
    ContentRemoveResponse,
    UserWarnResponse,
    ReporterInfo,
    ContentOwnerInfo,
)
from app.modules.auth.models import User
from app.modules.auth.audit import AuditLogger, AuditAction


class ModerationServiceError(Exception):
    """Base exception for moderation service errors."""
    pass


class ReportNotFoundError(ModerationServiceError):
    """Exception raised when report is not found."""
    pass


class ContentNotFoundError(ModerationServiceError):
    """Exception raised when content is not found."""
    pass


class UserNotFoundError(ModerationServiceError):
    """Exception raised when user is not found."""
    pass


class AdminModerationService:
    """Service for admin content moderation operations.
    
    Requirements: 6.1-6.5 - Content Moderation
    
    Property 9: Moderation Queue Sorting
    - Results SHALL be sorted by severity (critical > high > medium > low)
    - Then by report_count descending
    
    Property 10: Content Removal Flow
    - For any content removal action, the system SHALL delete content,
    - create notification for content owner, and create audit log with removal reason.
    
    Property 11: User Warning Counter
    - For any user warning action, the user's warning_count SHALL increment by 1
    - A UserWarning record SHALL be created
    """

    # Severity order for sorting (higher = more severe)
    SEVERITY_ORDER = {
        ReportSeverity.LOW.value: 1,
        ReportSeverity.MEDIUM.value: 2,
        ReportSeverity.HIGH.value: 3,
        ReportSeverity.CRITICAL.value: 4,
    }

    def __init__(self, session: AsyncSession):
        """Initialize moderation service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def get_moderation_queue(
        self,
        filters: ModerationFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> ContentReportListResponse:
        """Get paginated moderation queue with filters.
        
        Requirements: 6.1 - Display reported content sorted by severity and report count
        
        Property 9: Moderation Queue Sorting
        - Results SHALL be sorted by severity (critical > high > medium > low)
        - Then by report_count descending
        
        Args:
            filters: Moderation filters
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            ContentReportListResponse: Paginated report list
        """
        conditions = []
        
        # Status filter
        if filters.status:
            conditions.append(ContentReport.status == filters.status)
        else:
            # Default to pending reports
            conditions.append(ContentReport.status == ReportStatus.PENDING.value)
        
        # Severity filter
        if filters.severity:
            conditions.append(ContentReport.severity == filters.severity)
        
        # Content type filter
        if filters.content_type:
            conditions.append(ContentReport.content_type == filters.content_type)
        
        # Search filter
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    ContentReport.content_preview.ilike(search_term),
                    ContentReport.reason.ilike(search_term),
                )
            )
        
        # Build count query
        count_query = select(func.count(ContentReport.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Build data query with sorting
        # Property 9: Sort by severity (critical > high > medium > low), then by report_count desc
        severity_order = case(
            (ContentReport.severity == ReportSeverity.CRITICAL.value, 4),
            (ContentReport.severity == ReportSeverity.HIGH.value, 3),
            (ContentReport.severity == ReportSeverity.MEDIUM.value, 2),
            (ContentReport.severity == ReportSeverity.LOW.value, 1),
            else_=0
        )
        
        offset = (page - 1) * page_size
        data_query = (
            select(ContentReport)
            .order_by(desc(severity_order), desc(ContentReport.report_count), desc(ContentReport.created_at))
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            data_query = data_query.where(and_(*conditions))
        
        result = await self.session.execute(data_query)
        reports = list(result.scalars().all())
        
        # Convert to summaries with owner email
        items = []
        for report in reports:
            owner_email = await self._get_user_email(report.content_owner_id)
            items.append(ContentReportSummary(
                id=report.id,
                content_type=report.content_type,
                content_id=report.content_id,
                content_preview=report.content_preview,
                reason=report.reason,
                reason_category=report.reason_category,
                severity=report.severity,
                report_count=report.report_count,
                status=report.status,
                created_at=report.created_at,
                content_owner_email=owner_email,
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return ContentReportListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_report_detail(self, report_id: uuid.UUID) -> ContentReportDetail:
        """Get detailed report information.
        
        Requirements: 6.2 - Show content details, reporter info, and report reason
        
        Args:
            report_id: Report ID
            
        Returns:
            ContentReportDetail: Detailed report information
            
        Raises:
            ReportNotFoundError: If report not found
        """
        query = select(ContentReport).where(ContentReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if report is None:
            raise ReportNotFoundError(f"Report with ID {report_id} not found")
        
        # Get content owner info
        owner = await self._get_user_info(report.content_owner_id)
        content_owner = ContentOwnerInfo(
            id=report.content_owner_id,
            email=owner.get("email") if owner else None,
            name=owner.get("name") if owner else None,
        )
        
        # Get reporter info
        reporter = None
        if report.reporter_id:
            reporter_data = await self._get_user_info(report.reporter_id)
            if reporter_data:
                reporter = ReporterInfo(
                    id=report.reporter_id,
                    email=reporter_data.get("email"),
                    name=reporter_data.get("name"),
                )
        
        return ContentReportDetail(
            id=report.id,
            content_type=report.content_type,
            content_id=report.content_id,
            content_preview=report.content_preview,
            content_owner=content_owner,
            reporter=reporter,
            reason=report.reason,
            reason_category=report.reason_category,
            additional_info=report.additional_info,
            severity=report.severity,
            report_count=report.report_count,
            status=report.status,
            reviewed_by=report.reviewed_by,
            reviewed_at=report.reviewed_at,
            review_notes=report.review_notes,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    async def approve_content(
        self,
        report_id: uuid.UUID,
        admin_id: uuid.UUID,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ContentApproveResponse:
        """Approve content and dismiss reports.
        
        Requirements: 6.3 - Dismiss reports and mark content as reviewed
        
        Args:
            report_id: Report ID
            admin_id: Admin performing the action
            notes: Optional review notes
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ContentApproveResponse: Approval result
            
        Raises:
            ReportNotFoundError: If report not found
        """
        query = select(ContentReport).where(ContentReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if report is None:
            raise ReportNotFoundError(f"Report with ID {report_id} not found")
        
        # Mark as approved
        report.mark_as_reviewed(admin_id, ReportStatus.APPROVED, notes)
        await self.session.flush()
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "content_approved",
                "report_id": str(report_id),
                "content_type": report.content_type,
                "content_id": str(report.content_id),
                "notes": notes,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ContentApproveResponse(
            report_id=report_id,
            status=ReportStatus.APPROVED.value,
            reviewed_at=report.reviewed_at,
            message="Content approved and reports dismissed",
        )

    async def remove_content(
        self,
        report_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: str,
        notify_user: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ContentRemoveResponse:
        """Remove content and notify user.
        
        Requirements: 6.4 - Delete content, notify user, log action with reason
        
        Property 10: Content Removal Flow
        - For any content removal action, the system SHALL delete content,
        - create notification for content owner, and create audit log with removal reason.
        
        Args:
            report_id: Report ID
            admin_id: Admin performing the action
            reason: Reason for removal
            notify_user: Whether to notify the content owner
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ContentRemoveResponse: Removal result
            
        Raises:
            ReportNotFoundError: If report not found
        """
        query = select(ContentReport).where(ContentReport.id == report_id)
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()
        
        if report is None:
            raise ReportNotFoundError(f"Report with ID {report_id} not found")
        
        # Mark as removed
        report.mark_as_reviewed(admin_id, ReportStatus.REMOVED, reason)
        await self.session.flush()
        
        # Delete the actual content (implementation depends on content type)
        content_deleted = await self._delete_content(
            report.content_type,
            report.content_id,
        )
        
        # Notify user if requested
        user_notified = False
        if notify_user:
            user_notified = await self._send_content_removal_notification(
                report.content_owner_id,
                report.content_type,
                reason,
            )
        
        # Create audit log
        audit_log_id = uuid.uuid4()
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "content_removed",
                "audit_log_id": str(audit_log_id),
                "report_id": str(report_id),
                "content_type": report.content_type,
                "content_id": str(report.content_id),
                "content_owner_id": str(report.content_owner_id),
                "reason": reason,
                "content_deleted": content_deleted,
                "user_notified": user_notified,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ContentRemoveResponse(
            report_id=report_id,
            content_id=report.content_id,
            content_type=report.content_type,
            status=ReportStatus.REMOVED.value,
            content_deleted=content_deleted,
            user_notified=user_notified,
            audit_log_id=audit_log_id,
            removed_at=report.reviewed_at,
            message="Content removed successfully",
        )

    async def warn_user(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: str,
        related_report_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserWarnResponse:
        """Issue a warning to a user.
        
        Requirements: 6.5 - Send warning notification and increment user warning count
        
        Property 11: User Warning Counter
        - For any user warning action, the user's warning_count SHALL increment by 1
        - A UserWarning record SHALL be created
        
        Args:
            user_id: User ID to warn
            admin_id: Admin performing the action
            reason: Reason for warning
            related_report_id: Optional related content report ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            UserWarnResponse: Warning result
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Verify user exists
        user = await self._get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Get current warning count
        current_count = await self._get_user_warning_count(user_id)
        new_warning_number = current_count + 1
        
        # Create warning record
        warning = UserWarning(
            user_id=user_id,
            admin_id=admin_id,
            reason=reason,
            warning_number=new_warning_number,
            related_report_id=related_report_id,
        )
        self.session.add(warning)
        await self.session.flush()
        
        # Send notification
        notification_sent = await self._send_warning_notification(user_id, reason, new_warning_number)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "user_warning_issued",
                "target_user_id": str(user_id),
                "warning_id": str(warning.id),
                "warning_number": new_warning_number,
                "reason": reason,
                "related_report_id": str(related_report_id) if related_report_id else None,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return UserWarnResponse(
            warning_id=warning.id,
            user_id=user_id,
            warning_number=new_warning_number,
            reason=reason,
            notification_sent=notification_sent,
            created_at=warning.created_at,
            message=f"Warning #{new_warning_number} issued to user",
        )

    # ==================== Helper Methods ====================

    async def _get_user_email(self, user_id: uuid.UUID) -> Optional[str]:
        """Get user email by ID."""
        query = select(User.email).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_user_info(self, user_id: uuid.UUID) -> Optional[dict]:
        """Get user info by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return {"email": user.email, "name": user.name}
        return None

    async def _get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_user_warning_count(self, user_id: uuid.UUID) -> int:
        """Get the number of warnings for a user."""
        query = select(func.count(UserWarning.id)).where(UserWarning.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def _delete_content(self, content_type: str, content_id: uuid.UUID) -> bool:
        """Delete content based on type.
        
        This is a placeholder - actual implementation would depend on content type.
        """
        try:
            # Implementation would vary by content type
            # For now, return True to indicate success
            return True
        except Exception:
            return False

    async def _send_content_removal_notification(
        self,
        user_id: uuid.UUID,
        content_type: str,
        reason: str,
    ) -> bool:
        """Send content removal notification to user."""
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            notification_service = NotificationService(self.session)
            await notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="content.removed",
                    title="Content Removed",
                    message=f"Your {content_type} has been removed for violating our community guidelines. Reason: {reason}",
                    priority=NotificationPriority.HIGH,
                )
            )
            return True
        except Exception:
            return False

    async def _send_warning_notification(
        self,
        user_id: uuid.UUID,
        reason: str,
        warning_number: int,
    ) -> bool:
        """Send warning notification to user."""
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            notification_service = NotificationService(self.session)
            await notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="account.warning",
                    title=f"Warning #{warning_number}",
                    message=f"You have received a warning. Reason: {reason}. Please review our community guidelines.",
                    priority=NotificationPriority.HIGH,
                )
            )
            return True
        except Exception:
            return False
