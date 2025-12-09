"""Property-based tests for payment gateway enable/disable.

**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
**Validates: Requirements 30.2, 30.3**

Tests that:
- Gateway enable/disable actions update availability immediately
- Only enabled gateways are displayed to users
- Gateways without credentials cannot be enabled
"""

import uuid
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

from hypothesis import given, settings, strategies as st
import pytest


class GatewayProvider(str, Enum):
    """Supported payment gateway providers."""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MIDTRANS = "midtrans"
    XENDIT = "xendit"


GATEWAY_DEFAULTS = {
    GatewayProvider.STRIPE.value: {
        "display_name": "Stripe",
        "supported_currencies": ["USD", "EUR", "GBP", "IDR"],
        "supported_payment_methods": ["card", "apple_pay"],
    },
    GatewayProvider.PAYPAL.value: {
        "display_name": "PayPal",
        "supported_currencies": ["USD", "EUR", "GBP", "IDR"],
        "supported_payment_methods": ["paypal", "card"],
    },
    GatewayProvider.MIDTRANS.value: {
        "display_name": "Midtrans",
        "supported_currencies": ["IDR"],
        "supported_payment_methods": ["gopay", "ovo", "dana"],
    },
    GatewayProvider.XENDIT.value: {
        "display_name": "Xendit",
        "supported_currencies": ["IDR", "PHP", "VND"],
        "supported_payment_methods": ["ovo", "dana", "gcash"],
    },
}


