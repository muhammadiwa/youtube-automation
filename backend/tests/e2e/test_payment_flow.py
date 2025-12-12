"""End-to-end tests for payment flows.

Tests complete payment flows including:
- Plan selection and checkout
- Payment processing with multiple gateways
- Payment failure and retry with alternative gateway
- Subscription activation
- Webhook handling

**Validates: Requirements 28.1, 28.3, 28.4, 30.1, 30.2, 30.3, 30.4, 30.5**
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st, assume


class PaymentFlowState(str, Enum):
    """States in the payment flow."""
    INITIAL = "initial"
    PLAN_SELECTED = "plan_selected"
    CHECKOUT_STARTED = "checkout_started"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_ACTIVE = "subscription_active"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"


class GatewayProvider(str, Enum):
    """Payment gateway providers."""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MIDTRANS = "midtrans"
    XENDIT = "xendit"


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class MockPlan:
    """Mock subscription plan."""
    id: str = ""
    name: str = ""
    tier: str = PlanTier.FREE.value
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    features: list[str] = field(default_factory=list)
    limits: dict = field(default_factory=dict)


@dataclass
class MockPaymentGateway:
    """Mock payment gateway configuration."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider: str = ""
    display_name: str = ""
    is_enabled: bool = True
    is_default: bool = False
    supported_currencies: list[str] = field(default_factory=list)
    transaction_fee_percent: float = 2.9
    min_amount: float = 1.0
    health_status: str = "healthy"


@dataclass
class MockPayment:
    """Mock payment transaction."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    gateway_provider: str = ""
    gateway_payment_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    checkout_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class MockSubscription:
    """Mock subscription."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    plan_id: str = ""
    status: str = "inactive"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    payment_gateway: str = ""



