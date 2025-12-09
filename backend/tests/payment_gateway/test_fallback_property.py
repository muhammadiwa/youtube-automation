"""Property-based tests for payment gateway fallback logic.

**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
**Validates: Requirements 30.5**

Tests that:
- Failed payments can be retried with alternative gateways
- Payment details are preserved during fallback
- Fallback respects gateway availability and currency support
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
import pytest


class GatewayProvider(str, Enum):
    """Supported payment gateway providers."""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MIDTRANS = "midtrans"
    XENDIT = "xendit"


class PaymentStatus(str, Enum):
    """Payment status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


GATEWAY_CURRENCIES = {
    GatewayProvider.STRIPE.value: ["USD", "EUR", "GBP", "IDR"],
    GatewayProvider.PAYPAL.value: ["USD", "EUR", "GBP", "IDR"],
    GatewayProvider.MIDTRANS.value: ["IDR"],
    GatewayProvider.XENDIT.value: ["IDR", "PHP", "VND"],
}

MAX_TOTAL_ATTEMPTS = 3


@dataclass
class MockGatewayConfig:
    """Mock gateway configuration for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider: str = ""
    is_enabled: bool = True
    supported_currencies: list = field(default_factory=list)

    def supports_currency(self, currency: str) -> bool:
        return currency.upper() in [c.upper() for c in self.supported_currencies]


@dataclass
class MockTransaction:
    """Mock payment transaction for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    gateway_provider: str = ""
    amount: float = 0.0
    currency: str = "USD"
    description: str = ""
    status: str = PaymentStatus.PENDING.value
    attempt_count: int = 1
    previous_gateway: Optional[str] = None
    error_message: Optional[str] = None

    def can_retry(self) -> bool:
        return self.status in [PaymentStatus.FAILED.value, PaymentStatus.CANCELLED.value]


class MockFallbackService:
    """Mock fallback service for testing fallback logic."""
    
    def __init__(self, gateways: list[MockGatewayConfig]):
        self.gateways = {g.provider: g for g in gateways}
        self.transactions: dict[uuid.UUID, MockTransaction] = {}
    
    def add_transaction(self, tx: MockTransaction) -> None:
        self.transactions[tx.id] = tx
    
    def get_fallback_gateways(
        self,
        transaction: MockTransaction,
        exclude_providers: Optional[list[str]] = None,
    ) -> list[MockGatewayConfig]:
        """Get available fallback gateways."""
        exclude = set(exclude_providers or [])
        exclude.add(transaction.gateway_provider)
        if transaction.previous_gateway:
            exclude.add(transaction.previous_gateway)
        
        return [
            g for g in self.gateways.values()
            if g.provider not in exclude
            and g.is_enabled
            and g.supports_currency(transaction.currency)
        ]
    
    def can_retry(self, transaction: MockTransaction) -> bool:
        """Check if transaction can be retried."""
        if not transaction.can_retry():
            return False
        if transaction.attempt_count >= MAX_TOTAL_ATTEMPTS:
            return False
        return True
    
    def execute_fallback(
        self,
        transaction_id: uuid.UUID,
        fallback_provider: str,
    ) -> Optional[MockTransaction]:
        """Execute fallback to alternative gateway."""
        tx = self.transactions.get(transaction_id)
        if not tx:
            return None
        
        if not self.can_retry(tx):
            return None
        
        config = self.gateways.get(fallback_provider)
        if not config or not config.is_enabled:
            return None
        
        if not config.supports_currency(tx.currency):
            return None
        
        # Record previous gateway and increment attempt
        tx.previous_gateway = tx.gateway_provider
        tx.attempt_count += 1
        tx.gateway_provider = fallback_provider
        tx.status = PaymentStatus.PENDING.value
        tx.error_message = None
        
        return tx


# Strategies
gateway_provider_strategy = st.sampled_from([
    GatewayProvider.STRIPE.value,
    GatewayProvider.PAYPAL.value,
    GatewayProvider.MIDTRANS.value,
    GatewayProvider.XENDIT.value,
])

currency_strategy = st.sampled_from(["USD", "EUR", "IDR", "PHP", "VND"])

amount_strategy = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False)


def create_gateway_config(provider: str, is_enabled: bool = True) -> MockGatewayConfig:
    """Create a mock gateway config."""
    return MockGatewayConfig(
        provider=provider,
        is_enabled=is_enabled,
        supported_currencies=GATEWAY_CURRENCIES.get(provider, []),
    )


def create_failed_transaction(
    provider: str,
    currency: str,
    amount: float,
    attempt_count: int = 1,
) -> MockTransaction:
    """Create a failed transaction for testing."""
    return MockTransaction(
        gateway_provider=provider,
        amount=amount,
        currency=currency,
        description="Test payment",
        status=PaymentStatus.FAILED.value,
        attempt_count=attempt_count,
    )