@dataclass
class MockGatewayConfig:
    """Mock gateway configuration for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider: str = ""
    display_name: str = ""
    is_enabled: bool = False
    is_default: bool = False
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    supported_currencies: list = field(default_factory=list)

    def has_credentials(self) -> bool:
        return bool(self.api_key_encrypted and self.api_secret_encrypted)

    def supports_currency(self, currency: str) -> bool:
        return currency.upper() in [c.upper() for c in self.supported_currencies]


gateway_provider_strategy = st.sampled_from([
    GatewayProvider.STRIPE.value,
    GatewayProvider.PAYPAL.value,
    GatewayProvider.MIDTRANS.value,
    GatewayProvider.XENDIT.value,
])

gateway_providers_list_strategy = st.lists(
    gateway_provider_strategy,
    min_size=1,
    max_size=4,
    unique=True,
)


def create_mock_gateway_config(
    provider: str,
    is_enabled: bool = False,
    has_credentials: bool = True,
    is_default: bool = False,
) -> MockGatewayConfig:
    defaults = GATEWAY_DEFAULTS.get(provider, {})
    return MockGatewayConfig(
        id=uuid.uuid4(),
        provider=provider,
        display_name=defaults.get("display_name", provider),
        is_enabled=is_enabled,
        is_default=is_default,
        api_key_encrypted="encrypted_key" if has_credentials else None,
        api_secret_encrypted="encrypted_secret" if has_credentials else None,
        supported_currencies=defaults.get("supported_currencies", []),
    )


class GatewayStateManager:
    """In-memory gateway state manager for testing enable/disable logic."""
    
    def __init__(self):
        self.gateways: dict[str, MockGatewayConfig] = {}
    
    def add_gateway(self, config: MockGatewayConfig) -> None:
        self.gateways[config.provider] = config
    
    def get_enabled_gateways(self) -> list[MockGatewayConfig]:
        return [g for g in self.gateways.values() if g.is_enabled]
    
    def enable_gateway(self, provider: str) -> Optional[MockGatewayConfig]:
        config = self.gateways.get(provider)
        if not config:
            return None
        if not config.has_credentials():
            raise ValueError(f"Cannot enable gateway {provider}: no credentials")
        config.is_enabled = True
        return config
    
    def disable_gateway(self, provider: str) -> Optional[MockGatewayConfig]:
        config = self.gateways.get(provider)
        if not config:
            return None
        config.is_enabled = False
        config.is_default = False
        return config
    
    def get_enabled_gateways_for_currency(self, currency: str) -> list[MockGatewayConfig]:
        return [g for g in self.gateways.values() if g.is_enabled and g.supports_currency(currency)]


class TestGatewayEnableDisable:
    """Property tests for gateway enable/disable functionality.
    
    **Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
    **Validates: Requirements 30.2, 30.3**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_enable_gateway_with_credentials(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* gateway with credentials, enabling SHALL set is_enabled to True immediately.
        **Validates: Requirements 30.2**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=False, has_credentials=True)
        manager.add_gateway(config)
        
        result = manager.enable_gateway(provider)
        
        assert result is not None
        assert result.is_enabled is True
        enabled = manager.get_enabled_gateways()
        assert any(g.provider == provider for g in enabled)

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_disable_gateway(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* enabled gateway, disabling SHALL set is_enabled to False immediately.
        **Validates: Requirements 30.2**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=True, has_credentials=True)
        manager.add_gateway(config)
        
        result = manager.disable_gateway(provider)
        
        assert result is not None
        assert result.is_enabled is False
        enabled = manager.get_enabled_gateways()
        assert not any(g.provider == provider for g in enabled)

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_cannot_enable_gateway_without_credentials(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* gateway without credentials, enabling SHALL raise an error.
        **Validates: Requirements 30.2**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=False, has_credentials=False)
        manager.add_gateway(config)
        
        with pytest.raises(ValueError) as exc_info:
            manager.enable_gateway(provider)
        
        assert "credentials" in str(exc_info.value).lower()
        assert config.is_enabled is False


    @given(providers=gateway_providers_list_strategy)
    @settings(max_examples=100)
    def test_only_enabled_gateways_returned(self, providers: list) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* set of gateways, get_enabled_gateways SHALL return only enabled ones.
        **Validates: Requirements 30.3**
        """
        manager = GatewayStateManager()
        expected_enabled = []
        for i, provider in enumerate(providers):
            is_enabled = (i % 2 == 0)
            config = create_mock_gateway_config(provider=provider, is_enabled=is_enabled, has_credentials=True)
            manager.add_gateway(config)
            if is_enabled:
                expected_enabled.append(provider)
        
        enabled = manager.get_enabled_gateways()
        enabled_providers = [g.provider for g in enabled]
        
        assert set(enabled_providers) == set(expected_enabled)
        for gateway in enabled:
            assert gateway.is_enabled is True

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_enable_disable_toggle(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* gateway, toggling enable/disable SHALL update state immediately.
        **Validates: Requirements 30.2**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=False, has_credentials=True)
        manager.add_gateway(config)
        
        assert config.is_enabled is False
        assert len(manager.get_enabled_gateways()) == 0
        
        manager.enable_gateway(provider)
        assert config.is_enabled is True
        assert len(manager.get_enabled_gateways()) == 1
        
        manager.disable_gateway(provider)
        assert config.is_enabled is False
        assert len(manager.get_enabled_gateways()) == 0

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_disable_clears_default_flag(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* default gateway, disabling SHALL also clear the is_default flag.
        **Validates: Requirements 30.2**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=True, has_credentials=True, is_default=True)
        manager.add_gateway(config)
        
        assert config.is_default is True
        manager.disable_gateway(provider)
        assert config.is_enabled is False
        assert config.is_default is False



class TestEnabledGatewaysForCurrency:
    """Property tests for currency-filtered enabled gateways.
    
    **Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
    **Validates: Requirements 30.3**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_enabled_gateway_returned_for_supported_currency(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* enabled gateway, it SHALL be returned for currencies it supports.
        **Validates: Requirements 30.3**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=True, has_credentials=True)
        manager.add_gateway(config)
        
        if config.supported_currencies:
            currency = config.supported_currencies[0]
            enabled = manager.get_enabled_gateways_for_currency(currency)
            assert any(g.provider == provider for g in enabled)

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_disabled_gateway_not_returned_for_currency(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* disabled gateway, it SHALL NOT be returned even for supported currencies.
        **Validates: Requirements 30.3**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=False, has_credentials=True)
        manager.add_gateway(config)
        
        if config.supported_currencies:
            currency = config.supported_currencies[0]
            enabled = manager.get_enabled_gateways_for_currency(currency)
            assert not any(g.provider == provider for g in enabled)

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_enabled_gateway_not_returned_for_unsupported_currency(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
        
        *For any* enabled gateway, it SHALL NOT be returned for unsupported currencies.
        **Validates: Requirements 30.3**
        """
        manager = GatewayStateManager()
        config = create_mock_gateway_config(provider=provider, is_enabled=True, has_credentials=True)
        manager.add_gateway(config)
        
        unsupported_currency = "XYZ"
        if unsupported_currency not in config.supported_currencies:
            enabled = manager.get_enabled_gateways_for_currency(unsupported_currency)
            assert not any(g.provider == provider for g in enabled)



class TestHasCredentials:
    """Property tests for has_credentials method.
    
    **Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
    **Validates: Requirements 30.2**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_has_credentials_true_when_both_set(self, provider: str) -> None:
        """*For any* gateway with api_key and api_secret, has_credentials SHALL return True."""
        config = create_mock_gateway_config(provider=provider, has_credentials=True)
        assert config.has_credentials() is True

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_has_credentials_false_when_missing(self, provider: str) -> None:
        """*For any* gateway without api_key or api_secret, has_credentials SHALL return False."""
        config = create_mock_gateway_config(provider=provider, has_credentials=False)
        assert config.has_credentials() is False


class TestSupportsCurrency:
    """Property tests for supports_currency method.
    
    **Feature: youtube-automation, Property 36: Payment Gateway Enable/Disable**
    **Validates: Requirements 30.3**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_supports_currency_case_insensitive(self, provider: str) -> None:
        """*For any* gateway, supports_currency SHALL be case-insensitive."""
        config = create_mock_gateway_config(provider=provider, has_credentials=True)
        if config.supported_currencies:
            currency = config.supported_currencies[0]
            assert config.supports_currency(currency.upper()) is True
            assert config.supports_currency(currency.lower()) is True
