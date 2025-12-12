"""Admin Billing Service for subscription and revenue management.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Subscription & Revenue Management
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import (
    Subscription,
    Invoice,
    Plan,
    PlanTier,
    SubscriptionStatus,
    InvoiceStatus,
)
from app.modules.billing.repository import (
    SubscriptionRepository,
    InvoiceRepository,
    PlanRepository,
)
from app.modules.payment_gateway.models import (
    PaymentTransaction,
    PaymentStatus,
    PaymentGatewayConfig,
)
from app.modules.payment_gateway.repository import (
    PaymentTransactionRepository,
    PaymentGatewayRepository,
)
from app.modules.payment_gateway.service import PaymentGatewayFactory
from app.modules.admin.schemas import (
    AdminSubscriptionListResponse,
    AdminSubscriptionResponse,
    AdminSubscriptionFilters,
    SubscriptionUpgradeRequest,
    SubscriptionDowngradeRequest,
    SubscriptionExtendRequest,
    RefundRequest,
    RefundResponse,
    RevenueAnalyticsResponse,
    RevenueByPlan,
    RevenueByGateway,
)
from app.modules.admin.audit import AdminAuditService, AdminAuditEvent

logger = logging.getLogger(__name__)


class AdminAuditLogger:
    """Helper class for async audit logging in billing service."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_admin_action(
        self,
        admin_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID,
        details: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log an admin action asynchronously."""
        # Map action to AdminAuditEvent
        event_map = {
            "subscription_upgrade": AdminAuditEvent.SUBSCRIPTION_MODIFIED,
            "subscription_downgrade": AdminAuditEvent.SUBSCRIPTION_MODIFIED,
            "subscription_extended": AdminAuditEvent.SUBSCRIPTION_MODIFIED,
            "refund_processed": AdminAuditEvent.REFUND_PROCESSED,
        }
        event = event_map.get(action, AdminAuditEvent.SUBSCRIPTION_MODIFIED)
        
        # Get admin record to get admin_id
        from app.modules.admin.models import Admin
        result = await self.session.execute(
            select(Admin).where(Admin.user_id == admin_id)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            AdminAuditService.log(
                admin_id=admin.id,
                admin_user_id=admin_id,
                event=event,
                resource_type=resource_type,
                resource_id=str(resource_id),
                details={**details, "action": action},
                ip_address=ip_address,
                user_agent=user_agent,
            )


class SubscriptionNotFoundError(Exception):
    """Raised when subscription is not found."""
    pass


class PaymentNotFoundError(Exception):
    """Raised when payment transaction is not found."""
    pass


class RefundError(Exception):
    """Raised when refund processing fails."""
    pass


class AdminBillingService:
    """Service for admin billing operations.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Subscription & Revenue Management
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_repo = SubscriptionRepository(session)
        self.invoice_repo = InvoiceRepository(session)
        self.plan_repo = PlanRepository(session)
        self.transaction_repo = PaymentTransactionRepository(session)
        self.gateway_repo = PaymentGatewayRepository(session)
        self.audit_logger = AdminAuditLogger(session)

    # ==================== Subscription Management (4.1, 4.2) ====================

    async def get_subscriptions(
        self,
        filters: AdminSubscriptionFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminSubscriptionListResponse:
        """Get all subscriptions with filters.
        
        Requirements: 4.1 - Display all subscriptions with user, plan, status, dates
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated subscription list
        """
        from app.modules.auth.models import User
        
        query = select(Subscription).join(
            User, Subscription.user_id == User.id
        )
        
        # Apply filters
        if filters.plan:
            query = query.where(Subscription.plan_tier == filters.plan)
        
        if filters.status:
            query = query.where(Subscription.status == filters.status)
        
        if filters.user_search:
            search_term = f"%{filters.user_search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.name.ilike(search_term),
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Subscription.created_at.desc())
        query = query.limit(page_size).offset(offset)
        
        result = await self.session.execute(query)
        subscriptions = result.scalars().all()
        
        # Build response with user info
        items = []
        for sub in subscriptions:
            user_result = await self.session.execute(
                select(User).where(User.id == sub.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            items.append(AdminSubscriptionResponse(
                id=sub.id,
                user_id=sub.user_id,
                user_email=user.email if user else None,
                user_name=user.name if user else None,
                plan_tier=sub.plan_tier,
                status=sub.status,
                billing_cycle=sub.billing_cycle,
                current_period_start=sub.current_period_start,
                current_period_end=sub.current_period_end,
                cancel_at_period_end=sub.cancel_at_period_end,
                canceled_at=sub.canceled_at,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return AdminSubscriptionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_subscription(
        self,
        subscription_id: uuid.UUID,
    ) -> AdminSubscriptionResponse:
        """Get subscription by ID.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription details
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        from app.modules.auth.models import User
        
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        user_result = await self.session.execute(
            select(User).where(User.id == subscription.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        return AdminSubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
            plan_tier=subscription.plan_tier,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    async def upgrade_subscription(
        self,
        subscription_id: uuid.UUID,
        data: SubscriptionUpgradeRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminSubscriptionResponse:
        """Upgrade subscription to a higher plan.
        
        Requirements: 4.2 - Apply change immediately with prorated billing
        
        Args:
            subscription_id: Subscription ID
            data: Upgrade request data
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated subscription
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
            ValueError: If upgrade is invalid
        """
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        # Validate upgrade path
        tier_order = [PlanTier.FREE.value, PlanTier.BASIC.value, PlanTier.PRO.value, PlanTier.ENTERPRISE.value]
        current_index = tier_order.index(subscription.plan_tier) if subscription.plan_tier in tier_order else 0
        new_index = tier_order.index(data.new_plan) if data.new_plan in tier_order else 0
        
        if new_index <= current_index:
            raise ValueError(f"Cannot upgrade from {subscription.plan_tier} to {data.new_plan}")
        
        previous_plan = subscription.plan_tier
        
        # Calculate proration if applicable
        proration_amount = await self._calculate_proration(
            subscription, 
            data.new_plan, 
            is_upgrade=True
        )
        
        # Update subscription
        updated = await self.subscription_repo.update_subscription(
            subscription_id,
            plan_tier=data.new_plan,
            status=SubscriptionStatus.ACTIVE.value,
            cancel_at_period_end=False,
            canceled_at=None,
        )
        
        # Log audit
        await self.audit_logger.log_admin_action(
            admin_id=admin_id,
            action="subscription_upgrade",
            resource_type="subscription",
            resource_id=subscription_id,
            details={
                "previous_plan": previous_plan,
                "new_plan": data.new_plan,
                "proration_amount": proration_amount,
                "reason": data.reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return await self.get_subscription(subscription_id)

    async def downgrade_subscription(
        self,
        subscription_id: uuid.UUID,
        data: SubscriptionDowngradeRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminSubscriptionResponse:
        """Downgrade subscription to a lower plan.
        
        Requirements: 4.2 - Apply change immediately with prorated billing
        
        Args:
            subscription_id: Subscription ID
            data: Downgrade request data
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated subscription
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
            ValueError: If downgrade is invalid
        """
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        # Validate downgrade path
        tier_order = [PlanTier.FREE.value, PlanTier.BASIC.value, PlanTier.PRO.value, PlanTier.ENTERPRISE.value]
        current_index = tier_order.index(subscription.plan_tier) if subscription.plan_tier in tier_order else 0
        new_index = tier_order.index(data.new_plan) if data.new_plan in tier_order else 0
        
        if new_index >= current_index:
            raise ValueError(f"Cannot downgrade from {subscription.plan_tier} to {data.new_plan}")
        
        previous_plan = subscription.plan_tier
        
        # Calculate proration credit if applicable
        proration_credit = await self._calculate_proration(
            subscription, 
            data.new_plan, 
            is_upgrade=False
        )
        
        # Update subscription
        updated = await self.subscription_repo.update_subscription(
            subscription_id,
            plan_tier=data.new_plan,
        )
        
        # Log audit
        await self.audit_logger.log_admin_action(
            admin_id=admin_id,
            action="subscription_downgrade",
            resource_type="subscription",
            resource_id=subscription_id,
            details={
                "previous_plan": previous_plan,
                "new_plan": data.new_plan,
                "proration_credit": proration_credit,
                "reason": data.reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return await self.get_subscription(subscription_id)

    async def _calculate_proration(
        self,
        subscription: Subscription,
        new_plan: str,
        is_upgrade: bool,
    ) -> float:
        """Calculate prorated amount for plan change.
        
        Requirements: 4.2 - Prorated billing calculation
        Property 7: (remaining_days / total_days) * price_difference
        
        Args:
            subscription: Current subscription
            new_plan: New plan tier
            is_upgrade: Whether this is an upgrade
            
        Returns:
            Prorated amount (positive for upgrade, negative for downgrade credit)
        """
        # Get plan prices
        current_plan = await self.plan_repo.get_by_slug(subscription.plan_tier)
        new_plan_obj = await self.plan_repo.get_by_slug(new_plan)
        
        if not current_plan or not new_plan_obj:
            return 0.0
        
        # Get prices based on billing cycle
        if subscription.billing_cycle == "yearly":
            current_price = current_plan.price_yearly / 100  # Convert cents to dollars
            new_price = new_plan_obj.price_yearly / 100
        else:
            current_price = current_plan.price_monthly / 100
            new_price = new_plan_obj.price_monthly / 100
        
        # Calculate remaining days
        now = datetime.utcnow()
        total_days = (subscription.current_period_end - subscription.current_period_start).days
        remaining_days = max(0, (subscription.current_period_end - now).days)
        
        if total_days <= 0:
            return 0.0
        
        # Calculate proration: (remaining_days / total_days) * price_difference
        price_difference = new_price - current_price
        proration = (remaining_days / total_days) * price_difference
        
        return round(proration, 2)


    # ==================== Subscription Extension (4.3) ====================

    async def extend_subscription(
        self,
        subscription_id: uuid.UUID,
        data: SubscriptionExtendRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminSubscriptionResponse:
        """Extend subscription by adding days.
        
        Requirements: 4.3 - Add specified days to current period without additional charge
        Property 8: new_end_date = original_end_date + N days
        
        Args:
            subscription_id: Subscription ID
            data: Extension request data
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Updated subscription
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        subscription = await self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        
        original_end_date = subscription.current_period_end
        new_end_date = original_end_date + timedelta(days=data.days)
        
        # Update subscription
        updated = await self.subscription_repo.update_subscription(
            subscription_id,
            current_period_end=new_end_date,
            # Reactivate if expired
            status=SubscriptionStatus.ACTIVE.value if subscription.status == SubscriptionStatus.EXPIRED.value else subscription.status,
            cancel_at_period_end=False,
        )
        
        # Log audit
        await self.audit_logger.log_admin_action(
            admin_id=admin_id,
            action="subscription_extended",
            resource_type="subscription",
            resource_id=subscription_id,
            details={
                "days_added": data.days,
                "original_end_date": original_end_date.isoformat(),
                "new_end_date": new_end_date.isoformat(),
                "reason": data.reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return await self.get_subscription(subscription_id)

    # ==================== Refund Processing (4.4) ====================

    async def process_refund(
        self,
        payment_id: uuid.UUID,
        data: RefundRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefundResponse:
        """Process refund through original payment gateway.
        
        Requirements: 4.4 - Process refund through original payment gateway
        
        Args:
            payment_id: Payment transaction ID
            data: Refund request data
            admin_id: Admin performing the action
            ip_address: Request IP address
            user_agent: Request user agent
            
        Returns:
            Refund result
            
        Raises:
            PaymentNotFoundError: If payment not found
            RefundError: If refund processing fails
        """
        # Get payment transaction
        transaction = await self.transaction_repo.get_transaction(payment_id)
        if not transaction:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        
        # Validate transaction can be refunded
        if transaction.status == PaymentStatus.REFUNDED.value:
            raise RefundError("Payment has already been refunded")
        
        if transaction.status != PaymentStatus.COMPLETED.value:
            raise RefundError(f"Cannot refund payment with status '{transaction.status}'. Only completed payments can be refunded.")
        
        if not transaction.gateway_payment_id:
            raise RefundError("Payment has no gateway payment ID. Cannot process refund.")
        
        # Validate refund amount
        if data.amount is not None:
            if data.amount <= 0:
                raise RefundError("Refund amount must be positive")
            if data.amount > transaction.amount:
                raise RefundError(f"Refund amount ({data.amount}) exceeds payment amount ({transaction.amount})")
        
        # Get gateway configuration
        gateway_config = await self.gateway_repo.get_config_by_provider(
            transaction.gateway_provider
        )
        if not gateway_config:
            raise RefundError(f"Gateway {transaction.gateway_provider} not found")
        
        if not gateway_config.is_enabled:
            raise RefundError(f"Gateway {transaction.gateway_provider} is disabled")
        
        # Create gateway instance and process refund
        gateway = PaymentGatewayFactory.create(gateway_config)
        
        refund_amount = data.amount if data.amount is not None else transaction.amount
        
        try:
            refund_result = await gateway.refund_payment(
                payment_id=transaction.gateway_payment_id,
                amount=refund_amount,
            )
        except Exception as e:
            logger.error(f"Refund processing error: {e}")
            raise RefundError(f"Failed to process refund: {str(e)}")
        
        # Check if refund was successful based on status
        if refund_result.status == "failed":
            raise RefundError(f"Refund failed: {refund_result.error_message}")
        
        # Update transaction status
        await self.transaction_repo.update_transaction(
            payment_id,
            status=PaymentStatus.REFUNDED.value,
        )
        
        # Update subscription status if full refund
        if data.amount is None or data.amount >= transaction.amount:
            if transaction.subscription_id:
                await self.subscription_repo.update_subscription(
                    transaction.subscription_id,
                    status=SubscriptionStatus.CANCELED.value,
                    canceled_at=datetime.utcnow(),
                )
        
        # Log audit
        await self.audit_logger.log_admin_action(
            admin_id=admin_id,
            action="refund_processed",
            resource_type="payment",
            resource_id=payment_id,
            details={
                "refund_id": refund_result.refund_id,
                "amount": refund_amount,
                "currency": transaction.currency,
                "gateway": transaction.gateway_provider,
                "reason": data.reason,
                "is_partial": data.amount is not None and data.amount < transaction.amount,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return RefundResponse(
            refund_id=refund_result.refund_id,
            payment_id=payment_id,
            amount=refund_amount,
            currency=transaction.currency,
            status="completed",
            gateway=transaction.gateway_provider,
            processed_at=datetime.utcnow(),
        )

    # ==================== Revenue Analytics (4.5) ====================

    async def get_revenue_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> RevenueAnalyticsResponse:
        """Get revenue analytics.
        
        Requirements: 4.5 - Display MRR, ARR, revenue by plan, revenue by gateway, refund rate
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Revenue analytics data
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get all completed transactions in period
        transactions = await self._get_transactions_in_period(start_date, end_date)
        
        # Calculate total revenue
        total_revenue = sum(t.amount for t in transactions if t.status == PaymentStatus.COMPLETED.value)
        
        # Calculate refunds
        refunded_transactions = [t for t in transactions if t.status == PaymentStatus.REFUNDED.value]
        total_refunds = sum(t.amount for t in refunded_transactions)
        refund_count = len(refunded_transactions)
        
        # Calculate refund rate
        total_transactions = len([t for t in transactions if t.status in [PaymentStatus.COMPLETED.value, PaymentStatus.REFUNDED.value]])
        refund_rate = (refund_count / total_transactions * 100) if total_transactions > 0 else 0.0
        
        # Calculate MRR (Monthly Recurring Revenue)
        mrr = await self._calculate_mrr()
        
        # Calculate ARR (Annual Recurring Revenue)
        arr = mrr * 12
        
        # Revenue by plan
        revenue_by_plan = await self._calculate_revenue_by_plan(transactions)
        
        # Revenue by gateway
        revenue_by_gateway = await self._calculate_revenue_by_gateway(transactions)
        
        # Calculate growth rate (compare to previous period)
        previous_start = start_date - (end_date - start_date)
        previous_transactions = await self._get_transactions_in_period(previous_start, start_date)
        previous_revenue = sum(t.amount for t in previous_transactions if t.status == PaymentStatus.COMPLETED.value)
        
        growth_rate = 0.0
        if previous_revenue > 0:
            growth_rate = ((total_revenue - previous_revenue) / previous_revenue) * 100
        
        return RevenueAnalyticsResponse(
            mrr=round(mrr, 2),
            arr=round(arr, 2),
            total_revenue=round(total_revenue, 2),
            total_refunds=round(total_refunds, 2),
            refund_rate=round(refund_rate, 2),
            refund_count=refund_count,
            growth_rate=round(growth_rate, 2),
            revenue_by_plan=revenue_by_plan,
            revenue_by_gateway=revenue_by_gateway,
            period_start=start_date,
            period_end=end_date,
        )

    async def _get_transactions_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[PaymentTransaction]:
        """Get transactions within a date range."""
        result = await self.session.execute(
            select(PaymentTransaction).where(
                and_(
                    PaymentTransaction.created_at >= start_date,
                    PaymentTransaction.created_at <= end_date,
                )
            )
        )
        return list(result.scalars().all())

    async def _calculate_mrr(self) -> float:
        """Calculate Monthly Recurring Revenue from active subscriptions."""
        # Get all active subscriptions
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE.value
            )
        )
        subscriptions = result.scalars().all()
        
        mrr = 0.0
        for sub in subscriptions:
            plan = await self.plan_repo.get_by_slug(sub.plan_tier)
            if plan:
                if sub.billing_cycle == "yearly":
                    # Convert yearly to monthly
                    mrr += (plan.price_yearly / 100) / 12
                else:
                    mrr += plan.price_monthly / 100
        
        return mrr

    async def _calculate_revenue_by_plan(
        self,
        transactions: list[PaymentTransaction],
    ) -> list[RevenueByPlan]:
        """Calculate revenue breakdown by plan."""
        plan_revenue = {}
        
        for transaction in transactions:
            if transaction.status != PaymentStatus.COMPLETED.value:
                continue
            
            # Get plan from metadata or subscription
            plan_name = "unknown"
            if transaction.payment_metadata:
                plan_name = transaction.payment_metadata.get("plan_slug", "unknown")
            elif transaction.subscription_id:
                sub = await self.subscription_repo.get_by_id(transaction.subscription_id)
                if sub:
                    plan_name = sub.plan_tier
            
            if plan_name not in plan_revenue:
                plan_revenue[plan_name] = {"amount": 0.0, "count": 0}
            
            plan_revenue[plan_name]["amount"] += transaction.amount
            plan_revenue[plan_name]["count"] += 1
        
        return [
            RevenueByPlan(
                plan=plan,
                revenue=round(data["amount"], 2),
                transaction_count=data["count"],
            )
            for plan, data in plan_revenue.items()
        ]

    async def _calculate_revenue_by_gateway(
        self,
        transactions: list[PaymentTransaction],
    ) -> list[RevenueByGateway]:
        """Calculate revenue breakdown by payment gateway."""
        gateway_revenue = {}
        
        for transaction in transactions:
            if transaction.status != PaymentStatus.COMPLETED.value:
                continue
            
            gateway = transaction.gateway_provider
            if gateway not in gateway_revenue:
                gateway_revenue[gateway] = {"amount": 0.0, "count": 0}
            
            gateway_revenue[gateway]["amount"] += transaction.amount
            gateway_revenue[gateway]["count"] += 1
        
        return [
            RevenueByGateway(
                gateway=gateway,
                revenue=round(data["amount"], 2),
                transaction_count=data["count"],
            )
            for gateway, data in gateway_revenue.items()
        ]