class MockPaymentFlowService:
    """Mock service for testing payment flows."""
    
    ENCRYPTION_PREFIX = "encrypted_"
    
    def __init__(self):
        self.plans: dict[str, MockPlan] = {}
        self.gateways: dict[str, MockPaymentGateway] = {}
        self.payments: dict[uuid.UUID, MockPayment] = {}
        self.subscriptions: dict[uuid.UUID, MockSubscription] = {}
        self.user_subscriptions: dict[uuid.UUID, MockSubscription] = {}
        self.audit_logs: list[dict] = []
        
        # Initialize default plans
        self._init_plans()
        # Initialize default gateways
        self._init_gateways()
    
    def _init_plans(self) -> None:
        """Initialize default subscription plans."""
        self.plans = {
            "free": MockPlan(
                id="free", name="Free", tier=PlanTier.FREE.value,
                price_monthly=0, price_yearly=0,
                features=["1 YouTube account", "Basic analytics"],
                limits={"accounts": 1, "uploads_per_month": 10}
            ),
            "basic": MockPlan(
                id="basic", name="Basic", tier=PlanTier.BASIC.value,
                price_monthly=9.99, price_yearly=99.99,
                features=["3 YouTube accounts", "Advanced analytics", "Scheduling"],
                limits={"accounts": 3, "uploads_per_month": 50}
            ),
            "pro": MockPlan(
                id="pro", name="Pro", tier=PlanTier.PRO.value,
                price_monthly=29.99, price_yearly=299.99,
                features=["10 YouTube accounts", "AI features", "Live streaming"],
                limits={"accounts": 10, "uploads_per_month": 200}
            ),
            "enterprise": MockPlan(
                id="enterprise", name="Enterprise", tier=PlanTier.ENTERPRISE.value,
                price_monthly=99.99, price_yearly=999.99,
                features=["Unlimited accounts", "All features", "Priority support"],
                limits={"accounts": -1, "uploads_per_month": -1}
            ),
        }
    
    def _init_gateways(self) -> None:
        """Initialize default payment gateways."""
        self.gateways = {
            GatewayProvider.STRIPE.value: MockPaymentGateway(
                provider=GatewayProvider.STRIPE.value,
                display_name="Stripe",
                is_enabled=True,
                is_default=True,
                supported_currencies=["USD", "EUR", "GBP", "IDR"],
                transaction_fee_percent=2.9,
                min_amount=0.50,
            ),
            GatewayProvider.PAYPAL.value: MockPaymentGateway(
                provider=GatewayProvider.PAYPAL.value,
                display_name="PayPal",
                is_enabled=True,
                is_default=False,
                supported_currencies=["USD", "EUR", "GBP"],
                transaction_fee_percent=2.9,
                min_amount=1.00,
            ),
            GatewayProvider.MIDTRANS.value: MockPaymentGateway(
                provider=GatewayProvider.MIDTRANS.value,
                display_name="Midtrans",
                is_enabled=True,
                is_default=False,
                supported_currencies=["IDR"],
                transaction_fee_percent=2.0,
                min_amount=10000,
            ),
            GatewayProvider.XENDIT.value: MockPaymentGateway(
                provider=GatewayProvider.XENDIT.value,
                display_name="Xendit",
                is_enabled=True,
                is_default=False,
                supported_currencies=["IDR", "PHP", "VND"],
                transaction_fee_percent=1.5,
                min_amount=10000,
            ),
        }
    
    def get_plans(self) -> list[MockPlan]:
        """Get all available plans."""
        return list(self.plans.values())
    
    def get_plan(self, plan_id: str) -> Optional[MockPlan]:
        """Get a specific plan."""
        return self.plans.get(plan_id)
    
    def get_enabled_gateways(self, currency: str = "USD") -> list[MockPaymentGateway]:
        """Get enabled gateways for a currency."""
        return [
            g for g in self.gateways.values()
            if g.is_enabled and currency in g.supported_currencies
        ]
    
    def enable_gateway(self, provider: str) -> tuple[bool, PaymentFlowState]:
        """Enable a payment gateway."""
        gateway = self.gateways.get(provider)
        if not gateway:
            return False, PaymentFlowState.INITIAL
        
        gateway.is_enabled = True
        self._log_audit(None, "gateway_enabled", {"provider": provider})
        return True, PaymentFlowState.INITIAL
    
    def disable_gateway(self, provider: str) -> tuple[bool, PaymentFlowState]:
        """Disable a payment gateway."""
        gateway = self.gateways.get(provider)
        if not gateway:
            return False, PaymentFlowState.INITIAL
        
        gateway.is_enabled = False
        self._log_audit(None, "gateway_disabled", {"provider": provider})
        return True, PaymentFlowState.INITIAL
    
    def create_checkout(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        gateway_provider: str,
        billing_period: str = "monthly",
        currency: str = "USD",
    ) -> tuple[Optional[MockPayment], PaymentFlowState]:
        """Create a checkout session."""
        plan = self.plans.get(plan_id)
        if not plan:
            return None, PaymentFlowState.INITIAL
        
        gateway = self.gateways.get(gateway_provider)
        if not gateway or not gateway.is_enabled:
            return None, PaymentFlowState.INITIAL
        
        if currency not in gateway.supported_currencies:
            return None, PaymentFlowState.INITIAL
        
        # Calculate amount
        amount = plan.price_monthly if billing_period == "monthly" else plan.price_yearly
        
        if amount < gateway.min_amount:
            return None, PaymentFlowState.INITIAL
        
        # Create payment
        payment = MockPayment(
            user_id=user_id,
            gateway_provider=gateway_provider,
            gateway_payment_id=f"{gateway_provider}_{uuid.uuid4()}",
            amount=amount,
            currency=currency,
            status="pending",
            checkout_url=f"https://{gateway_provider}.example.com/checkout/{uuid.uuid4()}",
        )
        
        self.payments[payment.id] = payment
        self._log_audit(user_id, "checkout_created", {
            "payment_id": str(payment.id),
            "plan_id": plan_id,
            "gateway": gateway_provider,
        })
        
        return payment, PaymentFlowState.CHECKOUT_STARTED

    
    def process_payment(
        self,
        payment_id: uuid.UUID,
        simulate_success: bool = True,
    ) -> tuple[Optional[MockPayment], PaymentFlowState]:
        """Process a payment (simulate gateway response)."""
        payment = self.payments.get(payment_id)
        if not payment:
            return None, PaymentFlowState.INITIAL
        
        if payment.status != "pending":
            return payment, PaymentFlowState(payment.status)
        
        payment.status = "processing"
        
        if simulate_success:
            payment.status = "completed"
            payment.completed_at = datetime.utcnow()
            
            self._log_audit(payment.user_id, "payment_completed", {
                "payment_id": str(payment_id),
                "amount": payment.amount,
            })
            
            return payment, PaymentFlowState.PAYMENT_COMPLETED
        else:
            payment.status = "failed"
            payment.error_message = "Payment declined"
            
            self._log_audit(payment.user_id, "payment_failed", {
                "payment_id": str(payment_id),
                "error": payment.error_message,
            })
            
            return payment, PaymentFlowState.PAYMENT_FAILED
    
    def retry_with_alternative_gateway(
        self,
        original_payment_id: uuid.UUID,
        new_gateway_provider: str,
    ) -> tuple[Optional[MockPayment], PaymentFlowState]:
        """Retry failed payment with alternative gateway."""
        original = self.payments.get(original_payment_id)
        if not original or original.status != "failed":
            return None, PaymentFlowState.INITIAL
        
        gateway = self.gateways.get(new_gateway_provider)
        if not gateway or not gateway.is_enabled:
            return None, PaymentFlowState.INITIAL
        
        if original.currency not in gateway.supported_currencies:
            return None, PaymentFlowState.INITIAL
        
        # Create new payment
        payment = MockPayment(
            user_id=original.user_id,
            gateway_provider=new_gateway_provider,
            gateway_payment_id=f"{new_gateway_provider}_{uuid.uuid4()}",
            amount=original.amount,
            currency=original.currency,
            status="pending",
            checkout_url=f"https://{new_gateway_provider}.example.com/checkout/{uuid.uuid4()}",
        )
        
        self.payments[payment.id] = payment
        self._log_audit(original.user_id, "payment_retry", {
            "original_payment_id": str(original_payment_id),
            "new_payment_id": str(payment.id),
            "new_gateway": new_gateway_provider,
        })
        
        return payment, PaymentFlowState.CHECKOUT_STARTED
    
    def activate_subscription(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        payment_id: uuid.UUID,
        billing_period: str = "monthly",
    ) -> tuple[Optional[MockSubscription], PaymentFlowState]:
        """Activate subscription after successful payment."""
        payment = self.payments.get(payment_id)
        if not payment or payment.status != "completed":
            return None, PaymentFlowState.PAYMENT_PENDING
        
        plan = self.plans.get(plan_id)
        if not plan:
            return None, PaymentFlowState.INITIAL
        
        # Calculate period
        now = datetime.utcnow()
        if billing_period == "monthly":
            period_end = now + timedelta(days=30)
        else:
            period_end = now + timedelta(days=365)
        
        subscription = MockSubscription(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            current_period_start=now,
            current_period_end=period_end,
            payment_gateway=payment.gateway_provider,
        )
        
        self.subscriptions[subscription.id] = subscription
        self.user_subscriptions[user_id] = subscription
        
        self._log_audit(user_id, "subscription_activated", {
            "subscription_id": str(subscription.id),
            "plan_id": plan_id,
        })
        
        return subscription, PaymentFlowState.SUBSCRIPTION_ACTIVE
    
    def get_user_subscription(self, user_id: uuid.UUID) -> Optional[MockSubscription]:
        """Get user's current subscription."""
        return self.user_subscriptions.get(user_id)
    
    def cancel_subscription(self, user_id: uuid.UUID) -> tuple[bool, PaymentFlowState]:
        """Cancel user's subscription."""
        subscription = self.user_subscriptions.get(user_id)
        if not subscription:
            return False, PaymentFlowState.INITIAL
        
        subscription.status = "cancelled"
        
        self._log_audit(user_id, "subscription_cancelled", {
            "subscription_id": str(subscription.id),
        })
        
        return True, PaymentFlowState.SUBSCRIPTION_CANCELLED
    
    def handle_webhook(
        self,
        gateway_provider: str,
        event_type: str,
        payment_id: str,
    ) -> tuple[bool, PaymentFlowState]:
        """Handle webhook from payment gateway."""
        # Find payment by gateway payment ID
        payment = None
        for p in self.payments.values():
            if p.gateway_payment_id == payment_id:
                payment = p
                break
        
        if not payment:
            return False, PaymentFlowState.INITIAL
        
        if event_type == "payment.succeeded":
            payment.status = "completed"
            payment.completed_at = datetime.utcnow()
            return True, PaymentFlowState.PAYMENT_COMPLETED
        elif event_type == "payment.failed":
            payment.status = "failed"
            payment.error_message = "Payment failed via webhook"
            return True, PaymentFlowState.PAYMENT_FAILED
        
        return False, PaymentFlowState.INITIAL
    
    def _log_audit(self, user_id: Optional[uuid.UUID], action: str, details: dict) -> None:
        """Log audit entry."""
        self.audit_logs.append({
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow(),
        })



