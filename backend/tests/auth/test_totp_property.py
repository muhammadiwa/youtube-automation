"""Property-based tests for 2FA (TOTP) functionality.

**Feature: youtube-automation, Property 2: 2FA Enforcement**
**Validates: Requirements 1.2**
"""

import pyotp
from hypothesis import given, settings, strategies as st

from app.modules.auth.totp import (
    decode_backup_codes,
    encode_backup_codes,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_uri,
    verify_backup_code,
    verify_totp_code,
)


class Test2FAEnforcement:
    """Property tests for 2FA enforcement."""

    @given(st.emails())
    @settings(max_examples=100)
    def test_totp_secret_is_valid_base32(self, email: str) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        secret = generate_totp_secret()
        assert secret.isalnum()
        assert len(secret) >= 16
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert len(code) == 6
        assert code.isdigit()

    @given(st.emails())
    @settings(max_examples=100)
    def test_valid_totp_code_is_accepted(self, email: str) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        assert verify_totp_code(secret, valid_code)

    @given(
        invalid_code=st.text(
            alphabet=st.characters(whitelist_categories=("Nd",)),
            min_size=6,
            max_size=6,
        ).filter(lambda x: len(x) == 6 and x.isdigit())
    )
    @settings(max_examples=100)
    def test_invalid_totp_code_is_rejected(self, invalid_code: str) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        if invalid_code == valid_code:
            return
        assert not verify_totp_code(secret, invalid_code)


    @given(st.emails())
    @settings(max_examples=100)
    def test_totp_uri_contains_required_parts(self, email: str) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, email)
        assert uri.startswith("otpauth://totp/")
        assert secret in uri


class TestBackupCodes:
    """Property tests for backup codes."""

    @given(count=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_backup_codes_count_matches_request(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        assert len(codes) == count
        assert len(set(codes)) == count

    @given(count=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_backup_codes_format(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        for code in codes:
            assert len(code) == 8
            assert code.isalnum()

    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_backup_codes_roundtrip(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        original_codes = generate_backup_codes(count)
        encoded = encode_backup_codes(original_codes)
        decoded = decode_backup_codes(encoded)
        assert decoded == original_codes

    @given(count=st.integers(min_value=2, max_value=10))
    @settings(max_examples=100)
    def test_valid_backup_code_is_consumed(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        encoded = encode_backup_codes(codes)
        code_to_use = codes[0]
        is_valid, updated_encoded = verify_backup_code(encoded, code_to_use)
        assert is_valid
        assert updated_encoded is not None
        remaining_codes = decode_backup_codes(updated_encoded)
        assert len(remaining_codes) == count - 1
        assert code_to_use not in remaining_codes

    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_invalid_backup_code_is_rejected(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        encoded = encode_backup_codes(codes)
        invalid_code = "XXXXXXXX"
        if invalid_code in codes:
            return
        is_valid, updated_encoded = verify_backup_code(encoded, invalid_code)
        assert not is_valid
        assert updated_encoded is None

    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_backup_code_case_insensitive(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        encoded = encode_backup_codes(codes)
        code_to_use = codes[0]
        is_valid, _ = verify_backup_code(encoded, code_to_use.lower())
        assert is_valid

    @given(count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_backup_code_used_twice_fails(self, count: int) -> None:
        """**Feature: youtube-automation, Property 2: 2FA Enforcement**"""
        codes = generate_backup_codes(count)
        encoded = encode_backup_codes(codes)
        code_to_use = codes[0]
        is_valid, updated_encoded = verify_backup_code(encoded, code_to_use)
        assert is_valid
        is_valid_again, _ = verify_backup_code(updated_encoded, code_to_use)
        assert not is_valid_again
