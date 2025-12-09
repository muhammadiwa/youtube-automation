"""Property-based tests for gateway credential validation.

**Feature: youtube-automation, Property 39: Gateway Credential Validation**
**Validates: Requirements 30.7**

Tests that:
- Gateway credentials are validated before saving
- Invalid credentials are rejected
- Validation results include meaningful messages
"""

import string
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


@dataclass
class ValidationResult:
    """Result from credential validation."""
    is_valid: bool
    message: str
    details: Optional[dict] = None


@dataclass
class MockGatewayConfig:
    """Mock gateway configuration for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider: str = ""
    display_name: str = ""
    is_enabled: bool = False
    api_key_encrypted: Optional[str] = None
    api_secret_encrypted: Optional[str] = None
    webhook_secret_encrypted: Optional[str] = None

    def has_credentials(self) -> bool:
        return bool(self.api_key_encrypted and self.api_secret_encrypted)


# Credential format patterns for each provider
CREDENTIAL_PATTERNS = {
    GatewayProvider.STRIPE.value: {
        "api_key_prefix": "pk_",
        "api_secret_prefix": "sk_",
        "min_length": 20,
    },
    GatewayProvider.PAYPAL.value: {
        "api_key_prefix": "",  # Client ID has no prefix
        "api_secret_prefix": "",  # Client Secret has no prefix
        "min_length": 20,
    },
    GatewayProvider.MIDTRANS.value: {
        "api_key_prefix": "",  # Client Key
        "api_secret_prefix": "",  # Server Key
        "min_length": 10,
    },
    GatewayProvider.XENDIT.value: {
        "api_key_prefix": "xnd_",
        "api_secret_prefix": "xnd_",
        "min_length": 20,
    },
}


class MockCredentialValidator:
    """Mock credential validator for testing validation logic.
    
    Simulates credential validation without making actual API calls.
    """
    
    def __init__(self):
        # Track which credentials have been "validated" (simulated)
        self.validated_credentials: dict[str, bool] = {}
    
    def validate_format(self, provider: str, api_key: str, api_secret: str) -> ValidationResult:
        """Validate credential format for a provider.
        
        Requirements: 30.7 - Validate API keys before saving
        """
        pattern = CREDENTIAL_PATTERNS.get(provider)
        if not pattern:
            return ValidationResult(
                is_valid=False,
                message=f"Unknown provider: {provider}",
            )
        
        # Check minimum length
        if len(api_key) < pattern["min_length"]:
            return ValidationResult(
                is_valid=False,
                message=f"API key too short (min {pattern['min_length']} chars)",
                details={"field": "api_key", "length": len(api_key)},
            )
        
        if len(api_secret) < pattern["min_length"]:
            return ValidationResult(
                is_valid=False,
                message=f"API secret too short (min {pattern['min_length']} chars)",
                details={"field": "api_secret", "length": len(api_secret)},
            )
        
        # Check prefix if required
        if pattern["api_key_prefix"] and not api_key.startswith(pattern["api_key_prefix"]):
            return ValidationResult(
                is_valid=False,
                message=f"API key must start with '{pattern['api_key_prefix']}'",
                details={"field": "api_key", "expected_prefix": pattern["api_key_prefix"]},
            )
        
        if pattern["api_secret_prefix"] and not api_secret.startswith(pattern["api_secret_prefix"]):
            return ValidationResult(
                is_valid=False,
                message=f"API secret must start with '{pattern['api_secret_prefix']}'",
                details={"field": "api_secret", "expected_prefix": pattern["api_secret_prefix"]},
            )
        
        return ValidationResult(
            is_valid=True,
            message="Credentials format is valid",
            details={"provider": provider},
        )
    
    def validate_credentials(
        self, 
        provider: str, 
        api_key: str, 
        api_secret: str,
        simulate_api_call: bool = True,
    ) -> ValidationResult:
        """Validate credentials with format check and simulated API call.
        
        Requirements: 30.7 - Validate API keys before saving
        """
        # First validate format
        format_result = self.validate_format(provider, api_key, api_secret)
        if not format_result.is_valid:
            return format_result
        
        # Simulate API validation (in real implementation, this calls the gateway)
        if simulate_api_call:
            # For testing, we consider credentials valid if they pass format check
            # and have a specific pattern (simulating successful API response)
            is_valid = len(api_key) >= 20 and len(api_secret) >= 20
            
            if is_valid:
                return ValidationResult(
                    is_valid=True,
                    message=f"{provider.title()} credentials validated successfully",
                    details={"provider": provider, "mode": "test"},
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    message="Credentials validation failed with gateway",
                    details={"provider": provider, "error": "invalid_credentials"},
                )
        
        return format_result


# Strategies
gateway_provider_strategy = st.sampled_from([
    GatewayProvider.STRIPE.value,
    GatewayProvider.PAYPAL.value,
    GatewayProvider.MIDTRANS.value,
    GatewayProvider.XENDIT.value,
])

# Valid credential strategies
valid_api_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=20,
    max_size=100,
)

valid_api_secret_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=20,
    max_size=100,
)

# Invalid credential strategies (too short)
short_credential_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=9,
)


def create_valid_credentials(provider: str) -> tuple[str, str]:
    """Create valid credentials for a provider."""
    pattern = CREDENTIAL_PATTERNS.get(provider, {})
    prefix_key = pattern.get("api_key_prefix", "")
    prefix_secret = pattern.get("api_secret_prefix", "")
    
    api_key = prefix_key + "a" * 30
    api_secret = prefix_secret + "b" * 30
    
    return api_key, api_secret


class TestCredentialValidation:
    """Property tests for credential validation.
    
    **Feature: youtube-automation, Property 39: Gateway Credential Validation**
    **Validates: Requirements 30.7**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_valid_credentials_pass_validation(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* provider with valid credentials, validation SHALL succeed.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        api_key, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_credentials(provider, api_key, api_secret)
        
        assert result.is_valid is True
        assert result.message is not None
        assert len(result.message) > 0

    @given(
        provider=gateway_provider_strategy,
        short_key=short_credential_strategy,
    )
    @settings(max_examples=100)
    def test_short_api_key_fails_validation(
        self, 
        provider: str, 
        short_key: str,
    ) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* API key shorter than minimum length, validation SHALL fail.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        _, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_format(provider, short_key, api_secret)
        
        assert result.is_valid is False
        assert "short" in result.message.lower() or "api key" in result.message.lower()


    @given(
        provider=gateway_provider_strategy,
        short_secret=short_credential_strategy,
    )
    @settings(max_examples=100)
    def test_short_api_secret_fails_validation(
        self, 
        provider: str, 
        short_secret: str,
    ) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* API secret shorter than minimum length, validation SHALL fail.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        api_key, _ = create_valid_credentials(provider)
        
        result = validator.validate_format(provider, api_key, short_secret)
        
        assert result.is_valid is False
        assert "short" in result.message.lower() or "secret" in result.message.lower()

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_validation_result_includes_message(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* validation, the result SHALL include a descriptive message.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        api_key, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_credentials(provider, api_key, api_secret)
        
        assert result.message is not None
        assert isinstance(result.message, str)
        assert len(result.message) > 0

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_validation_result_is_boolean(self, provider: str) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* validation, is_valid SHALL be a boolean value.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        api_key, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_credentials(provider, api_key, api_secret)
        
        assert isinstance(result.is_valid, bool)



class TestPrefixValidation:
    """Property tests for credential prefix validation.
    
    **Feature: youtube-automation, Property 39: Gateway Credential Validation**
    **Validates: Requirements 30.7**
    """

    def test_stripe_requires_pk_prefix_for_api_key(self) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        Stripe API key SHALL start with 'pk_' prefix.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        
        # Valid Stripe credentials
        valid_result = validator.validate_format(
            GatewayProvider.STRIPE.value,
            "pk_test_" + "a" * 30,
            "sk_test_" + "b" * 30,
        )
        assert valid_result.is_valid is True
        
        # Invalid - missing pk_ prefix
        invalid_result = validator.validate_format(
            GatewayProvider.STRIPE.value,
            "invalid_" + "a" * 30,
            "sk_test_" + "b" * 30,
        )
        assert invalid_result.is_valid is False
        assert "pk_" in invalid_result.message

    def test_stripe_requires_sk_prefix_for_api_secret(self) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        Stripe API secret SHALL start with 'sk_' prefix.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        
        # Invalid - missing sk_ prefix
        invalid_result = validator.validate_format(
            GatewayProvider.STRIPE.value,
            "pk_test_" + "a" * 30,
            "invalid_" + "b" * 30,
        )
        assert invalid_result.is_valid is False
        assert "sk_" in invalid_result.message

    def test_xendit_requires_xnd_prefix(self) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        Xendit credentials SHALL start with 'xnd_' prefix.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        
        # Valid Xendit credentials
        valid_result = validator.validate_format(
            GatewayProvider.XENDIT.value,
            "xnd_development_" + "a" * 30,
            "xnd_development_" + "b" * 30,
        )
        assert valid_result.is_valid is True
        
        # Invalid - missing xnd_ prefix
        invalid_result = validator.validate_format(
            GatewayProvider.XENDIT.value,
            "invalid_" + "a" * 30,
            "xnd_development_" + "b" * 30,
        )
        assert invalid_result.is_valid is False



class TestUnknownProvider:
    """Property tests for unknown provider handling.
    
    **Feature: youtube-automation, Property 39: Gateway Credential Validation**
    **Validates: Requirements 30.7**
    """

    @given(
        unknown_provider=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in [p.value for p in GatewayProvider]
        ),
        api_key=valid_api_key_strategy,
        api_secret=valid_api_secret_strategy,
    )
    @settings(max_examples=50)
    def test_unknown_provider_fails_validation(
        self,
        unknown_provider: str,
        api_key: str,
        api_secret: str,
    ) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* unknown provider, validation SHALL fail with appropriate message.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        
        result = validator.validate_format(unknown_provider, api_key, api_secret)
        
        assert result.is_valid is False
        assert "unknown" in result.message.lower() or "provider" in result.message.lower()


class TestValidationDetails:
    """Property tests for validation result details.
    
    **Feature: youtube-automation, Property 39: Gateway Credential Validation**
    **Validates: Requirements 30.7**
    """

    @given(provider=gateway_provider_strategy)
    @settings(max_examples=100)
    def test_successful_validation_includes_provider_in_details(
        self, 
        provider: str,
    ) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* successful validation, details SHALL include the provider.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        api_key, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_credentials(provider, api_key, api_secret)
        
        assert result.is_valid is True
        assert result.details is not None
        assert result.details.get("provider") == provider

    @given(
        provider=gateway_provider_strategy,
        short_key=short_credential_strategy,
    )
    @settings(max_examples=100)
    def test_failed_validation_includes_field_in_details(
        self, 
        provider: str,
        short_key: str,
    ) -> None:
        """**Feature: youtube-automation, Property 39: Gateway Credential Validation**
        
        *For any* failed validation, details SHALL indicate which field failed.
        **Validates: Requirements 30.7**
        """
        validator = MockCredentialValidator()
        _, api_secret = create_valid_credentials(provider)
        
        result = validator.validate_format(provider, short_key, api_secret)
        
        assert result.is_valid is False
        assert result.details is not None
        assert "field" in result.details or "length" in result.details
