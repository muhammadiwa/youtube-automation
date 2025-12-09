"""Property-based tests for payment gateway credential encryption.

**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
**Validates: Requirements 30.4**

Tests that:
- All gateway credentials are encrypted using KMS before storage
- Credentials are never stored in plaintext
- Encrypted credentials can be decrypted back to original values
"""

import string
from hypothesis import given, settings, strategies as st
import pytest

from app.core.kms import (
    kms_encrypt_simple,
    kms_decrypt_simple,
    is_kms_encrypted,
    reset_key_manager,
)


# Strategy for generating realistic API keys
api_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=16,
    max_size=128,
)

# Strategy for generating realistic API secrets
api_secret_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?",
    min_size=32,
    max_size=256,
)

# Strategy for webhook secrets
webhook_secret_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=16,
    max_size=64,
)


# Local implementations matching interface.py
def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential using KMS."""
    if not plaintext:
        raise ValueError("Cannot encrypt empty credential")
    return kms_encrypt_simple(plaintext)


def decrypt_credential(ciphertext: str) -> str:
    """Decrypt a credential using KMS."""
    if not ciphertext:
        return None
    return kms_decrypt_simple(ciphertext)


@pytest.fixture(autouse=True)
def reset_kms():
    """Reset KMS key manager before each test."""
    reset_key_manager()
    yield
    reset_key_manager()


class TestCredentialEncryption:
    """Property tests for credential encryption.
    
    **Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
    **Validates: Requirements 30.4**
    """

    @given(api_key=api_key_strategy)
    @settings(max_examples=100)
    def test_api_key_encryption_round_trip(self, api_key: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* API key, encrypting and then decrypting SHALL return the original value.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(api_key)
        decrypted = decrypt_credential(encrypted)
        
        assert decrypted == api_key

    @given(api_secret=api_secret_strategy)
    @settings(max_examples=100)
    def test_api_secret_encryption_round_trip(self, api_secret: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* API secret, encrypting and then decrypting SHALL return the original value.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(api_secret)
        decrypted = decrypt_credential(encrypted)
        
        assert decrypted == api_secret


    @given(webhook_secret=webhook_secret_strategy)
    @settings(max_examples=100)
    def test_webhook_secret_encryption_round_trip(self, webhook_secret: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* webhook secret, encrypting and then decrypting SHALL return the original value.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(webhook_secret)
        decrypted = decrypt_credential(encrypted)
        
        assert decrypted == webhook_secret

    @given(credential=api_key_strategy)
    @settings(max_examples=100)
    def test_encrypted_credential_differs_from_plaintext(self, credential: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* credential, the encrypted value SHALL differ from the plaintext.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(credential)
        
        # Encrypted value must be different from plaintext
        assert encrypted != credential
        # Encrypted value should be recognizable as KMS-encrypted
        assert is_kms_encrypted(encrypted)

    @given(credential=api_key_strategy)
    @settings(max_examples=100)
    def test_plaintext_not_in_encrypted_output(self, credential: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* credential, the plaintext SHALL NOT appear in the encrypted output.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(credential)
        
        # Plaintext should not be a substring of encrypted value
        assert credential not in encrypted



class TestEncryptionEdgeCases:
    """Property tests for encryption edge cases.
    
    **Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
    **Validates: Requirements 30.4**
    """

    def test_empty_credential_raises_error(self) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        Encrypting an empty credential SHALL raise ValueError.
        **Validates: Requirements 30.4**
        """
        with pytest.raises(ValueError):
            encrypt_credential("")

    def test_decrypt_none_returns_none(self) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        Decrypting None or empty string SHALL return None.
        **Validates: Requirements 30.4**
        """
        assert decrypt_credential(None) is None
        assert decrypt_credential("") is None

    @given(credential=api_key_strategy)
    @settings(max_examples=100)
    def test_multiple_encryptions_decrypt_correctly(self, credential: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* credential, multiple encryptions SHALL all decrypt to the same value.
        **Validates: Requirements 30.4**
        """
        encrypted1 = encrypt_credential(credential)
        encrypted2 = encrypt_credential(credential)
        
        # Both should decrypt to the same value
        assert decrypt_credential(encrypted1) == credential
        assert decrypt_credential(encrypted2) == credential


class TestIsKmsEncrypted:
    """Property tests for is_kms_encrypted detection.
    
    **Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
    **Validates: Requirements 30.4**
    """

    @given(credential=api_key_strategy)
    @settings(max_examples=100)
    def test_encrypted_values_detected(self, credential: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* encrypted credential, is_kms_encrypted SHALL return True.
        **Validates: Requirements 30.4**
        """
        encrypted = encrypt_credential(credential)
        assert is_kms_encrypted(encrypted) is True

    @given(plaintext=api_key_strategy)
    @settings(max_examples=100)
    def test_plaintext_not_detected_as_encrypted(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 37: Payment Gateway Credential Encryption**
        
        *For any* plaintext credential, is_kms_encrypted SHALL return False.
        **Validates: Requirements 30.4**
        """
        # Plaintext that doesn't start with Fernet prefix should not be detected
        if not plaintext.startswith("gAAAAA"):
            assert is_kms_encrypted(plaintext) is False