class TestPaymentFallback:
    """Property tests for payment fallback logic.
    
    **Feature: youtube-automation, Property 38: Payment Gateway Fallback**
    **Validates: Requirements 30.5**
    """

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_preserves_payment_details(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* failed payment, fallback SHALL preserve amount, currency, and description.
        **Validates: Requirements 30.5**
        """
        # Create all gateways
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        # Create failed transaction
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        # Get fallback gateways
        fallbacks = service.get_fallback_gateways(tx)
        
        # If there's a fallback available, execute it
        if fallbacks:
            fallback_provider = fallbacks[0].provider
            result = service.execute_fallback(tx.id, fallback_provider)
            
            assert result is not None
            # Payment details preserved
            assert result.amount == amount
            assert result.currency == currency
            assert result.description == "Test payment"


    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_excludes_failed_gateway(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* failed payment, fallback gateways SHALL NOT include the failed gateway.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        # Original provider should not be in fallbacks
        fallback_providers = [g.provider for g in fallbacks]
        assert original_provider not in fallback_providers

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_only_returns_currency_compatible_gateways(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* failed payment, fallback gateways SHALL support the payment currency.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        # All fallbacks must support the currency
        for gateway in fallbacks:
            assert gateway.supports_currency(currency)


    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_only_returns_enabled_gateways(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* failed payment, fallback gateways SHALL only include enabled gateways.
        **Validates: Requirements 30.5**
        """
        # Create mix of enabled and disabled gateways
        gateways = []
        for i, p in enumerate(GatewayProvider):
            gateways.append(create_gateway_config(p.value, is_enabled=(i % 2 == 0)))
        
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        # All fallbacks must be enabled
        for gateway in fallbacks:
            assert gateway.is_enabled is True

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_changes_gateway_provider(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* successful fallback, the gateway provider SHALL change to the alternative.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        if fallbacks:
            fallback_provider = fallbacks[0].provider
            result = service.execute_fallback(tx.id, fallback_provider)
            
            assert result is not None
            assert result.gateway_provider == fallback_provider
            assert result.gateway_provider != original_provider


    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_increments_attempt_count(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* fallback execution, attempt count SHALL be incremented.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount, attempt_count=1)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        if fallbacks:
            original_attempts = tx.attempt_count
            result = service.execute_fallback(tx.id, fallbacks[0].provider)
            
            assert result is not None
            assert result.attempt_count == original_attempts + 1

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_fallback_records_previous_gateway(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* fallback execution, the previous gateway SHALL be recorded.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(original_provider, currency, amount)
        service.add_transaction(tx)
        
        fallbacks = service.get_fallback_gateways(tx)
        
        if fallbacks:
            result = service.execute_fallback(tx.id, fallbacks[0].provider)
            
            assert result is not None
            assert result.previous_gateway == original_provider



class TestFallbackRetryLimits:
    """Property tests for fallback retry limits.
    
    **Feature: youtube-automation, Property 38: Payment Gateway Fallback**
    **Validates: Requirements 30.5**
    """

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_cannot_retry_after_max_attempts(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* transaction at max attempts, can_retry SHALL return False.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        # Create transaction at max attempts
        tx = create_failed_transaction(
            original_provider, currency, amount, 
            attempt_count=MAX_TOTAL_ATTEMPTS
        )
        service.add_transaction(tx)
        
        assert service.can_retry(tx) is False

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
        attempt_count=st.integers(min_value=1, max_value=MAX_TOTAL_ATTEMPTS - 1),
    )
    @settings(max_examples=100)
    def test_can_retry_before_max_attempts(
        self,
        original_provider: str,
        currency: str,
        amount: float,
        attempt_count: int,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* failed transaction below max attempts, can_retry SHALL return True.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = create_failed_transaction(
            original_provider, currency, amount, 
            attempt_count=attempt_count
        )
        service.add_transaction(tx)
        
        assert service.can_retry(tx) is True

    @given(
        original_provider=gateway_provider_strategy,
        currency=currency_strategy,
        amount=amount_strategy,
    )
    @settings(max_examples=100)
    def test_cannot_retry_completed_transaction(
        self,
        original_provider: str,
        currency: str,
        amount: float,
    ) -> None:
        """**Feature: youtube-automation, Property 38: Payment Gateway Fallback**
        
        *For any* completed transaction, can_retry SHALL return False.
        **Validates: Requirements 30.5**
        """
        gateways = [create_gateway_config(p.value) for p in GatewayProvider]
        service = MockFallbackService(gateways)
        
        tx = MockTransaction(
            gateway_provider=original_provider,
            amount=amount,
            currency=currency,
            status=PaymentStatus.COMPLETED.value,
        )
        service.add_transaction(tx)
        
        assert service.can_retry(tx) is False
