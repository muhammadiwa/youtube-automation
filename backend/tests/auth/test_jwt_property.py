"""Property-based tests for JWT authentication.

**Feature: youtube-automation, Property 1: Authentication Token Validity**
**Validates: Requirements 1.1**
"""

import uuid
from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings, strategies as st

from app.modules.auth.jwt import (
    TokenBlacklist,
    blacklist_token,
    create_access_token,
    create_auth_tokens,
    create_refresh_token,
    decode_token,
    validate_token,
)

# Strategy for generating valid UUIDs
uuid_strategy = st.uuids()


class TestJWTTokenValidity:
    """Property tests for JWT token validity."""

    @pytest.fixture(autouse=True)
    def clear_blacklist(self):
        """Clear token blacklist before each test."""
        TokenBlacklist.clear()
        yield
        TokenBlacklist.clear()

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_access_token_contains_correct_user_id(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**

        For any valid user ID, creating an access token SHALL produce a token
        that can be decoded and contains the correct user ID.
        """
        token, _ = create_access_token(user_id)
        payload = decode_token(token)

        assert payload is not None, "Token should be decodable"
        assert payload.sub == str(user_id), (
            f"Token user ID {payload.sub} does not match expected {user_id}"
        )


    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_access_token_has_correct_type(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_access_token(user_id)
        payload = decode_token(token)
        assert payload is not None, "Token should be decodable"
        assert payload.type == "access"

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_refresh_token_has_correct_type(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload is not None, "Token should be decodable"
        assert payload.type == "refresh"

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_token_has_valid_expiration(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_access_token(user_id)
        payload = decode_token(token)
        assert payload is not None
        assert payload.exp > datetime.utcnow()

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_token_has_issued_at_timestamp(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        before = datetime.utcnow()
        token, _ = create_access_token(user_id)
        after = datetime.utcnow()
        payload = decode_token(token)
        assert payload is not None
        assert payload.iat >= before - timedelta(seconds=1)
        assert payload.iat <= after + timedelta(seconds=1)

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_token_has_unique_jti(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token1, jti1 = create_access_token(user_id)
        token2, jti2 = create_access_token(user_id)
        assert jti1 != jti2, "Each token should have a unique JTI"

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_valid_access_token_validates_successfully(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_access_token(user_id)
        payload = validate_token(token, "access")
        assert payload is not None
        assert payload.sub == str(user_id)

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_valid_refresh_token_validates_successfully(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_refresh_token(user_id)
        payload = validate_token(token, "refresh")
        assert payload is not None
        assert payload.sub == str(user_id)

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_access_token_fails_refresh_validation(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_access_token(user_id)
        payload = validate_token(token, "refresh")
        assert payload is None

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_refresh_token_fails_access_validation(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_refresh_token(user_id)
        payload = validate_token(token, "access")
        assert payload is None

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_blacklisted_token_fails_validation(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        token, _ = create_access_token(user_id)
        assert validate_token(token, "access") is not None
        blacklist_token(token)
        assert validate_token(token, "access") is None

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_auth_tokens_contains_both_token_types(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        tokens = create_auth_tokens(user_id)
        access_payload = validate_token(tokens.access_token, "access")
        refresh_payload = validate_token(tokens.refresh_token, "refresh")
        assert access_payload is not None
        assert refresh_payload is not None

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_auth_tokens_has_correct_expiry_info(self, user_id: uuid.UUID) -> None:
        """**Feature: youtube-automation, Property 1: Authentication Token Validity**"""
        tokens = create_auth_tokens(user_id)
        assert tokens.expires_in > 0
        assert tokens.token_type == "bearer"


class TestInvalidTokens:
    """Tests for invalid token handling."""

    def test_invalid_token_string_fails_decode(self) -> None:
        """Invalid token strings SHALL fail to decode."""
        invalid_tokens = ["", "not-a-token", "a.b.c"]
        for token in invalid_tokens:
            assert decode_token(token) is None

    def test_tampered_token_fails_validation(self) -> None:
        """Tampered tokens SHALL fail validation."""
        user_id = uuid.uuid4()
        token, _ = create_access_token(user_id)
        tampered = token[:-5] + "XXXXX"
        assert validate_token(tampered, "access") is None
