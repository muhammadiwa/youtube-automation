"""Feature Gate Service for enforcing plan limits.

Provides centralized limit checking for all features based on user's subscription plan.
All limits are fetched from database Plan model - NO hardcoded limits.

Requirements: 28.1 - Feature access based on tier
"""

import uuid
from typing import Optional, Tuple
from datetime import datetime

from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import Plan, Subscription, SubscriptionStatus
from app.modules.billing.repository import PlanRepository, SubscriptionRepository


class LimitExceededError(Exception):
    """Exception raised when a plan limit is exceeded."""
    
    def __init__(
        self,
        resource: str,
        current: int,
        limit: int,
        plan_name: str,
        message: Optional[str] = None,
    ):
        self.resource = resource
        self.current = current
        self.limit = limit
        self.plan_name = plan_name
        self.message = message or f"{resource} limit exceeded: {current}/{limit} (Plan: {plan_name})"
        super().__init__(self.message)


class FeatureGateService:
    """Service for checking and enforcing plan limits.
    
    All limits are fetched from database Plan model.
    Supports -1 as unlimited value.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.plan_repo = PlanRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
    
    async def get_user_plan(self, user_id: uuid.UUID) -> Tuple[Plan, Subscription]:
        """Get user's current plan and subscription.
        
        Returns:
            Tuple of (Plan, Subscription)
            
        Raises:
            ValueError: If user has no subscription
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        
        if not subscription:
            # Auto-create FREE subscription
            from app.modules.billing.service import BillingService
            billing_service = BillingService(self.session)
            await billing_service.ensure_free_subscription(user_id)
            subscription = await self.subscription_repo.get_by_user_id(user_id)
        
        if not subscription:
            raise ValueError(f"Failed to get/create subscription for user {user_id}")
        
        # Get plan from database
        plan = await self.plan_repo.get_by_slug(subscription.plan_tier)
        
        if not plan:
            # Fallback to free plan if plan not found
            plan = await self.plan_repo.get_by_slug("free")
        
        if not plan:
            raise ValueError(f"Plan '{subscription.plan_tier}' not found in database")
        
        return plan, subscription
    
    def _is_unlimited(self, limit: int) -> bool:
        """Check if limit value means unlimited."""
        return limit == -1
    
    async def check_accounts_limit(
        self,
        user_id: uuid.UUID,
        raise_on_exceed: bool = True,
    ) -> Tuple[bool, int, int, str]:
        """Check if user can add more YouTube accounts.
        
        Args:
            user_id: User UUID
            raise_on_exceed: If True, raise LimitExceededError when exceeded
            
        Returns:
            Tuple of (can_add, current_count, limit, plan_name)
            
        Raises:
            LimitExceededError: If limit exceeded and raise_on_exceed is True
        """
        from app.modules.account.models import YouTubeAccount
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Count current active accounts
        result = await self.session.execute(
            select(sql_func.count(YouTubeAccount.id))
            .where(YouTubeAccount.user_id == user_id)
            .where(YouTubeAccount.status == "active")
        )
        current_count = result.scalar() or 0
        
        limit = plan.max_accounts
        
        # Check if unlimited
        if self._is_unlimited(limit):
            return True, current_count, limit, plan.name
        
        can_add = current_count < limit
        
        if not can_add and raise_on_exceed:
            raise LimitExceededError(
                resource="YouTube Accounts",
                current=current_count,
                limit=limit,
                plan_name=plan.name,
                message=f"Anda sudah mencapai batas maksimal {limit} akun YouTube untuk plan {plan.name}. Upgrade plan untuk menambah lebih banyak akun."
            )
        
        return can_add, current_count, limit, plan.name
    
    async def check_videos_per_month_limit(
        self,
        user_id: uuid.UUID,
        raise_on_exceed: bool = True,
    ) -> Tuple[bool, int, int, str]:
        """Check if user can upload more videos this month.
        
        Args:
            user_id: User UUID
            raise_on_exceed: If True, raise LimitExceededError when exceeded
            
        Returns:
            Tuple of (can_upload, current_count, limit, plan_name)
            
        Raises:
            LimitExceededError: If limit exceeded and raise_on_exceed is True
        """
        from app.modules.video.models import Video
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Count videos uploaded in current billing period
        result = await self.session.execute(
            select(sql_func.count(Video.id))
            .where(Video.user_id == user_id)
            .where(Video.created_at >= subscription.current_period_start)
        )
        current_count = result.scalar() or 0
        
        limit = plan.max_videos_per_month
        
        # Check if unlimited
        if self._is_unlimited(limit):
            return True, current_count, limit, plan.name
        
        can_upload = current_count < limit
        
        if not can_upload and raise_on_exceed:
            raise LimitExceededError(
                resource="Videos per Month",
                current=current_count,
                limit=limit,
                plan_name=plan.name,
                message=f"Anda sudah mencapai batas maksimal {limit} video per bulan untuk plan {plan.name}. Upgrade plan untuk upload lebih banyak video."
            )
        
        return can_upload, current_count, limit, plan.name
    
    async def check_streams_per_month_limit(
        self,
        user_id: uuid.UUID,
        raise_on_exceed: bool = True,
    ) -> Tuple[bool, int, int, str]:
        """Check if user can create more streams this month.
        
        Counts both LiveEvent and StreamJob.
        
        Args:
            user_id: User UUID
            raise_on_exceed: If True, raise LimitExceededError when exceeded
            
        Returns:
            Tuple of (can_create, current_count, limit, plan_name)
            
        Raises:
            LimitExceededError: If limit exceeded and raise_on_exceed is True
        """
        from app.modules.stream.models import LiveEvent
        from app.modules.stream.stream_job_models import StreamJob
        from app.modules.account.models import YouTubeAccount
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Count LiveEvent streams in current billing period
        live_events_result = await self.session.execute(
            select(sql_func.count(LiveEvent.id))
            .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
            .where(YouTubeAccount.user_id == user_id)
            .where(LiveEvent.created_at >= subscription.current_period_start)
        )
        live_events_count = live_events_result.scalar() or 0
        
        # Count StreamJob streams in current billing period
        stream_jobs_result = await self.session.execute(
            select(sql_func.count(StreamJob.id))
            .where(StreamJob.user_id == user_id)
            .where(StreamJob.created_at >= subscription.current_period_start)
        )
        stream_jobs_count = stream_jobs_result.scalar() or 0
        
        current_count = live_events_count + stream_jobs_count
        limit = plan.max_streams_per_month
        
        # Check if unlimited
        if self._is_unlimited(limit):
            return True, current_count, limit, plan.name
        
        can_create = current_count < limit
        
        if not can_create and raise_on_exceed:
            raise LimitExceededError(
                resource="Streams per Month",
                current=current_count,
                limit=limit,
                plan_name=plan.name,
                message=f"Anda sudah mencapai batas maksimal {limit} stream per bulan untuk plan {plan.name}. Upgrade plan untuk membuat lebih banyak stream."
            )
        
        return can_create, current_count, limit, plan.name
    
    async def check_concurrent_streams_limit(
        self,
        user_id: uuid.UUID,
        raise_on_exceed: bool = True,
    ) -> Tuple[bool, int, int, str]:
        """Check if user can start another concurrent stream.
        
        Counts currently running LiveEvent (LIVE status) and StreamJob (RUNNING status).
        
        Args:
            user_id: User UUID
            raise_on_exceed: If True, raise LimitExceededError when exceeded
            
        Returns:
            Tuple of (can_start, current_count, limit, plan_name)
            
        Raises:
            LimitExceededError: If limit exceeded and raise_on_exceed is True
        """
        from app.modules.stream.models import LiveEvent, LiveEventStatus
        from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
        from app.modules.account.models import YouTubeAccount
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Count currently running LiveEvent (LIVE status)
        live_result = await self.session.execute(
            select(sql_func.count(LiveEvent.id))
            .join(YouTubeAccount, LiveEvent.account_id == YouTubeAccount.id)
            .where(YouTubeAccount.user_id == user_id)
            .where(LiveEvent.status == LiveEventStatus.LIVE.value)
        )
        live_count = live_result.scalar() or 0
        
        # Count currently running StreamJob (RUNNING status)
        jobs_result = await self.session.execute(
            select(sql_func.count(StreamJob.id))
            .where(StreamJob.user_id == user_id)
            .where(StreamJob.status == StreamJobStatus.RUNNING.value)
        )
        jobs_count = jobs_result.scalar() or 0
        
        current_count = live_count + jobs_count
        limit = plan.concurrent_streams
        
        # Check if unlimited
        if self._is_unlimited(limit):
            return True, current_count, limit, plan.name
        
        can_start = current_count < limit
        
        if not can_start and raise_on_exceed:
            raise LimitExceededError(
                resource="Concurrent Streams",
                current=current_count,
                limit=limit,
                plan_name=plan.name,
                message=f"Anda sudah mencapai batas maksimal {limit} stream bersamaan untuk plan {plan.name}. Hentikan stream lain atau upgrade plan."
            )
        
        return can_start, current_count, limit, plan.name
    
    async def check_storage_limit(
        self,
        user_id: uuid.UUID,
        additional_bytes: int = 0,
        raise_on_exceed: bool = True,
    ) -> Tuple[bool, float, float, str]:
        """Check if user has storage space available.
        
        Args:
            user_id: User UUID
            additional_bytes: Additional bytes to be added
            raise_on_exceed: If True, raise LimitExceededError when exceeded
            
        Returns:
            Tuple of (has_space, current_gb, limit_gb, plan_name)
            
        Raises:
            LimitExceededError: If limit exceeded and raise_on_exceed is True
        """
        from app.modules.video.models import Video
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Calculate current storage usage
        result = await self.session.execute(
            select(sql_func.coalesce(sql_func.sum(Video.file_size), 0))
            .where(Video.user_id == user_id)
            .where(Video.file_size.isnot(None))
        )
        current_bytes = result.scalar() or 0
        current_gb = current_bytes / (1024 * 1024 * 1024)
        
        limit_gb = float(plan.max_storage_gb)
        
        # Check if unlimited
        if self._is_unlimited(plan.max_storage_gb):
            return True, current_gb, limit_gb, plan.name
        
        # Check with additional bytes
        total_bytes = current_bytes + additional_bytes
        total_gb = total_bytes / (1024 * 1024 * 1024)
        
        has_space = total_gb <= limit_gb
        
        if not has_space and raise_on_exceed:
            raise LimitExceededError(
                resource="Storage",
                current=int(current_gb * 100) / 100,  # Round to 2 decimal
                limit=int(limit_gb),
                plan_name=plan.name,
                message=f"Storage penuh: {current_gb:.2f}GB / {limit_gb}GB untuk plan {plan.name}. Hapus video lama atau upgrade plan."
            )
        
        return has_space, current_gb, limit_gb, plan.name
    
    async def get_bandwidth_usage(
        self,
        user_id: uuid.UUID,
    ) -> Tuple[float, float, str]:
        """Calculate bandwidth usage from stream jobs.
        
        Bandwidth = bitrate (kbps) * duration (seconds) / 8 / 1024 / 1024 = GB
        
        Args:
            user_id: User UUID
            
        Returns:
            Tuple of (current_gb, limit_gb, plan_name)
        """
        from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
        from app.core.datetime_utils import utcnow, ensure_utc
        
        plan, subscription = await self.get_user_plan(user_id)
        
        # Calculate bandwidth from completed/stopped stream jobs in current billing period
        bandwidth_result = await self.session.execute(
            select(
                sql_func.coalesce(
                    sql_func.sum(
                        StreamJob.target_bitrate * StreamJob.total_duration_seconds / 8 / 1024 / 1024
                    ), 
                    0
                )
            )
            .where(StreamJob.user_id == user_id)
            .where(StreamJob.created_at >= subscription.current_period_start)
            .where(StreamJob.total_duration_seconds > 0)
        )
        bandwidth_from_jobs = bandwidth_result.scalar() or 0
        
        # Also calculate bandwidth from currently running streams
        running_streams_result = await self.session.execute(
            select(StreamJob)
            .where(StreamJob.user_id == user_id)
            .where(StreamJob.status == StreamJobStatus.RUNNING.value)
            .where(StreamJob.actual_start_at.isnot(None))
        )
        running_streams = running_streams_result.scalars().all()
        
        running_bandwidth = 0.0
        for stream in running_streams:
            if stream.actual_start_at:
                now = utcnow()
                start = ensure_utc(stream.actual_start_at)
                duration_seconds = (now - start).total_seconds()
                # bitrate (kbps) * duration (s) / 8 / 1024 / 1024 = GB
                running_bandwidth += (stream.target_bitrate * duration_seconds) / 8 / 1024 / 1024
        
        bandwidth_used = float(bandwidth_from_jobs) + running_bandwidth
        limit_gb = float(plan.max_bandwidth_gb)
        
        return bandwidth_used, limit_gb, plan.name
    
    async def get_usage_summary(self, user_id: uuid.UUID) -> dict:
        """Get complete usage summary for a user.
        
        Returns:
            Dictionary with all usage metrics and limits
        """
        plan, subscription = await self.get_user_plan(user_id)
        
        # Get all counts
        _, accounts_count, accounts_limit, _ = await self.check_accounts_limit(user_id, raise_on_exceed=False)
        _, videos_count, videos_limit, _ = await self.check_videos_per_month_limit(user_id, raise_on_exceed=False)
        _, streams_count, streams_limit, _ = await self.check_streams_per_month_limit(user_id, raise_on_exceed=False)
        _, concurrent_count, concurrent_limit, _ = await self.check_concurrent_streams_limit(user_id, raise_on_exceed=False)
        _, storage_gb, storage_limit, _ = await self.check_storage_limit(user_id, raise_on_exceed=False)
        bandwidth_gb, bandwidth_limit, _ = await self.get_bandwidth_usage(user_id)
        
        return {
            "plan": {
                "slug": plan.slug,
                "name": plan.name,
            },
            "subscription": {
                "status": subscription.status,
                "period_start": subscription.current_period_start.isoformat(),
                "period_end": subscription.current_period_end.isoformat(),
            },
            "usage": {
                "accounts": {
                    "current": accounts_count,
                    "limit": accounts_limit,
                    "unlimited": self._is_unlimited(accounts_limit),
                },
                "videos_per_month": {
                    "current": videos_count,
                    "limit": videos_limit,
                    "unlimited": self._is_unlimited(videos_limit),
                },
                "streams_per_month": {
                    "current": streams_count,
                    "limit": streams_limit,
                    "unlimited": self._is_unlimited(streams_limit),
                },
                "concurrent_streams": {
                    "current": concurrent_count,
                    "limit": concurrent_limit,
                    "unlimited": self._is_unlimited(concurrent_limit),
                },
                "storage_gb": {
                    "current": round(storage_gb, 2),
                    "limit": storage_limit,
                    "unlimited": self._is_unlimited(int(storage_limit)),
                },
                "bandwidth_gb": {
                    "current": round(bandwidth_gb, 2),
                    "limit": bandwidth_limit,
                    "unlimited": self._is_unlimited(int(bandwidth_limit)),
                },
            },
        }
