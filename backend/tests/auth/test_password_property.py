"""Property-based tests for password policy enforcement.

**Feature: youtube-automation, Property 4: Password Policy Enforcement**
**Validates: Requirements 1.4**
"""

from hypothesis import given, settings, strategies as st

from app.modules.auth.models import (
    hash_password,
    validate_password_policy,
    verify_password,
)

valid_password_strategy = st.from_regex(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,20}$",
    fullmatch=True,
)
short_password_strategy = st.text(min_size=1, max_size=7)
no_uppercase_strategy = st.from_regex(r"^[a-z\d!@#$%^&*(),.?\":{}|<>]{8,20}$", fullmatch=True)
no_lowercase_strategy = st.from_regex(r"^[A-Z\d!@#$%^&*(),.?\":{}|<>]{8,20}$", fullmatch=True)
no_digit_strategy = st.from_regex(r"^[A-Za-z!@#$%^&*(),.?\":{}|<>]{8,20}$", fullmatch=True)
no_special_strategy = st.from_regex(r"^[A-Za-z\d]{8,20}$", fullmatch=True)


class TestPasswordPolicyEnforcement:
    """Property tests for password policy enforcement."""

    @given(password=valid_password_strategy)
    @settings(max_examples=100)
    def test_valid_password_passes_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert len(violations) == 0

    @given(password=short_password_strategy)
    @settings(max_examples=100)
    def test_short_password_fails_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert any("8 characters" in v for v in violations)

    @given(password=no_uppercase_strategy)
    @settings(max_examples=100)
    def test_no_uppercase_fails_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert any("uppercase" in v.lower() for v in violations)


    @given(password=no_lowercase_strategy)
    @settings(max_examples=100)
    def test_no_lowercase_fails_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert any("lowercase" in v.lower() for v in violations)

    @given(password=no_digit_strategy)
    @settings(max_examples=100)
    def test_no_digit_fails_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert any("digit" in v.lower() for v in violations)

    @given(password=no_special_strategy)
    @settings(max_examples=100)
    def test_no_special_char_fails_validation(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy(password)
        assert any("special" in v.lower() for v in violations)

    @given(password=valid_password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_password_hashing_produces_different_hash(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        hashed = hash_password(password)
        assert hashed != password

    @given(password=valid_password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_password_verification_succeeds_for_correct_password(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    @given(password=valid_password_strategy, wrong_password=valid_password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_password_verification_fails_for_wrong_password(self, password: str, wrong_password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        if password == wrong_password:
            return
        hashed = hash_password(password)
        assert not verify_password(wrong_password, hashed)

    @given(password=valid_password_strategy)
    @settings(max_examples=100, deadline=None)
    def test_same_password_produces_different_hashes(self, password: str) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_empty_password_fails_validation(self) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        violations = validate_password_policy("")
        assert len(violations) >= 1
        assert any("8 characters" in v for v in violations)

    def test_violations_are_specific(self) -> None:
        """**Feature: youtube-automation, Property 4: Password Policy Enforcement**"""
        password = "abcdefgh"
        violations = validate_password_policy(password)
        assert len(violations) == 3
