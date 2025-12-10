"""Repository for Billing Service database operations.

Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import (
    Subscription,
    UsageRecord,
    UsageAggregate,
    Invoice,
    PaymentMethod,
    Plan,
    PlanTier,
    SubscriptionStatus,
    UsageResourceType,
    InvoiceStatus,
    PLAN_LIMITS,
)


class PlanRepository:
    """Repository for plan operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> list[Plan]:
        """Get all active plans ordered by sort_order."""
        result = await self.session.execute(
            select(Plan)
            .where(Plan.is_active == True)
            .order_by(Plan.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[Plan]:
        """Get plan by slug."""
        result = await self.session.execute(
            select(Plan).where(Plan.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[Plan]:
        """Get plan by ID."""
        result = await self.session.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Plan:
        """Create a new plan."""
        plan = Plan(**kwargs)
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update(self, plan_id: uuid.UUID, **kwargs) -> Optional[Plan]:
        """Update a plan."""
        plan = await self.get_by_id(plan_id)
        if not plan:
            return None
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan


class SubscriptionRepository:
    """Repository for subscription operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subscription(
        self,
        user_id: uuid.UUID,
        plan_tier: str = PlanTier.FREE.value,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        stripe_price_id: Optional[str] = None,
    ) -> Subscription:
        """Create a new subscription."""
        now = datetime.utcnow()
        if current_period_start is None:
            current_period_start = now
        if current_period_end is None:
            # Default to 30 days for free tier
            current_period_end = now + timedelta(days=30)

        subscription = Subscription(
            user_id=user_id,
            plan_tier=plan_tier,
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_price_id=stripe_price_id,
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: uuid.UUID) -> Optional[Subscription]:
        """Get subscription by ID."""
        result = await self.session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Subscription]:
        """Get subscription by user ID."""
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        **kwargs,
    ) -> Optional[Subscription]:
        """Update subscription fields."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None

        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def update_plan(
        self,
        subscription_id: uuid.UUID,
        new_plan: str,
        stripe_price_id: Optional[str] = None,
    ) -> Optional[Subscription]:
        """Update subscription plan tier."""
        return await self.update_subscription(
            subscription_id,
            plan_tier=new_plan,
            stripe_price_id=stripe_price_id,
        )

    async def cancel_subscription(
        self,
        subscription_id: uuid.UUID,
        cancel_at_period_end: bool = True,
    ) -> Optional[Subscription]:
        """Cancel a subscription."""
        return await self.update_subscription(
            subscription_id,
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=datetime.utcnow(),
        )

    async def expire_subscription(
        self,
        subscription_id: uuid.UUID,
    ) -> Optional[Subscription]:
        """Mark subscription as expired and downgrade to free.
        
        Requirements: 28.4 - Downgrade to free tier
        """
        return await self.update_subscription(
            subscription_id,
            status=SubscriptionStatus.EXPIRED.value,
            plan_tier=PlanTier.FREE.value,
        )

    async def get_expiring_subscriptions(
        self,
        days_until_expiry: int = 7,
    ) -> list[Subscription]:
        """Get subscriptions expiring within specified days."""
        expiry_threshold = datetime.utcnow() + timedelta(days=days_until_expiry)
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE.value,
                    Subscription.current_period_end <= expiry_threshold,
                    Subscription.cancel_at_period_end == True,
                )
            )
        )
        return list(result.scalars().all())

    async def get_expired_subscriptions(self) -> list[Subscription]:
        """Get all subscriptions that have expired and need processing.
        
        Requirements: 28.4 - Expiration handling
        
        Returns subscriptions where:
        - Status is ACTIVE or PAST_DUE
        - Current period has ended
        - cancel_at_period_end is True OR status is PAST_DUE
        """
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.PAST_DUE.value,
                    ]),
                    Subscription.current_period_end < now,
                )
            )
        )
        return list(result.scalars().all())

    async def downgrade_to_free(
        self,
        subscription_id: uuid.UUID,
        preserve_data_until: Optional[datetime] = None,
    ) -> Optional[Subscription]:
        """Downgrade subscription to free tier.
        
        Requirements: 28.4 - Downgrade to free tier, preserve data for 30 days
        
        Args:
            subscription_id: Subscription ID
            preserve_data_until: Date until which data should be preserved
            
        Returns:
            Updated subscription or None
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None
        
        # Store the previous tier for notification purposes
        previous_tier = subscription.plan_tier
        
        # Calculate data preservation date (30 days from now)
        if preserve_data_until is None:
            preserve_data_until = datetime.utcnow() + timedelta(days=30)
        
        # Update subscription
        subscription.status = SubscriptionStatus.EXPIRED.value
        subscription.plan_tier = PlanTier.FREE.value
        
        # Store preservation date in custom_limits for tracking
        if subscription.custom_limits is None:
            subscription.custom_limits = {}
        subscription.custom_limits["data_preserved_until"] = preserve_data_until.isoformat()
        subscription.custom_limits["previous_tier"] = previous_tier
        
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def reactivate_subscription(
        self,
        subscription_id: uuid.UUID,
        plan_tier: str,
        period_end: datetime,
    ) -> Optional[Subscription]:
        """Reactivate an expired subscription.
        
        Args:
            subscription_id: Subscription ID
            plan_tier: New plan tier
            period_end: New period end date
            
        Returns:
            Updated subscription or None
        """
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None
        
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.plan_tier = plan_tier
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = period_end
        subscription.cancel_at_period_end = False
        subscription.canceled_at = None
        
        # Clear preservation data
        if subscription.custom_limits:
            subscription.custom_limits.pop("data_preserved_until", None)
            subscription.custom_limits.pop("previous_tier", None)
        
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription



class UsageRepository:
    """Repository for usage tracking operations.
    
    Requirements: 27.1, 27.2, 27.3, 27.4
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_usage(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        resource_type: str,
        amount: float,
        billing_period_start: date,
        billing_period_end: date,
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        """Record a usage event.
        
        Args:
            user_id: User ID
            subscription_id: Subscription ID
            resource_type: Type of resource being tracked
            amount: Usage amount
            billing_period_start: Start of billing period
            billing_period_end: End of billing period
            metadata: Optional metadata (stored as usage_metadata in model)
        """
        record = UsageRecord(
            user_id=user_id,
            subscription_id=subscription_id,
            resource_type=resource_type,
            amount=amount,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            usage_metadata=metadata,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_usage_records(
        self,
        user_id: uuid.UUID,
        resource_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[UsageRecord], int]:
        """Get usage records with filters."""
        query = select(UsageRecord).where(UsageRecord.user_id == user_id)

        if resource_type:
            query = query.where(UsageRecord.resource_type == resource_type)
        if start_date:
            query = query.where(UsageRecord.billing_period_start >= start_date)
        if end_date:
            query = query.where(UsageRecord.billing_period_end <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(UsageRecord.recorded_at.desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total

    async def get_or_create_aggregate(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        resource_type: str,
        billing_period_start: date,
        billing_period_end: date,
        limit_value: float,
    ) -> UsageAggregate:
        """Get or create usage aggregate for a billing period."""
        result = await self.session.execute(
            select(UsageAggregate).where(
                and_(
                    UsageAggregate.user_id == user_id,
                    UsageAggregate.resource_type == resource_type,
                    UsageAggregate.billing_period_start == billing_period_start,
                )
            )
        )
        aggregate = result.scalar_one_or_none()

        if not aggregate:
            aggregate = UsageAggregate(
                user_id=user_id,
                subscription_id=subscription_id,
                resource_type=resource_type,
                total_used=0.0,
                limit_value=limit_value,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
            )
            self.session.add(aggregate)
            await self.session.commit()
            await self.session.refresh(aggregate)

        return aggregate

    async def update_aggregate(
        self,
        aggregate_id: uuid.UUID,
        amount_to_add: float,
    ) -> UsageAggregate:
        """Update usage aggregate with new amount."""
        result = await self.session.execute(
            select(UsageAggregate).where(UsageAggregate.id == aggregate_id)
        )
        aggregate = result.scalar_one_or_none()
        if aggregate:
            aggregate.total_used += amount_to_add
            await self.session.commit()
            await self.session.refresh(aggregate)
        return aggregate

    async def mark_warning_sent(
        self,
        aggregate_id: uuid.UUID,
        threshold: int,
    ) -> None:
        """Mark that a warning was sent for a threshold.
        
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        """
        result = await self.session.execute(
            select(UsageAggregate).where(UsageAggregate.id == aggregate_id)
        )
        aggregate = result.scalar_one_or_none()
        if aggregate:
            if threshold == 50:
                aggregate.warning_50_sent = True
            elif threshold == 75:
                aggregate.warning_75_sent = True
            elif threshold == 90:
                aggregate.warning_90_sent = True
            await self.session.commit()

    async def get_user_aggregates(
        self,
        user_id: uuid.UUID,
        billing_period_start: date,
    ) -> list[UsageAggregate]:
        """Get all usage aggregates for a user in a billing period."""
        result = await self.session.execute(
            select(UsageAggregate).where(
                and_(
                    UsageAggregate.user_id == user_id,
                    UsageAggregate.billing_period_start == billing_period_start,
                )
            )
        )
        return list(result.scalars().all())

    async def get_usage_breakdown(
        self,
        user_id: uuid.UUID,
        resource_type: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get detailed usage breakdown by metadata.
        
        Requirements: 27.3 - Track encoding minutes per resolution tier
        Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
        """
        result = await self.session.execute(
            select(UsageRecord).where(
                and_(
                    UsageRecord.user_id == user_id,
                    UsageRecord.resource_type == resource_type,
                    UsageRecord.billing_period_start >= start_date,
                    UsageRecord.billing_period_end <= end_date,
                )
            )
        )
        records = result.scalars().all()

        # Group by metadata
        breakdown = {}
        for record in records:
            key = str(record.usage_metadata) if record.usage_metadata else "default"
            if key not in breakdown:
                breakdown[key] = {
                    "metadata": record.usage_metadata,
                    "total_amount": 0.0,
                    "record_count": 0,
                }
            breakdown[key]["total_amount"] += record.amount
            breakdown[key]["record_count"] += 1

        return list(breakdown.values())

    async def get_usage_records_for_export(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        resource_types: Optional[list[str]] = None,
    ) -> list[UsageRecord]:
        """Get all usage records for export.
        
        Requirements: 27.5 - Detailed CSV export with timestamps and resource types
        
        Args:
            user_id: User ID
            start_date: Start date for export
            end_date: End date for export
            resource_types: Optional list of resource types to filter
            
        Returns:
            List of usage records ordered by recorded_at
        """
        query = select(UsageRecord).where(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.recorded_at >= datetime.combine(start_date, datetime.min.time()),
                UsageRecord.recorded_at <= datetime.combine(end_date, datetime.max.time()),
            )
        )
        
        if resource_types:
            query = query.where(UsageRecord.resource_type.in_(resource_types))
        
        query = query.order_by(UsageRecord.recorded_at.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class InvoiceRepository:
    """Repository for invoice operations.
    
    Requirements: 28.3, 28.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_invoice(
        self,
        user_id: uuid.UUID,
        subscription_id: uuid.UUID,
        invoice_number: str,
        period_start: date,
        period_end: date,
        subtotal: int = 0,
        tax: int = 0,
        total: int = 0,
        line_items: Optional[list] = None,
        stripe_invoice_id: Optional[str] = None,
        due_date: Optional[date] = None,
    ) -> Invoice:
        """Create a new invoice."""
        invoice = Invoice(
            user_id=user_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            period_start=period_start,
            period_end=period_end,
            subtotal=subtotal,
            tax=tax,
            total=total,
            amount_due=total,
            line_items=line_items,
            stripe_invoice_id=stripe_invoice_id,
            due_date=due_date,
        )
        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def get_by_id(self, invoice_id: uuid.UUID) -> Optional[Invoice]:
        """Get invoice by ID."""
        result = await self.session.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_id(self, stripe_invoice_id: str) -> Optional[Invoice]:
        """Get invoice by Stripe invoice ID."""
        result = await self.session.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_user_invoices(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        """Get user's invoices with pagination."""
        query = select(Invoice).where(Invoice.user_id == user_id)

        if status:
            query = query.where(Invoice.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Invoice.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)

        return list(result.scalars().all()), total

    async def update_invoice(
        self,
        invoice_id: uuid.UUID,
        **kwargs,
    ) -> Optional[Invoice]:
        """Update invoice fields."""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return None

        for key, value in kwargs.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)

        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def mark_paid(
        self,
        invoice_id: uuid.UUID,
        payment_intent_id: Optional[str] = None,
    ) -> Optional[Invoice]:
        """Mark invoice as paid."""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return None

        invoice.status = InvoiceStatus.PAID.value
        invoice.paid_at = datetime.utcnow()
        invoice.amount_paid = invoice.total
        invoice.amount_due = 0
        if payment_intent_id:
            invoice.payment_intent_id = payment_intent_id

        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice


class PaymentMethodRepository:
    """Repository for payment method operations.
    
    Requirements: 28.3
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment_method(
        self,
        user_id: uuid.UUID,
        stripe_payment_method_id: str,
        card_brand: Optional[str] = None,
        card_last4: Optional[str] = None,
        card_exp_month: Optional[int] = None,
        card_exp_year: Optional[int] = None,
        is_default: bool = False,
    ) -> PaymentMethod:
        """Create a new payment method."""
        # If setting as default, unset other defaults
        if is_default:
            await self.session.execute(
                update(PaymentMethod)
                .where(PaymentMethod.user_id == user_id)
                .values(is_default=False)
            )

        payment_method = PaymentMethod(
            user_id=user_id,
            stripe_payment_method_id=stripe_payment_method_id,
            card_brand=card_brand,
            card_last4=card_last4,
            card_exp_month=card_exp_month,
            card_exp_year=card_exp_year,
            is_default=is_default,
        )
        self.session.add(payment_method)
        await self.session.commit()
        await self.session.refresh(payment_method)
        return payment_method

    async def get_by_id(self, payment_method_id: uuid.UUID) -> Optional[PaymentMethod]:
        """Get payment method by ID."""
        result = await self.session.execute(
            select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
        )
        return result.scalar_one_or_none()

    async def get_user_payment_methods(
        self,
        user_id: uuid.UUID,
    ) -> list[PaymentMethod]:
        """Get all payment methods for a user."""
        result = await self.session.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_default_payment_method(
        self,
        user_id: uuid.UUID,
    ) -> Optional[PaymentMethod]:
        """Get user's default payment method."""
        result = await self.session.execute(
            select(PaymentMethod).where(
                and_(
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.is_default == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def set_default(
        self,
        payment_method_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[PaymentMethod]:
        """Set a payment method as default."""
        # Unset other defaults
        await self.session.execute(
            update(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .values(is_default=False)
        )

        # Set new default
        result = await self.session.execute(
            select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
        )
        payment_method = result.scalar_one_or_none()
        if payment_method:
            payment_method.is_default = True
            await self.session.commit()
            await self.session.refresh(payment_method)
        return payment_method

    async def delete_payment_method(
        self,
        payment_method_id: uuid.UUID,
    ) -> bool:
        """Delete a payment method."""
        result = await self.session.execute(
            delete(PaymentMethod).where(PaymentMethod.id == payment_method_id)
        )
        await self.session.commit()
        return result.rowcount > 0