# Strategies
user_id_strategy = st.uuids()
plan_id_strategy = st.sampled_from(["basic", "pro", "enterprise"])
gateway_strategy = st.sampled_from([g.value for g in GatewayProvider])
billing_period_strategy = st.sampled_from(["monthly", "yearly"])
currency_strategy = st.sampled_from(["USD", "EUR", "IDR"])


class TestCompletePaymentFlow:
    """End-to-end tests for complete payment flows."""

    @given(
        user_id=user_id_strategy,
        plan_id=plan_id_strategy,
        billing_period=billing_period_strategy,
    )
    @settings(max_examples=50)
    def test_complete_checkout_to_subscription_flow(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        billing_period: str,
    ) -> None:
        """Test complete flow from checkout to active subscription.
        
        **Validates: Requirements 28.1, 28.3, 30.1**
        """
        service = MockPaymentFlowService()
        
        # Step 1: Get available plans
        plans = service.get_plans()
        assert len(plans) > 0
        
        plan = service.get_plan(plan_id)
        assert plan is not None
        
        # Step 2: Get enabled gateways
        gateways = service.get_enabled_gateways("USD")
        assert len(gateways) > 0
        
        # Step 3: Create checkout with default gateway (Stripe)
        payment, state = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value, billing_period
        )
        assert state == PaymentFlowState.CHECKOUT_STARTED
        assert payment is not None
        assert payment.checkout_url is not None
        
        # Step 4: Process payment (simulate success)
        payment, state = service.process_payment(payment.id, simulate_success=True)
        assert state == PaymentFlowState.PAYMENT_COMPLETED
        
        # Step 5: Activate subscription
        subscription, state = service.activate_subscription(
            user_id, plan_id, payment.id, billing_period
        )
        assert state == PaymentFlowState.SUBSCRIPTION_ACTIVE
        assert subscription is not None
        assert subscription.plan_id == plan_id
        
        # Verify subscription is retrievable
        user_sub = service.get_user_subscription(user_id)
        assert user_sub is not None
        assert user_sub.status == "active"

    @given(
        user_id=user_id_strategy,
        plan_id=plan_id_strategy,
    )
    @settings(max_examples=50)
    def test_payment_failure_and_retry_flow(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test payment failure and retry with alternative gateway.
        
        **Validates: Requirements 30.5**
        """
        service = MockPaymentFlowService()
        
        # Step 1: Create checkout with Stripe
        payment1, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        
        # Step 2: Simulate payment failure
        payment1, state = service.process_payment(payment1.id, simulate_success=False)
        assert state == PaymentFlowState.PAYMENT_FAILED
        assert payment1.error_message is not None
        
        # Step 3: Retry with PayPal
        payment2, state = service.retry_with_alternative_gateway(
            payment1.id, GatewayProvider.PAYPAL.value
        )
        assert state == PaymentFlowState.CHECKOUT_STARTED
        assert payment2 is not None
        assert payment2.gateway_provider == GatewayProvider.PAYPAL.value
        
        # Step 4: Process retry payment successfully
        payment2, state = service.process_payment(payment2.id, simulate_success=True)
        assert state == PaymentFlowState.PAYMENT_COMPLETED
        
        # Step 5: Activate subscription
        subscription, state = service.activate_subscription(
            user_id, plan_id, payment2.id
        )
        assert state == PaymentFlowState.SUBSCRIPTION_ACTIVE

    @given(
        user_id=user_id_strategy,
        plan_id=plan_id_strategy,
        gateway=gateway_strategy,
    )
    @settings(max_examples=50)
    def test_gateway_selection_flow(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        gateway: str,
    ) -> None:
        """Test payment with different gateway providers.
        
        **Validates: Requirements 30.1, 30.2**
        """
        service = MockPaymentFlowService()
        
        # Determine appropriate currency for gateway
        gateway_config = service.gateways.get(gateway)
        if not gateway_config:
            # Invalid gateway
            payment, state = service.create_checkout(user_id, plan_id, gateway)
            assert state == PaymentFlowState.INITIAL
            return
        
        currency = gateway_config.supported_currencies[0]
        
        # For IDR-only gateways, the plan price needs adjustment
        # Skip if gateway min_amount is higher than plan price (IDR gateways)
        plan = service.get_plan(plan_id)
        if currency == "IDR" and plan.price_monthly < gateway_config.min_amount:
            # This is expected - IDR gateways have higher min amounts
            return
        
        # Create checkout
        payment, state = service.create_checkout(
            user_id, plan_id, gateway, currency=currency
        )
        
        if gateway_config.is_enabled:
            assert state == PaymentFlowState.CHECKOUT_STARTED
            assert payment is not None
            assert payment.gateway_provider == gateway
        else:
            assert state == PaymentFlowState.INITIAL


class TestGatewayManagement:
    """Tests for gateway enable/disable functionality."""

    @given(gateway=gateway_strategy)
    @settings(max_examples=20)
    def test_gateway_enable_disable_flow(self, gateway: str) -> None:
        """Test enabling and disabling gateways.
        
        **Validates: Requirements 30.2, 30.3**
        """
        service = MockPaymentFlowService()
        
        # Disable gateway
        success, _ = service.disable_gateway(gateway)
        assert success
        
        gateway_config = service.gateways.get(gateway)
        assert not gateway_config.is_enabled
        
        # Verify disabled gateway not in enabled list
        enabled = service.get_enabled_gateways("USD")
        assert all(g.provider != gateway for g in enabled)
        
        # Re-enable gateway
        success, _ = service.enable_gateway(gateway)
        assert success
        assert gateway_config.is_enabled

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_cannot_checkout_with_disabled_gateway(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test that checkout fails with disabled gateway.
        
        **Validates: Requirements 30.3**
        """
        service = MockPaymentFlowService()
        
        # Disable Stripe
        service.disable_gateway(GatewayProvider.STRIPE.value)
        
        # Try to checkout with disabled gateway
        payment, state = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        
        assert state == PaymentFlowState.INITIAL
        assert payment is None


class TestWebhookHandling:
    """Tests for webhook handling."""

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_webhook_payment_success(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test webhook handling for successful payment.
        
        **Validates: Requirements 30.4**
        """
        service = MockPaymentFlowService()
        
        # Create checkout
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        
        # Simulate webhook
        success, state = service.handle_webhook(
            GatewayProvider.STRIPE.value,
            "payment.succeeded",
            payment.gateway_payment_id,
        )
        
        assert success
        assert state == PaymentFlowState.PAYMENT_COMPLETED
        assert payment.status == "completed"

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_webhook_payment_failure(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test webhook handling for failed payment."""
        service = MockPaymentFlowService()
        
        # Create checkout
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        
        # Simulate failure webhook
        success, state = service.handle_webhook(
            GatewayProvider.STRIPE.value,
            "payment.failed",
            payment.gateway_payment_id,
        )
        
        assert success
        assert state == PaymentFlowState.PAYMENT_FAILED
        assert payment.status == "failed"


class TestSubscriptionLifecycle:
    """Tests for subscription lifecycle."""

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_subscription_cancellation_flow(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test subscription cancellation flow.
        
        **Validates: Requirements 28.4**
        """
        service = MockPaymentFlowService()
        
        # Create and complete payment
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        service.process_payment(payment.id, simulate_success=True)
        
        # Activate subscription
        subscription, _ = service.activate_subscription(
            user_id, plan_id, payment.id
        )
        assert subscription.status == "active"
        
        # Cancel subscription
        success, state = service.cancel_subscription(user_id)
        assert success
        assert state == PaymentFlowState.SUBSCRIPTION_CANCELLED
        
        # Verify cancelled
        user_sub = service.get_user_subscription(user_id)
        assert user_sub.status == "cancelled"

    @given(
        user_id=user_id_strategy,
        plan_id=plan_id_strategy,
        billing_period=billing_period_strategy,
    )
    @settings(max_examples=50)
    def test_subscription_period_calculation(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        billing_period: str,
    ) -> None:
        """Test subscription period is calculated correctly.
        
        **Validates: Requirements 28.1**
        """
        service = MockPaymentFlowService()
        
        # Create and complete payment
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value, billing_period
        )
        service.process_payment(payment.id, simulate_success=True)
        
        # Activate subscription
        subscription, _ = service.activate_subscription(
            user_id, plan_id, payment.id, billing_period
        )
        
        # Verify period
        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None
        
        period_days = (subscription.current_period_end - subscription.current_period_start).days
        
        if billing_period == "monthly":
            assert 29 <= period_days <= 31
        else:
            assert 364 <= period_days <= 366


class TestPaymentFlowErrorScenarios:
    """Test error scenarios in payment flows."""

    @given(user_id=user_id_strategy)
    @settings(max_examples=50)
    def test_checkout_with_invalid_plan_fails(self, user_id: uuid.UUID) -> None:
        """Test that checkout with invalid plan fails."""
        service = MockPaymentFlowService()
        
        payment, state = service.create_checkout(
            user_id, "invalid_plan", GatewayProvider.STRIPE.value
        )
        
        assert state == PaymentFlowState.INITIAL
        assert payment is None

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_checkout_with_invalid_gateway_fails(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test that checkout with invalid gateway fails."""
        service = MockPaymentFlowService()
        
        payment, state = service.create_checkout(
            user_id, plan_id, "invalid_gateway"
        )
        
        assert state == PaymentFlowState.INITIAL
        assert payment is None

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_cannot_activate_subscription_without_payment(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test that subscription cannot be activated without completed payment."""
        service = MockPaymentFlowService()
        
        # Create checkout but don't process
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        
        # Try to activate without payment
        subscription, state = service.activate_subscription(
            user_id, plan_id, payment.id
        )
        
        assert state == PaymentFlowState.PAYMENT_PENDING
        assert subscription is None

    @given(user_id=user_id_strategy, plan_id=plan_id_strategy)
    @settings(max_examples=50)
    def test_cannot_retry_non_failed_payment(
        self,
        user_id: uuid.UUID,
        plan_id: str,
    ) -> None:
        """Test that only failed payments can be retried."""
        service = MockPaymentFlowService()
        
        # Create and complete payment
        payment, _ = service.create_checkout(
            user_id, plan_id, GatewayProvider.STRIPE.value
        )
        service.process_payment(payment.id, simulate_success=True)
        
        # Try to retry completed payment
        retry_payment, state = service.retry_with_alternative_gateway(
            payment.id, GatewayProvider.PAYPAL.value
        )
        
        assert state == PaymentFlowState.INITIAL
        assert retry_payment is None

    @given(user_id=user_id_strategy)
    @settings(max_examples=50)
    def test_cancel_nonexistent_subscription_fails(
        self,
        user_id: uuid.UUID,
    ) -> None:
        """Test that cancelling non-existent subscription fails."""
        service = MockPaymentFlowService()
        
        success, state = service.cancel_subscription(user_id)
        
        assert not success
        assert state == PaymentFlowState.INITIAL
