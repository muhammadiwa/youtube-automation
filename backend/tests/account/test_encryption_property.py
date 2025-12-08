"""Property-based tests for OAuth token encryption.

**Feature: youtube-automation, Property 5: OAuth Token Encryption**
**Validates: Requirements 2.2, 25.1**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume

from app.core.encryption import (
    decrypt_token,
    encrypt_token,
    is_encrypted,
    rotate_encryption_key,
)
from app.modules.account.encryption import EncryptedTokenMixin


# Strategy for generating valid OAuth-like tokens (non-empty strings)
token_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_."
    ),
    min_size=10,
    max_size=500
)


class TestOAuthTokenEncryption:
    """Property tests for OAuth token encryption.

    **Feature: youtube-automation, Property 5: OAuth Token Encryption**
    **Validates: Requirements 2.2, 25.1**
    """

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_encrypted_token_differs_from_plaintext(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any OAuth token, the encrypted value SHALL differ from the plaintext,
        ensuring tokens are never stored in plaintext.
        """
        assume(len(plaintext) > 0)
        encrypted = encrypt_token(plaintext)
        assert encrypted != plaintext, (
            "Encrypted token must differ from plaintext"
        )

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_encryption_round_trip_preserves_token(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any OAuth token, encrypting and then decrypting SHALL return
        the original token value.
        """
        assume(len(plaintext) > 0)
        encrypted = encrypt_token(plaintext)
        decrypted = decrypt_token(encrypted)
        assert decrypted == plaintext, (
            f"Round-trip failed: expected '{plaintext}', got '{decrypted}'"
        )

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_encrypted_token_is_detected_as_encrypted(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any encrypted token, the is_encrypted function SHALL return True.
        """
        assume(len(plaintext) > 0)
        encrypted = encrypt_token(plaintext)
        assert is_encrypted(encrypted), (
            "Encrypted token should be detected as encrypted"
        )

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_plaintext_token_is_not_detected_as_encrypted(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any plaintext token, the is_encrypted function SHALL return False.
        """
        assume(len(plaintext) > 0)
        # Ensure plaintext doesn't accidentally look like Fernet format
        assume(not plaintext.startswith("gAAAAA"))
        assert not is_encrypted(plaintext), (
            "Plaintext token should not be detected as encrypted"
        )

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_encrypted_token_has_fernet_format(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any encrypted token, the output SHALL have Fernet format
        (starts with 'gAAAAA' and has sufficient length).
        """
        assume(len(plaintext) > 0)
        encrypted = encrypt_token(plaintext)
        assert encrypted.startswith("gAAAAA"), (
            "Encrypted token should start with Fernet prefix"
        )
        assert len(encrypted) > 50, (
            "Encrypted token should have sufficient length"
        )

    @given(plaintext1=token_strategy, plaintext2=token_strategy)
    @settings(max_examples=100)
    def test_different_plaintexts_produce_different_ciphertexts(
        self, plaintext1: str, plaintext2: str
    ) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any two different plaintext tokens, their encrypted values
        SHALL be different.
        """
        assume(len(plaintext1) > 0 and len(plaintext2) > 0)
        assume(plaintext1 != plaintext2)
        encrypted1 = encrypt_token(plaintext1)
        encrypted2 = encrypt_token(plaintext2)
        assert encrypted1 != encrypted2, (
            "Different plaintexts should produce different ciphertexts"
        )

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_same_plaintext_produces_different_ciphertexts(
        self, plaintext: str
    ) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any plaintext token encrypted multiple times, each encryption
        SHALL produce a different ciphertext (due to random IV).
        """
        assume(len(plaintext) > 0)
        encrypted1 = encrypt_token(plaintext)
        encrypted2 = encrypt_token(plaintext)
        # Fernet uses random IV, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2, (
            "Same plaintext should produce different ciphertexts due to random IV"
        )


class TestEncryptedTokenMixin:
    """Property tests for EncryptedTokenMixin helper class."""

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_mixin_encrypt_decrypt_round_trip(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        For any token, using the mixin's encrypt and decrypt methods
        SHALL preserve the original value.
        """
        assume(len(plaintext) > 0)
        encrypted = EncryptedTokenMixin.encrypt_value(plaintext)
        decrypted = EncryptedTokenMixin.decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_mixin_handles_none_values(self) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**

        The mixin SHALL handle None values gracefully.
        """
        assert EncryptedTokenMixin.encrypt_value(None) is None
        assert EncryptedTokenMixin.decrypt_value(None) is None
        assert EncryptedTokenMixin.is_value_encrypted(None) is True

    @given(plaintext=token_strategy)
    @settings(max_examples=100)
    def test_mixin_is_value_encrypted_detects_encrypted(self, plaintext: str) -> None:
        """**Feature: youtube-automation, Property 5: OAuth Token Encryption**"""
        assume(len(plaintext) > 0)
        encrypted = EncryptedTokenMixin.encrypt_value(plaintext)
        assert EncryptedTokenMixin.is_value_encrypted(encrypted) is True


class TestInvalidEncryptionInputs:
    """Tests for invalid encryption input handling."""

    def test_empty_string_raises_error(self) -> None:
        """Empty strings SHALL raise ValueError when encrypting."""
        with pytest.raises(ValueError, match="Cannot encrypt empty token"):
            encrypt_token("")

    def test_decrypt_invalid_ciphertext_returns_none(self) -> None:
        """Invalid ciphertext SHALL return None when decrypting."""
        invalid_ciphertexts = [
            "not-encrypted",
            "gAAAAA-invalid",
            "random-string-123",
        ]
        for ciphertext in invalid_ciphertexts:
            assert decrypt_token(ciphertext) is None

    def test_decrypt_empty_string_returns_none(self) -> None:
        """Empty string SHALL return None when decrypting."""
        assert decrypt_token("") is None
