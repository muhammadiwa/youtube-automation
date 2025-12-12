"""Admin User Service for user management operations.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6 - User Management
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.schemas import (
    UserFilters,
    UserSummary,
    UserDetail,
    UserListResponse,
    UserSuspendRequest,
    UserSuspendResponse,
    UserActivateResponse,
    ImpersonationSession,
    ImpersonateResponse,
    PasswordResetResponse,
    SubscriptionInfo,
    YouTubeAccountSummary,
    UsageStats,
    ActivityLog,
)
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.audit import AuditLogger, AuditAction
from app.modules.job.models import Job, JobStatus


class AdminUserServiceError(Exception):
    """Base exception for admin user service errors."""
    pass


class UserNotFoundError(AdminUserServiceError):
    """Exception raised when user is not found."""
    pass


class UserAlreadySuspendedError(AdminUserServiceError):
    """Exception raised when user is already suspended."""
    pass


class UserNotSuspendedError(AdminUserServiceError):
    """Exception raised when trying to activate a non-suspended user."""
    pass


class AdminUserService:
    """Service for admin user management operations.
    
    Requirements: 3.1-3.6 - User Management
    """

    def __init__(self, session: AsyncSession):
        """Initialize admin user service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_users(
        self,
        filters: UserFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> UserListResponse:
        """Get paginated list of users with filters.
        
        Requirements: 3.1 - Display paginated list with search, filter by status, plan, registration date
        
        Args:
            filters: User filters
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            UserListResponse: Paginated user list
        """
        conditions = []
        
        # Status filter
        if filters.status:
            if filters.status == "suspended":
                conditions.append(User.is_active == False)
            elif filters.status == "active":
                conditions.append(User.is_active == True)
        
        # Search filter (email or name)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    User.email.ilike(search_term),
                    User.name.ilike(search_term),
                )
            )
        
        # Registration date filters
        if filters.registered_after:
            conditions.append(User.created_at >= filters.registered_after)
        if filters.registered_before:
            conditions.append(User.created_at <= filters.registered_before)
        
        # Build count query
        count_query = select(func.count(User.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Build data query
        offset = (page - 1) * page_size
        data_query = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            data_query = data_query.where(and_(*conditions))
        
        result = await self.session.execute(data_query)
        users = list(result.scalars().all())
        
        # Convert to summaries
        items = []
        for user in users:
            # Get warning count
            warning_count = await self._get_user_warning_count(user.id)
            
            # Get subscription plan name (simplified - would need join in production)
            plan_name = await self._get_user_plan_name(user.id)
            
            status = "suspended" if not user.is_active else "active"
            
            items.append(UserSummary(
                id=user.id,
                email=user.email,
                name=user.name,
                status=status,
                is_active=user.is_active,
                plan_name=plan_name,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                warning_count=warning_count,
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user_detail(self, user_id: uuid.UUID) -> UserDetail:
        """Get detailed user information.
        
        Requirements: 3.2 - Show profile info, subscription, connected accounts, usage stats, activity history
        
        Args:
            user_id: User ID
            
        Returns:
            UserDetail: Detailed user information
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Get subscription info
        subscription = await self._get_user_subscription(user_id)
        
        # Get connected YouTube accounts
        connected_accounts = await self._get_connected_accounts(user_id)
        
        # Get usage stats
        usage_stats = await self._get_usage_stats(user_id)
        
        # Get activity history (last 50 entries)
        activity_history = await self._get_activity_history(user_id, limit=50)
        
        # Get warning count
        warning_count = await self._get_user_warning_count(user_id)
        
        status = "suspended" if not user.is_active else "active"
        
        return UserDetail(
            id=user.id,
            email=user.email,
            name=user.name,
            status=status,
            is_active=user.is_active,
            is_2fa_enabled=user.is_2fa_enabled,
            subscription=subscription,
            connected_accounts=connected_accounts,
            usage_stats=usage_stats,
            activity_history=activity_history,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            warning_count=warning_count,
        )

    async def suspend_user(
        self,
        user_id: uuid.UUID,
        reason: str,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSuspendResponse:
        """Suspend a user account.
        
        Requirements: 3.3 - Disable user access, pause all scheduled jobs, send notification email
        
        Args:
            user_id: User ID to suspend
            reason: Reason for suspension
            admin_id: Admin performing the action
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            UserSuspendResponse: Suspension result
            
        Raises:
            UserNotFoundError: If user not found
            UserAlreadySuspendedError: If user is already suspended
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        if not user.is_active:
            raise UserAlreadySuspendedError(f"User {user_id} is already suspended")
        
        # Suspend user
        user.is_active = False
        await self.session.flush()
        
        # Pause all scheduled jobs for this user
        jobs_paused = await self._pause_user_jobs(user_id)
        
        # Send notification email
        notification_sent = await self._send_suspension_notification(user, reason)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "user_suspended",
                "target_user_id": str(user_id),
                "reason": reason,
                "jobs_paused": jobs_paused,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return UserSuspendResponse(
            user_id=user_id,
            status="suspended",
            suspended_at=datetime.utcnow(),
            reason=reason,
            jobs_paused=jobs_paused,
            notification_sent=notification_sent,
        )

    async def activate_user(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserActivateResponse:
        """Activate a suspended user account.
        
        Requirements: 3.4 - Restore access and resume paused jobs
        
        Args:
            user_id: User ID to activate
            admin_id: Admin performing the action
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            UserActivateResponse: Activation result
            
        Raises:
            UserNotFoundError: If user not found
            UserNotSuspendedError: If user is not suspended
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        if user.is_active:
            raise UserNotSuspendedError(f"User {user_id} is not suspended")
        
        # Activate user
        user.is_active = True
        await self.session.flush()
        
        # Resume paused jobs
        jobs_resumed = await self._resume_user_jobs(user_id)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "user_activated",
                "target_user_id": str(user_id),
                "jobs_resumed": jobs_resumed,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return UserActivateResponse(
            user_id=user_id,
            status="active",
            activated_at=datetime.utcnow(),
            jobs_resumed=jobs_resumed,
        )

    async def impersonate_user(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ImpersonateResponse:
        """Create an impersonation session for a user.
        
        Requirements: 3.5 - Create temporary session for support purposes with full audit logging
        
        Args:
            user_id: User ID to impersonate
            admin_id: Admin performing the action
            reason: Reason for impersonation
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ImpersonateResponse: Impersonation session info
            
        Raises:
            UserNotFoundError: If user not found
        """
        from app.modules.auth.jwt import create_access_token
        
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Create impersonation session
        session_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour session
        
        # Create access token for impersonation
        access_token = create_access_token(
            user_id=str(user_id),
            additional_claims={
                "impersonation": True,
                "impersonated_by": str(admin_id),
                "session_id": str(session_id),
            }
        )
        
        # Create audit log entry
        audit_log_id = uuid.uuid4()
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "user_impersonation_started",
                "target_user_id": str(user_id),
                "session_id": str(session_id),
                "reason": reason,
                "expires_at": expires_at.isoformat(),
                "audit_log_id": str(audit_log_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        session = ImpersonationSession(
            session_id=session_id,
            admin_id=admin_id,
            user_id=user_id,
            access_token=access_token,
            expires_at=expires_at,
            audit_log_id=audit_log_id,
        )
        
        return ImpersonateResponse(
            session=session,
            message=f"Impersonation session created for user {user.email}",
        )

    async def reset_user_password(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PasswordResetResponse:
        """Initiate password reset for a user.
        
        Requirements: 3.6 - Send secure reset link to user email
        
        Args:
            user_id: User ID
            admin_id: Admin performing the action
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            PasswordResetResponse: Reset result
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Send password reset email
        reset_link_sent = await self._send_password_reset_email(user, reset_token)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin_id,
            details={
                "event": "admin_password_reset",
                "target_user_id": str(user_id),
                "target_email": user.email,
                "reset_link_sent": reset_link_sent,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return PasswordResetResponse(
            user_id=user_id,
            email=user.email,
            reset_link_sent=reset_link_sent,
            expires_at=expires_at,
        )

    # ==================== Helper Methods ====================

    async def _get_user_warning_count(self, user_id: uuid.UUID) -> int:
        """Get the number of warnings for a user."""
        # This would query a user_warnings table in production
        # For now, return 0 as placeholder
        return 0

    async def _get_user_plan_name(self, user_id: uuid.UUID) -> Optional[str]:
        """Get the user's subscription plan name."""
        # This would join with subscriptions table in production
        # For now, return None as placeholder
        try:
            from app.modules.billing.models import Subscription
            query = select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"])
            )
            result = await self.session.execute(query)
            subscription = result.scalar_one_or_none()
            if subscription:
                return subscription.plan_name
        except Exception:
            pass
        return None

    async def _get_user_subscription(self, user_id: uuid.UUID) -> Optional[SubscriptionInfo]:
        """Get user's subscription information."""
        try:
            from app.modules.billing.models import Subscription
            query = select(Subscription).where(Subscription.user_id == user_id)
            result = await self.session.execute(query)
            subscription = result.scalar_one_or_none()
            if subscription:
                return SubscriptionInfo(
                    id=subscription.id,
                    plan_name=subscription.plan_name,
                    status=subscription.status,
                    start_date=subscription.start_date,
                    end_date=subscription.end_date,
                    next_billing_date=getattr(subscription, 'next_billing_date', None),
                )
        except Exception:
            pass
        return None

    async def _get_connected_accounts(self, user_id: uuid.UUID) -> list[YouTubeAccountSummary]:
        """Get user's connected YouTube accounts."""
        try:
            from app.modules.account.models import YouTubeAccount
            query = select(YouTubeAccount).where(YouTubeAccount.user_id == user_id)
            result = await self.session.execute(query)
            accounts = list(result.scalars().all())
            return [
                YouTubeAccountSummary(
                    id=acc.id,
                    channel_id=acc.channel_id,
                    channel_name=acc.channel_name or "Unknown",
                    subscriber_count=getattr(acc, 'subscriber_count', None),
                    is_active=acc.is_active,
                )
                for acc in accounts
            ]
        except Exception:
            pass
        return []

    async def _get_usage_stats(self, user_id: uuid.UUID) -> UsageStats:
        """Get user's usage statistics."""
        # This would aggregate from various tables in production
        return UsageStats(
            total_videos=0,
            total_streams=0,
            storage_used_gb=0.0,
            bandwidth_used_gb=0.0,
            ai_generations_used=0,
        )

    async def _get_activity_history(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> list[ActivityLog]:
        """Get user's activity history from audit logs."""
        # This would query audit_logs table in production
        return []

    async def _pause_user_jobs(self, user_id: uuid.UUID) -> int:
        """Pause all queued jobs for a user.
        
        Returns the number of jobs paused.
        """
        # Update queued jobs to a paused state
        query = select(Job).where(
            Job.user_id == user_id,
            Job.status == JobStatus.QUEUED.value,
        )
        result = await self.session.execute(query)
        jobs = list(result.scalars().all())
        
        paused_count = 0
        for job in jobs:
            # Mark job as failed with suspension reason
            job.status = JobStatus.FAILED.value
            job.error = "User account suspended"
            paused_count += 1
        
        await self.session.flush()
        return paused_count

    async def _resume_user_jobs(self, user_id: uuid.UUID) -> int:
        """Resume paused jobs for a user.
        
        Returns the number of jobs resumed.
        """
        # Find jobs that were paused due to suspension
        query = select(Job).where(
            Job.user_id == user_id,
            Job.status == JobStatus.FAILED.value,
            Job.error == "User account suspended",
        )
        result = await self.session.execute(query)
        jobs = list(result.scalars().all())
        
        resumed_count = 0
        for job in jobs:
            # Re-queue the job
            job.status = JobStatus.QUEUED.value
            job.error = None
            job.attempts = 0
            resumed_count += 1
        
        await self.session.flush()
        return resumed_count

    async def _send_suspension_notification(self, user: User, reason: str) -> bool:
        """Send suspension notification email to user."""
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            notification_service = NotificationService(self.session)
            await notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user.id,
                    event_type="account.suspended",
                    title="Account Suspended",
                    message=f"Your account has been suspended. Reason: {reason}. Please contact support for more information.",
                    priority=NotificationPriority.HIGH,
                )
            )
            return True
        except Exception:
            return False

    async def _send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email to user."""
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            notification_service = NotificationService(self.session)
            await notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user.id,
                    event_type="account.password_reset",
                    title="Password Reset Request",
                    message="An administrator has initiated a password reset for your account. Please check your email for the reset link.",
                    priority=NotificationPriority.HIGH,
                    payload={"reset_token": reset_token},
                )
            )
            return True
        except Exception:
            return False
