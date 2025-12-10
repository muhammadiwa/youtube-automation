"""Billing Service for subscription and usage management.

Implements plan provisioning, usage metering, and payment processing.
Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import (
    Subscription,
    UsageRecord,
    UsageAggregate,
    Invoice,
    PaymentMethod,
    PlanTier,
    SubscriptionStatus,
    UsageResourceType,
    PLAN_LIMITS,
)
from app.modules.billing.repository import (
    PlanRepository,
    SubscriptionRepository,
    UsageRepository,
    InvoiceRepository,
    PaymentMethodRepository,
)
from app.modules.billing.schemas import (
    PlanTier as SchemaPlanTier,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionStatusResponse,
    PlanFeatures,
    PlanComparisonResponse,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageMetric,
    UsageDashboardResponse,
    UsageBreakdownResponse,
    UsageWarningEvent,
    InvoiceResponse,
    InvoiceListResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodListResponse,
    BillingDashboardResponse,
    FeatureCheckRequest,
    FeatureCheckResponse,
)
from app.modules.billing.metering import (
    UsageMeteringService,
    calculate_usage_percent,
    get_warning_threshold,
    should_send_warning,
    get_all_pending_warnings,
)


class BillingService:
    """Service for billing and subscription management.
    
    Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
    """

    # Warning thresholds (Requirements: 27.2)
    WARNING_THRESHOLDS = [50, 75, 90]

    def __init__(self, session: AsyncSession):
        self.session = session
        self.plan_repo = PlanRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.usage_repo = UsageRepository(session)
        self.invoice_repo = InvoiceRepository(session)
        self.payment_repo = PaymentMethodRepository(session)

    # ==================== Plan Provisioning (28.1) ====================

    def get_plan_features(self, plan_tier: str) -> PlanFeatures:
        """Get features and limits for a plan tier.
        
        Requirements: 28.1 - Feature access based on tier
        """
        limits = PLAN_LIMITS.get(plan_tier, PLAN_LIMITS[PlanTier.FREE.value])
        return PlanFeatures(
            tier=SchemaPlanTier(plan_tier),
            api_calls=limits["api_calls"],
            encoding_minutes=limits["encoding_minutes"],
            storage_gb=limits["storage_gb"],
            bandwidth_gb=limits["bandwidth_gb"],
            connected_accounts=limits["connected_accounts"],
            concurrent_streams=limits["concurrent_streams"],
            features=limits["features"],
        )

    def get_all_plan_features(self) -> PlanComparisonResponse:
        """Get features for all plan tiers for comparison (legacy method)."""
        plans = [
            self.get_plan_features(tier.value)
            for tier in PlanTier
        ]
        return PlanComparisonResponse(plans=plans)

    async def get_plans_from_db(self) -> list[dict]:
        """Get all active plans from database.
        
        Requirements: 28.1 - Plan tiers with feature limits
        Returns plans in format suitable for frontend display.
        """
        plans = await self.plan_repo.get_all_active()
        return [plan.to_dict() for plan in plans]

    async def get_plan_by_slug(self, slug: str) -> Optional[dict]:
        """Get a specific plan by slug."""
        plan = await self.plan_repo.get_by_slug(slug)
        return plan.to_dict() if plan else None

    async def check_feature_access(
        self,
        user_id: uuid.UUID,
        feature: str,
    ) -> FeatureCheckResponse:
        """Check if user has access to a feature.
        
        Requirements: 28.1 - Feature access based on tier
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        
        if not subscription:
            # No subscription, use free tier
            current_tier = PlanTier.FREE.value
            has_access = feature in PLAN_LIMITS[PlanTier.FREE.value]["features"]
        else:
            current_tier = subscription.plan_tier
            has_access = subscription.has_feature(feature)

        # Find minimum tier required for this feature
        required_tier = None
        for tier in [PlanTier.FREE, PlanTier.BASIC, PlanTier.PRO, PlanTier.ENTERPRISE]:
            if feature in PLAN_LIMITS[tier.value]["features"]:
                required_tier = tier
                break

        return FeatureCheckResponse(
            feature=feature,
            has_access=has_access,
            required_tier=required_tier,
            current_tier=SchemaPlanTier(current_tier),
            upgrade_required=not has_access,
        )

    async def check_limit(
        self,
        user_id: uuid.UUID,
        resource_type: str,
        requested_amount: float = 1.0,
    ) -> tuple[bool, float, float]:
        """Check if user has remaining quota for a resource.
        
        Returns: (has_quota, current_usage, limit)
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        
        if not subscription:
            limit = PLAN_LIMITS[PlanTier.FREE.value].get(resource_type, 0)
        else:
            limit = subscription.get_limit(resource_type)

        # -1 means unlimited
        if limit == -1:
            return True, 0.0, -1.0

        # Get current usage
        billing_start = subscription.current_period_start.date() if subscription else date.today()
        aggregates = await self.usage_repo.get_user_aggregates(user_id, billing_start)
        
        current_usage = 0.0
        for agg in aggregates:
            if agg.resource_type == resource_type:
                current_usage = agg.total_used
                break

        has_quota = (current_usage + requested_amount) <= limit
        return has_quota, current_usage, float(limit)

    # ==================== Subscription Management (28.1, 28.4) ====================

    async def create_subscription(
        self,
        user_id: uuid.UUID,
        data: SubscriptionCreate,
    ) -> SubscriptionResponse:
        """Create a new subscription for a user.
        
        Requirements: 28.1 - Provision features based on tier
        """
        # Check if user already has a subscription
        existing = await self.subscription_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("User already has a subscription")

        subscription = await self.subscription_repo.create_subscription(
            user_id=user_id,
            plan_tier=data.plan_tier.value,
            stripe_price_id=data.stripe_price_id,
        )

        # Initialize usage aggregates for the billing period
        await self._initialize_usage_aggregates(subscription)

        return self._subscription_to_response(subscription)

    async def get_subscription(
        self,
        user_id: uuid.UUID,
    ) -> Optional[SubscriptionResponse]:
        """Get user's subscription."""
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None
        return self._subscription_to_response(subscription)

    async def get_subscription_status(
        self,
        user_id: uuid.UUID,
    ) -> Optional[SubscriptionStatusResponse]:
        """Get detailed subscription status."""
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None

        days_until_expiry = (subscription.current_period_end - datetime.utcnow()).days
        
        # Determine available upgrades
        tier_order = [PlanTier.FREE, PlanTier.BASIC, PlanTier.PRO, PlanTier.ENTERPRISE]
        current_index = next(
            (i for i, t in enumerate(tier_order) if t.value == subscription.plan_tier),
            0
        )
        available_upgrades = [t for t in tier_order[current_index + 1:]]

        return SubscriptionStatusResponse(
            subscription=self._subscription_to_response(subscription),
            is_active=subscription.is_active(),
            is_expired=subscription.is_expired(),
            days_until_expiry=max(0, days_until_expiry),
            can_upgrade=current_index < len(tier_order) - 1,
            available_upgrades=[SchemaPlanTier(t.value) for t in available_upgrades],
        )

    async def update_subscription(
        self,
        user_id: uuid.UUID,
        data: SubscriptionUpdate,
    ) -> Optional[SubscriptionResponse]:
        """Update user's subscription."""
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "plan_tier" in update_data:
            update_data["plan_tier"] = update_data["plan_tier"].value

        updated = await self.subscription_repo.update_subscription(
            subscription.id,
            **update_data,
        )
        return self._subscription_to_response(updated) if updated else None

    async def cancel_subscription(
        self,
        user_id: uuid.UUID,
        cancel_at_period_end: bool = True,
    ) -> Optional[SubscriptionResponse]:
        """Cancel user's subscription."""
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None

        updated = await self.subscription_repo.cancel_subscription(
            subscription.id,
            cancel_at_period_end=cancel_at_period_end,
        )
        return self._subscription_to_response(updated) if updated else None

    async def handle_subscription_expiry(
        self,
        subscription_id: uuid.UUID,
    ) -> Optional[SubscriptionResponse]:
        """Handle subscription expiry - downgrade to free tier.
        
        Requirements: 28.4 - Downgrade to free tier, preserve data for 30 days
        """
        updated = await self.subscription_repo.downgrade_to_free(subscription_id)
        return self._subscription_to_response(updated) if updated else None

    async def process_expired_subscriptions(self) -> list[dict]:
        """Process all expired subscriptions.
        
        Requirements: 28.4 - Expiration handling, downgrade to free tier
        
        Returns:
            List of processed subscription details
        """
        expired = await self.subscription_repo.get_expired_subscriptions()
        results = []
        
        for subscription in expired:
            previous_tier = subscription.plan_tier
            updated = await self.subscription_repo.downgrade_to_free(subscription.id)
            
            if updated:
                results.append({
                    "subscription_id": str(subscription.id),
                    "user_id": str(subscription.user_id),
                    "previous_tier": previous_tier,
                    "new_tier": PlanTier.FREE.value,
                    "data_preserved_until": (
                        updated.custom_limits.get("data_preserved_until")
                        if updated.custom_limits else None
                    ),
                })
        
        return results

    async def get_expiring_subscriptions(
        self,
        days_until_expiry: int = 7,
    ) -> list[SubscriptionResponse]:
        """Get subscriptions expiring within specified days.
        
        Requirements: 28.4 - Expiration handling
        
        Args:
            days_until_expiry: Number of days to look ahead
            
        Returns:
            List of expiring subscriptions
        """
        subscriptions = await self.subscription_repo.get_expiring_subscriptions(
            days_until_expiry
        )
        return [self._subscription_to_response(s) for s in subscriptions]

    async def reactivate_subscription(
        self,
        user_id: uuid.UUID,
        plan_tier: str,
        period_days: int = 30,
    ) -> Optional[SubscriptionResponse]:
        """Reactivate an expired subscription.
        
        Requirements: 28.4 - Allow reactivation after expiry
        
        Args:
            user_id: User ID
            plan_tier: Plan tier to reactivate to
            period_days: Number of days for the new period
            
        Returns:
            Reactivated subscription or None
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None
        
        period_end = datetime.utcnow() + timedelta(days=period_days)
        updated = await self.subscription_repo.reactivate_subscription(
            subscription.id,
            plan_tier,
            period_end,
        )
        
        if updated:
            # Reinitialize usage aggregates for the new billing period
            await self._initialize_usage_aggregates(updated)
        
        return self._subscription_to_response(updated) if updated else None

    async def check_data_preservation_status(
        self,
        user_id: uuid.UUID,
    ) -> Optional[dict]:
        """Check data preservation status for an expired subscription.
        
        Requirements: 28.4 - Preserve data for 30 days
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with preservation status or None
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            return None
        
        if subscription.status != SubscriptionStatus.EXPIRED.value:
            return {
                "is_expired": False,
                "status": subscription.status,
                "data_at_risk": False,
            }
        
        # Check preservation date
        preserve_until = None
        previous_tier = None
        if subscription.custom_limits:
            preserve_until_str = subscription.custom_limits.get("data_preserved_until")
            if preserve_until_str:
                preserve_until = datetime.fromisoformat(preserve_until_str)
            previous_tier = subscription.custom_limits.get("previous_tier")
        
        now = datetime.utcnow()
        days_remaining = 0
        data_at_risk = False
        
        if preserve_until:
            days_remaining = max(0, (preserve_until - now).days)
            data_at_risk = days_remaining <= 7  # Warning if less than 7 days
        
        return {
            "is_expired": True,
            "status": subscription.status,
            "previous_tier": previous_tier,
            "data_preserved_until": preserve_until.isoformat() if preserve_until else None,
            "days_remaining": days_remaining,
            "data_at_risk": data_at_risk,
        }

    async def _initialize_usage_aggregates(
        self,
        subscription: Subscription,
    ) -> None:
        """Initialize usage aggregates for a new billing period."""
        limits = subscription.get_limits()
        billing_start = subscription.current_period_start.date()
        billing_end = subscription.current_period_end.date()

        for resource_type in UsageResourceType:
            limit = limits.get(resource_type.value, 0)
            await self.usage_repo.get_or_create_aggregate(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                resource_type=resource_type.value,
                billing_period_start=billing_start,
                billing_period_end=billing_end,
                limit_value=float(limit),
            )


    # ==================== Usage Metering (27.1, 27.2, 27.3, 27.4) ====================

    async def record_usage(
        self,
        user_id: uuid.UUID,
        data: UsageRecordCreate,
    ) -> tuple[UsageRecordResponse, Optional[UsageWarningEvent]]:
        """Record usage and check for warnings.
        
        Requirements: 27.1 - Track API calls, encoding, storage, bandwidth
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            raise ValueError("User has no subscription")

        billing_start = subscription.current_period_start.date()
        billing_end = subscription.current_period_end.date()

        # Record the usage
        record = await self.usage_repo.record_usage(
            user_id=user_id,
            subscription_id=subscription.id,
            resource_type=data.resource_type.value,
            amount=data.amount,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
            metadata=data.metadata,
        )

        # Update aggregate
        limit = subscription.get_limit(data.resource_type.value)
        aggregate = await self.usage_repo.get_or_create_aggregate(
            user_id=user_id,
            subscription_id=subscription.id,
            resource_type=data.resource_type.value,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
            limit_value=float(limit),
        )
        await self.usage_repo.update_aggregate(aggregate.id, data.amount)

        # Check for warnings (Requirements: 27.2)
        warning_event = await self._check_usage_warnings(aggregate)

        return self._usage_record_to_response(record), warning_event

    async def _check_usage_warnings(
        self,
        aggregate: UsageAggregate,
    ) -> Optional[UsageWarningEvent]:
        """Check if usage warnings need to be sent.
        
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        """
        # Skip if unlimited
        if aggregate.limit_value == -1:
            return None

        for threshold in self.WARNING_THRESHOLDS:
            if aggregate.needs_warning(threshold):
                await self.usage_repo.mark_warning_sent(aggregate.id, threshold)
                
                percent = aggregate.get_usage_percent()
                return UsageWarningEvent(
                    user_id=aggregate.user_id,
                    resource_type=aggregate.resource_type,
                    threshold_percent=threshold,
                    current_usage=aggregate.total_used,
                    limit=aggregate.limit_value,
                    current_percent=percent,
                    message=f"Usage warning: {aggregate.resource_type} has reached {percent:.1f}% of limit",
                )

        return None

    async def get_usage_dashboard(
        self,
        user_id: uuid.UUID,
    ) -> UsageDashboardResponse:
        """Get usage dashboard for user.
        
        Requirements: 27.1 - Display breakdown of usage
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            raise ValueError("User has no subscription")

        billing_start = subscription.current_period_start.date()
        billing_end = subscription.current_period_end.date()

        aggregates = await self.usage_repo.get_user_aggregates(user_id, billing_start)

        metrics = []
        total_warnings = 0
        for agg in aggregates:
            is_unlimited = agg.limit_value == -1
            percent = 0.0 if is_unlimited else agg.get_usage_percent()
            warning_threshold = agg.get_warning_threshold_reached()
            
            if warning_threshold:
                total_warnings += 1

            metrics.append(UsageMetric(
                resource_type=agg.resource_type,
                used=agg.total_used,
                limit=agg.limit_value,
                percent=percent,
                is_unlimited=is_unlimited,
                warning_threshold_reached=warning_threshold,
            ))

        return UsageDashboardResponse(
            user_id=user_id,
            plan_tier=subscription.plan_tier,
            billing_period_start=billing_start,
            billing_period_end=billing_end,
            metrics=metrics,
            total_warnings_sent=total_warnings,
        )

    async def get_usage_breakdown(
        self,
        user_id: uuid.UUID,
        resource_type: str,
        start_date: date,
        end_date: date,
    ) -> UsageBreakdownResponse:
        """Get detailed usage breakdown.
        
        Requirements: 27.3 - Track encoding minutes per resolution tier
        Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        limit = subscription.get_limit(resource_type) if subscription else 0

        breakdown = await self.usage_repo.get_usage_breakdown(
            user_id=user_id,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
        )

        total_used = sum(item["total_amount"] for item in breakdown)

        return UsageBreakdownResponse(
            resource_type=resource_type,
            total_used=total_used,
            limit=float(limit),
            breakdown=breakdown,
        )

    async def record_api_call(
        self,
        user_id: uuid.UUID,
        endpoint: str,
        method: str,
    ) -> tuple[UsageRecordResponse, Optional[UsageWarningEvent]]:
        """Record an API call.
        
        Requirements: 27.1 - Track API calls
        
        Args:
            user_id: User ID
            endpoint: API endpoint called
            method: HTTP method used
            
        Returns:
            Tuple of (usage record, warning event if any)
        """
        data = UsageRecordCreate(
            resource_type=UsageResourceType.API_CALLS,
            amount=1.0,
            metadata={"endpoint": endpoint, "method": method},
        )
        return await self.record_usage(user_id, data)

    async def record_encoding_minutes(
        self,
        user_id: uuid.UUID,
        minutes: float,
        resolution: str,
        video_id: Optional[str] = None,
    ) -> tuple[UsageRecordResponse, Optional[UsageWarningEvent]]:
        """Record encoding minutes usage.
        
        Requirements: 27.1 - Track encoding minutes
        Requirements: 27.3 - Track encoding minutes per resolution tier
        
        Args:
            user_id: User ID
            minutes: Encoding minutes used
            resolution: Resolution tier (720p, 1080p, 2K, 4K)
            video_id: Optional video ID for attribution
            
        Returns:
            Tuple of (usage record, warning event if any)
        """
        metadata = {"resolution": resolution}
        if video_id:
            metadata["video_id"] = video_id
        
        data = UsageRecordCreate(
            resource_type=UsageResourceType.ENCODING_MINUTES,
            amount=minutes,
            metadata=metadata,
        )
        return await self.record_usage(user_id, data)

    async def record_storage(
        self,
        user_id: uuid.UUID,
        size_gb: float,
        file_type: str,
        file_id: Optional[str] = None,
    ) -> tuple[UsageRecordResponse, Optional[UsageWarningEvent]]:
        """Record storage usage.
        
        Requirements: 27.1 - Track storage
        
        Args:
            user_id: User ID
            size_gb: Storage size in GB
            file_type: Type of file (video, thumbnail, backup, etc.)
            file_id: Optional file ID for attribution
            
        Returns:
            Tuple of (usage record, warning event if any)
        """
        metadata = {"file_type": file_type}
        if file_id:
            metadata["file_id"] = file_id
        
        data = UsageRecordCreate(
            resource_type=UsageResourceType.STORAGE_GB,
            amount=size_gb,
            metadata=metadata,
        )
        return await self.record_usage(user_id, data)

    async def record_bandwidth(
        self,
        user_id: uuid.UUID,
        size_gb: float,
        usage_type: str,
        resource_id: Optional[str] = None,
    ) -> tuple[UsageRecordResponse, Optional[UsageWarningEvent]]:
        """Record bandwidth usage.
        
        Requirements: 27.1 - Track bandwidth
        Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
        
        Args:
            user_id: User ID
            size_gb: Bandwidth used in GB
            usage_type: Type of usage (stream, upload, download)
            resource_id: Optional stream/video ID for attribution
            
        Returns:
            Tuple of (usage record, warning event if any)
        """
        metadata = {"usage_type": usage_type}
        if resource_id:
            metadata["resource_id"] = resource_id
        
        data = UsageRecordCreate(
            resource_type=UsageResourceType.BANDWIDTH_GB,
            amount=size_gb,
            metadata=metadata,
        )
        return await self.record_usage(user_id, data)

    async def get_encoding_breakdown_by_resolution(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get encoding usage breakdown by resolution tier.
        
        Requirements: 27.3 - Track encoding minutes per resolution tier
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with resolution breakdown
        """
        breakdown = await self.get_usage_breakdown(
            user_id=user_id,
            resource_type=UsageResourceType.ENCODING_MINUTES.value,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Group by resolution
        by_resolution = {}
        for item in breakdown.breakdown:
            metadata = item.get("metadata") or {}
            resolution = metadata.get("resolution", "unknown")
            if resolution not in by_resolution:
                by_resolution[resolution] = {
                    "resolution": resolution,
                    "total_minutes": 0.0,
                    "record_count": 0,
                }
            by_resolution[resolution]["total_minutes"] += item.get("total_amount", 0)
            by_resolution[resolution]["record_count"] += item.get("record_count", 0)
        
        return {
            "total_minutes": breakdown.total_used,
            "limit": breakdown.limit,
            "by_resolution": list(by_resolution.values()),
        }

    async def get_bandwidth_breakdown_by_source(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get bandwidth usage breakdown by source.
        
        Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with bandwidth breakdown by source
        """
        breakdown = await self.get_usage_breakdown(
            user_id=user_id,
            resource_type=UsageResourceType.BANDWIDTH_GB.value,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Group by usage type
        by_type = {}
        by_resource = {}
        
        for item in breakdown.breakdown:
            metadata = item.get("metadata") or {}
            usage_type = metadata.get("usage_type", "unknown")
            resource_id = metadata.get("resource_id")
            amount = item.get("total_amount", 0)
            
            # Group by type
            if usage_type not in by_type:
                by_type[usage_type] = 0.0
            by_type[usage_type] += amount
            
            # Group by resource if available
            if resource_id:
                if resource_id not in by_resource:
                    by_resource[resource_id] = {
                        "resource_id": resource_id,
                        "usage_type": usage_type,
                        "total_gb": 0.0,
                    }
                by_resource[resource_id]["total_gb"] += amount
        
        return {
            "total_gb": breakdown.total_used,
            "limit": breakdown.limit,
            "by_type": by_type,
            "by_resource": list(by_resource.values()),
        }

    # ==================== Usage Export (27.5) ====================

    async def export_usage_to_csv(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        resource_types: Optional[list[str]] = None,
    ) -> dict:
        """Export usage data to CSV file.
        
        Requirements: 27.5 - Detailed CSV export with timestamps and resource types
        
        Args:
            user_id: User ID
            start_date: Start date for export
            end_date: End date for export
            resource_types: Optional list of resource types to filter
            
        Returns:
            Dict with download_url, filename, record_count, and generated_at
        """
        import csv
        import io
        from app.core.storage import storage_service
        
        # Get all usage records for the date range
        records = await self.usage_repo.get_usage_records_for_export(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            resource_types=resource_types,
        )
        
        # Generate CSV content
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write header row
        writer.writerow([
            "record_id",
            "user_id",
            "subscription_id",
            "resource_type",
            "amount",
            "billing_period_start",
            "billing_period_end",
            "recorded_at",
            "metadata",
        ])
        
        # Write data rows
        for record in records:
            metadata_str = ""
            if record.usage_metadata:
                import json
                metadata_str = json.dumps(record.usage_metadata)
            
            writer.writerow([
                str(record.id),
                str(record.user_id),
                str(record.subscription_id),
                record.resource_type,
                record.amount,
                record.billing_period_start.isoformat(),
                record.billing_period_end.isoformat(),
                record.recorded_at.isoformat(),
                metadata_str,
            ])
        
        # Get CSV content as bytes
        csv_content = csv_buffer.getvalue().encode("utf-8")
        csv_buffer.close()
        
        # Generate filename
        generated_at = datetime.utcnow()
        filename = f"usage_export_{user_id.hex[:8]}_{start_date.isoformat()}_{end_date.isoformat()}_{generated_at.strftime('%Y%m%d%H%M%S')}.csv"
        
        # Upload to storage
        storage_key = f"exports/usage/{user_id}/{filename}"
        result = await storage_service.upload_file(
            key=storage_key,
            content=csv_content,
            content_type="text/csv",
        )
        
        if not result.success:
            raise ValueError(f"Failed to upload export file: {result.error_message}")
        
        # Get download URL (expires in 1 hour)
        download_url = await storage_service.get_url(storage_key, expires_in=3600)
        
        return {
            "download_url": download_url,
            "filename": filename,
            "record_count": len(records),
            "generated_at": generated_at,
        }

    # ==================== Invoice Management (28.3, 28.5) ====================

    async def get_invoices(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InvoiceListResponse:
        """Get user's invoices.
        
        Requirements: 28.5 - Invoice history
        """
        offset = (page - 1) * page_size
        invoices, total = await self.invoice_repo.get_user_invoices(
            user_id=user_id,
            status=status,
            limit=page_size,
            offset=offset,
        )

        return InvoiceListResponse(
            invoices=[self._invoice_to_response(inv) for inv in invoices],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(invoices)) < total,
        )

    async def get_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> Optional[InvoiceResponse]:
        """Get a specific invoice."""
        invoice = await self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            return None
        return self._invoice_to_response(invoice)

    async def generate_invoice(
        self,
        user_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> InvoiceResponse:
        """Generate an invoice for a billing period.
        
        Requirements: 28.3 - Invoice generation
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            raise ValueError("User has no subscription")

        # Generate invoice number
        invoice_number = f"INV-{user_id.hex[:8].upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Calculate line items based on plan
        line_items = [
            {
                "description": f"{subscription.plan_tier.title()} Plan - Monthly",
                "quantity": 1,
                "unit_price": self._get_plan_price(subscription.plan_tier),
                "amount": self._get_plan_price(subscription.plan_tier),
            }
        ]

        subtotal = sum(item["amount"] for item in line_items)
        tax = 0  # Tax calculation would go here
        total = subtotal + tax

        invoice = await self.invoice_repo.create_invoice(
            user_id=user_id,
            subscription_id=subscription.id,
            invoice_number=invoice_number,
            period_start=period_start,
            period_end=period_end,
            subtotal=subtotal,
            tax=tax,
            total=total,
            line_items=line_items,
            due_date=period_end + timedelta(days=7),
        )

        return self._invoice_to_response(invoice)

    def _get_plan_price(self, plan_tier: str) -> int:
        """Get plan price in cents."""
        prices = {
            PlanTier.FREE.value: 0,
            PlanTier.BASIC.value: 1999,  # $19.99
            PlanTier.PRO.value: 4999,    # $49.99
            PlanTier.ENTERPRISE.value: 19999,  # $199.99
        }
        return prices.get(plan_tier, 0)

    # ==================== Payment Methods (28.3) ====================

    async def add_payment_method(
        self,
        user_id: uuid.UUID,
        data: PaymentMethodCreate,
    ) -> PaymentMethodResponse:
        """Add a payment method.
        
        Requirements: 28.3 - Payment processing
        """
        payment_method = await self.payment_repo.create_payment_method(
            user_id=user_id,
            stripe_payment_method_id=data.stripe_payment_method_id,
            is_default=data.set_as_default,
        )
        return self._payment_method_to_response(payment_method)

    async def get_payment_methods(
        self,
        user_id: uuid.UUID,
    ) -> PaymentMethodListResponse:
        """Get user's payment methods."""
        methods = await self.payment_repo.get_user_payment_methods(user_id)
        default = await self.payment_repo.get_default_payment_method(user_id)

        return PaymentMethodListResponse(
            payment_methods=[self._payment_method_to_response(m) for m in methods],
            default_payment_method_id=default.id if default else None,
        )

    async def set_default_payment_method(
        self,
        user_id: uuid.UUID,
        payment_method_id: uuid.UUID,
    ) -> Optional[PaymentMethodResponse]:
        """Set a payment method as default."""
        method = await self.payment_repo.set_default(payment_method_id, user_id)
        if not method:
            return None
        return self._payment_method_to_response(method)

    async def delete_payment_method(
        self,
        payment_method_id: uuid.UUID,
    ) -> bool:
        """Delete a payment method."""
        return await self.payment_repo.delete_payment_method(payment_method_id)

    # ==================== Billing Dashboard (28.5) ====================

    async def get_billing_dashboard(
        self,
        user_id: uuid.UUID,
    ) -> BillingDashboardResponse:
        """Get complete billing dashboard.
        
        Requirements: 28.5 - Usage breakdown, invoice history
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            raise ValueError("User has no subscription")

        usage = await self.get_usage_dashboard(user_id)
        invoices_response = await self.get_invoices(user_id, page_size=5)
        payment_methods = await self.get_payment_methods(user_id)

        # Calculate next billing date
        next_billing_date = None
        if subscription.is_active() and not subscription.cancel_at_period_end:
            next_billing_date = subscription.current_period_end.date()

        # Estimate next invoice
        estimated_next = self._get_plan_price(subscription.plan_tier)

        return BillingDashboardResponse(
            subscription=self._subscription_to_response(subscription),
            usage=usage,
            recent_invoices=invoices_response.invoices,
            payment_methods=payment_methods.payment_methods,
            next_billing_date=next_billing_date,
            estimated_next_invoice=estimated_next if estimated_next > 0 else None,
        )

    # ==================== Helper Methods ====================

    def _subscription_to_response(self, subscription: Subscription) -> SubscriptionResponse:
        """Convert subscription model to response schema."""
        return SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_tier=subscription.plan_tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            trial_start=subscription.trial_start,
            trial_end=subscription.trial_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            features=subscription.get_features(),
            limits=subscription.get_limits(),
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    def _usage_record_to_response(self, record: UsageRecord) -> UsageRecordResponse:
        """Convert usage record model to response schema."""
        return UsageRecordResponse(
            id=record.id,
            user_id=record.user_id,
            subscription_id=record.subscription_id,
            resource_type=record.resource_type,
            amount=record.amount,
            metadata=record.usage_metadata,
            billing_period_start=record.billing_period_start,
            billing_period_end=record.billing_period_end,
            recorded_at=record.recorded_at,
        )

    def _invoice_to_response(self, invoice: Invoice) -> InvoiceResponse:
        """Convert invoice model to response schema."""
        return InvoiceResponse(
            id=invoice.id,
            user_id=invoice.user_id,
            subscription_id=invoice.subscription_id,
            invoice_number=invoice.invoice_number,
            status=invoice.status,
            subtotal=invoice.subtotal,
            tax=invoice.tax,
            total=invoice.total,
            amount_paid=invoice.amount_paid,
            amount_due=invoice.amount_due,
            currency=invoice.currency,
            period_start=invoice.period_start,
            period_end=invoice.period_end,
            line_items=invoice.line_items,
            paid_at=invoice.paid_at,
            invoice_pdf_url=invoice.invoice_pdf_url,
            hosted_invoice_url=invoice.hosted_invoice_url,
            created_at=invoice.created_at,
            due_date=invoice.due_date,
        )

    def _payment_method_to_response(self, method: PaymentMethod) -> PaymentMethodResponse:
        """Convert payment method model to response schema."""
        return PaymentMethodResponse(
            id=method.id,
            user_id=method.user_id,
            card_brand=method.card_brand,
            card_last4=method.card_last4,
            card_exp_month=method.card_exp_month,
            card_exp_year=method.card_exp_year,
            is_default=method.is_default,
            created_at=method.created_at,
        )


# ==================== Standalone Functions for Property Testing ====================

def get_plan_features(plan_tier: str) -> dict:
    """Get features and limits for a plan tier.
    
    Requirements: 28.1 - Feature access based on tier
    
    Args:
        plan_tier: The plan tier (free, basic, pro, enterprise)
        
    Returns:
        Dictionary with features and limits for the tier
    """
    return PLAN_LIMITS.get(plan_tier, PLAN_LIMITS[PlanTier.FREE.value])


def has_feature_access(plan_tier: str, feature: str) -> bool:
    """Check if a plan tier has access to a feature.
    
    Requirements: 28.1 - Feature access based on tier
    
    Args:
        plan_tier: The plan tier
        feature: The feature to check
        
    Returns:
        True if the tier has access to the feature
    """
    limits = get_plan_features(plan_tier)
    return feature in limits.get("features", [])


def get_limit_for_resource(plan_tier: str, resource: str) -> int:
    """Get the limit for a resource in a plan tier.
    
    Args:
        plan_tier: The plan tier
        resource: The resource type
        
    Returns:
        The limit value (-1 for unlimited)
    """
    limits = get_plan_features(plan_tier)
    return limits.get(resource, 0)


def calculate_usage_percent(used: float, limit: float) -> float:
    """Calculate usage as percentage of limit.
    
    Args:
        used: Amount used
        limit: Limit value (-1 for unlimited)
        
    Returns:
        Usage percentage (0.0 for unlimited)
    """
    if limit == -1:
        return 0.0
    if limit <= 0:
        return 100.0
    return (used / limit) * 100


def get_warning_threshold(usage_percent: float) -> Optional[int]:
    """Get the warning threshold reached for a usage percentage.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    Args:
        usage_percent: Current usage percentage
        
    Returns:
        The highest threshold reached (50, 75, 90) or None
    """
    if usage_percent >= 90:
        return 90
    elif usage_percent >= 75:
        return 75
    elif usage_percent >= 50:
        return 50
    return None


def should_send_warning(
    usage_percent: float,
    warning_50_sent: bool,
    warning_75_sent: bool,
    warning_90_sent: bool,
) -> Optional[int]:
    """Determine if a warning should be sent.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    Args:
        usage_percent: Current usage percentage
        warning_50_sent: Whether 50% warning was sent
        warning_75_sent: Whether 75% warning was sent
        warning_90_sent: Whether 90% warning was sent
        
    Returns:
        The threshold to warn about, or None if no warning needed
    """
    if usage_percent >= 90 and not warning_90_sent:
        return 90
    elif usage_percent >= 75 and not warning_75_sent:
        return 75
    elif usage_percent >= 50 and not warning_50_sent:
        return 50
    return None


# ==================== Stripe Payment Integration (28.3) ====================

class StripePaymentService:
    """Service for Stripe payment integration.
    
    Requirements: 28.3 - Stripe integration, Invoice generation
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_repo = SubscriptionRepository(session)
        self.invoice_repo = InvoiceRepository(session)
        self.payment_repo = PaymentMethodRepository(session)
        self._stripe_client = None

    @property
    def stripe_client(self):
        """Lazy load Stripe client."""
        if self._stripe_client is None:
            from app.modules.billing.stripe_client import get_stripe_client
            self._stripe_client = get_stripe_client()
        return self._stripe_client

    async def create_or_get_stripe_customer(
        self,
        user_id: uuid.UUID,
        email: str,
        name: Optional[str] = None,
    ) -> str:
        """Create or get a Stripe customer for a user.
        
        Args:
            user_id: User ID
            email: User email
            name: User name
            
        Returns:
            Stripe customer ID
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        
        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id
        
        # Create new Stripe customer
        customer = self.stripe_client.create_customer(
            email=email,
            name=name,
            metadata={"user_id": str(user_id)},
        )
        
        # Update subscription with Stripe customer ID
        if subscription:
            await self.subscription_repo.update_subscription(
                subscription.id,
                stripe_customer_id=customer.id,
            )
        
        return customer.id

    async def create_checkout_session(
        self,
        user_id: uuid.UUID,
        plan_tier: str,
        success_url: str,
        cancel_url: str,
        email: str,
        name: Optional[str] = None,
        trial_days: Optional[int] = None,
    ) -> dict:
        """Create a Stripe checkout session for subscription.
        
        Requirements: 28.3 - Stripe integration
        
        Args:
            user_id: User ID
            plan_tier: Plan tier to subscribe to
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            email: User email
            name: User name
            trial_days: Trial period in days
            
        Returns:
            Dict with session_id and url
        """
        # Get or create Stripe customer
        customer_id = await self.create_or_get_stripe_customer(user_id, email, name)
        
        # Get price ID for plan
        price_id = self.stripe_client.get_price_id_for_plan(plan_tier)
        if not price_id:
            raise ValueError(f"No Stripe price configured for plan: {plan_tier}")
        
        # Create checkout session
        return self.stripe_client.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            trial_days=trial_days,
            metadata={"user_id": str(user_id), "plan_tier": plan_tier},
        )

    async def create_billing_portal_session(
        self,
        user_id: uuid.UUID,
        return_url: str,
    ) -> dict:
        """Create a Stripe billing portal session.
        
        Args:
            user_id: User ID
            return_url: URL to return to after portal
            
        Returns:
            Dict with session_id and url
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("User has no Stripe customer")
        
        return self.stripe_client.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url,
        )

    async def attach_payment_method(
        self,
        user_id: uuid.UUID,
        payment_method_id: str,
        set_as_default: bool = True,
    ) -> dict:
        """Attach a payment method to a user's Stripe customer.
        
        Requirements: 28.3 - Payment processing
        
        Args:
            user_id: User ID
            payment_method_id: Stripe payment method ID
            set_as_default: Whether to set as default
            
        Returns:
            Payment method details
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription or not subscription.stripe_customer_id:
            raise ValueError("User has no Stripe customer")
        
        # Attach to Stripe customer
        pm_data = self.stripe_client.attach_payment_method(
            payment_method_id=payment_method_id,
            customer_id=subscription.stripe_customer_id,
        )
        
        # Set as default if requested
        if set_as_default:
            self.stripe_client.update_customer(
                customer_id=subscription.stripe_customer_id,
                default_payment_method=payment_method_id,
            )
        
        # Store in our database
        await self.payment_repo.create_payment_method(
            user_id=user_id,
            stripe_payment_method_id=pm_data.id,
            card_brand=pm_data.card_brand,
            card_last4=pm_data.card_last4,
            card_exp_month=pm_data.card_exp_month,
            card_exp_year=pm_data.card_exp_year,
            is_default=set_as_default,
        )
        
        return {
            "id": pm_data.id,
            "card_brand": pm_data.card_brand,
            "card_last4": pm_data.card_last4,
            "card_exp_month": pm_data.card_exp_month,
            "card_exp_year": pm_data.card_exp_year,
        }

    async def upgrade_subscription(
        self,
        user_id: uuid.UUID,
        new_plan_tier: str,
    ) -> dict:
        """Upgrade a user's subscription to a new plan.
        
        Requirements: 28.3 - Stripe integration
        
        Args:
            user_id: User ID
            new_plan_tier: New plan tier
            
        Returns:
            Updated subscription details
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription:
            raise ValueError("User has no subscription")
        
        if not subscription.stripe_subscription_id:
            raise ValueError("User has no Stripe subscription")
        
        # Get new price ID
        price_id = self.stripe_client.get_price_id_for_plan(new_plan_tier)
        if not price_id:
            raise ValueError(f"No Stripe price configured for plan: {new_plan_tier}")
        
        # Update Stripe subscription
        stripe_sub = self.stripe_client.update_subscription(
            subscription_id=subscription.stripe_subscription_id,
            price_id=price_id,
        )
        
        # Update local subscription
        await self.subscription_repo.update_subscription(
            subscription.id,
            plan_tier=new_plan_tier,
            stripe_price_id=price_id,
            current_period_start=stripe_sub.current_period_start,
            current_period_end=stripe_sub.current_period_end,
        )
        
        return {
            "plan_tier": new_plan_tier,
            "status": stripe_sub.status,
            "current_period_end": stripe_sub.current_period_end.isoformat(),
        }

    async def cancel_stripe_subscription(
        self,
        user_id: uuid.UUID,
        cancel_at_period_end: bool = True,
    ) -> dict:
        """Cancel a user's Stripe subscription.
        
        Args:
            user_id: User ID
            cancel_at_period_end: Whether to cancel at period end
            
        Returns:
            Cancellation details
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)
        if not subscription or not subscription.stripe_subscription_id:
            raise ValueError("User has no Stripe subscription")
        
        # Cancel in Stripe
        stripe_sub = self.stripe_client.cancel_subscription(
            subscription_id=subscription.stripe_subscription_id,
            cancel_at_period_end=cancel_at_period_end,
        )
        
        # Update local subscription
        await self.subscription_repo.cancel_subscription(
            subscription.id,
            cancel_at_period_end=cancel_at_period_end,
        )
        
        return {
            "status": stripe_sub.status,
            "cancel_at_period_end": stripe_sub.cancel_at_period_end,
            "current_period_end": stripe_sub.current_period_end.isoformat(),
        }

    async def sync_invoice_from_stripe(
        self,
        stripe_invoice_id: str,
    ) -> Optional[Invoice]:
        """Sync an invoice from Stripe to local database.
        
        Requirements: 28.3 - Invoice generation
        
        Args:
            stripe_invoice_id: Stripe invoice ID
            
        Returns:
            Local Invoice model or None
        """
        stripe_inv = self.stripe_client.get_invoice(stripe_invoice_id)
        if not stripe_inv:
            return None
        
        # Find subscription by Stripe customer ID
        # This is a simplified lookup - in production you'd have a customer table
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(
            stripe_inv.subscription_id
        ) if stripe_inv.subscription_id else None
        
        if not subscription:
            return None
        
        # Check if invoice already exists
        existing = await self.invoice_repo.get_by_stripe_id(stripe_invoice_id)
        if existing:
            # Update existing invoice
            return await self.invoice_repo.update_invoice(
                existing.id,
                status=stripe_inv.status,
                amount_paid=stripe_inv.amount_paid,
                amount_due=stripe_inv.amount_due,
                paid_at=datetime.utcnow() if stripe_inv.status == "paid" else None,
                invoice_pdf_url=stripe_inv.invoice_pdf,
                hosted_invoice_url=stripe_inv.hosted_invoice_url,
                payment_intent_id=stripe_inv.payment_intent_id,
            )
        
        # Create new invoice
        invoice_number = f"INV-{stripe_invoice_id[-8:].upper()}"
        return await self.invoice_repo.create_invoice(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            invoice_number=invoice_number,
            period_start=stripe_inv.period_start.date(),
            period_end=stripe_inv.period_end.date(),
            subtotal=stripe_inv.subtotal,
            tax=stripe_inv.tax,
            total=stripe_inv.total,
            stripe_invoice_id=stripe_invoice_id,
        )

    async def handle_webhook_event(self, event: dict) -> dict:
        """Handle a Stripe webhook event.
        
        Requirements: 28.3 - Stripe integration
        
        Args:
            event: Stripe webhook event
            
        Returns:
            Processing result
        """
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})
        
        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "payment_method.attached": self._handle_payment_method_attached,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return await handler(data)
        
        return {"status": "ignored", "event_type": event_type}

    async def _handle_subscription_created(self, data: dict) -> dict:
        """Handle subscription.created webhook."""
        stripe_sub_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        
        # Find subscription by Stripe subscription ID
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(stripe_sub_id)
        if subscription:
            await self.subscription_repo.update_subscription(
                subscription.id,
                status=status,
                current_period_start=datetime.fromtimestamp(data.get("current_period_start", 0)),
                current_period_end=datetime.fromtimestamp(data.get("current_period_end", 0)),
            )
        
        return {"status": "processed", "subscription_id": stripe_sub_id}

    async def _handle_subscription_updated(self, data: dict) -> dict:
        """Handle subscription.updated webhook."""
        stripe_sub_id = data.get("id")
        status = data.get("status")
        cancel_at_period_end = data.get("cancel_at_period_end", False)
        
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(stripe_sub_id)
        if subscription:
            await self.subscription_repo.update_subscription(
                subscription.id,
                status=status,
                cancel_at_period_end=cancel_at_period_end,
                current_period_start=datetime.fromtimestamp(data.get("current_period_start", 0)),
                current_period_end=datetime.fromtimestamp(data.get("current_period_end", 0)),
            )
        
        return {"status": "processed", "subscription_id": stripe_sub_id}

    async def _handle_subscription_deleted(self, data: dict) -> dict:
        """Handle subscription.deleted webhook."""
        stripe_sub_id = data.get("id")
        
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(stripe_sub_id)
        if subscription:
            await self.subscription_repo.expire_subscription(subscription.id)
        
        return {"status": "processed", "subscription_id": stripe_sub_id}

    async def _handle_invoice_paid(self, data: dict) -> dict:
        """Handle invoice.paid webhook."""
        stripe_invoice_id = data.get("id")
        await self.sync_invoice_from_stripe(stripe_invoice_id)
        return {"status": "processed", "invoice_id": stripe_invoice_id}

    async def _handle_invoice_payment_failed(self, data: dict) -> dict:
        """Handle invoice.payment_failed webhook."""
        stripe_invoice_id = data.get("id")
        stripe_sub_id = data.get("subscription")
        
        # Update subscription status
        if stripe_sub_id:
            subscription = await self.subscription_repo.get_by_stripe_subscription_id(stripe_sub_id)
            if subscription:
                await self.subscription_repo.update_subscription(
                    subscription.id,
                    status=SubscriptionStatus.PAST_DUE.value,
                )
        
        return {"status": "processed", "invoice_id": stripe_invoice_id}

    async def _handle_payment_method_attached(self, data: dict) -> dict:
        """Handle payment_method.attached webhook."""
        pm_id = data.get("id")
        return {"status": "processed", "payment_method_id": pm_id}
