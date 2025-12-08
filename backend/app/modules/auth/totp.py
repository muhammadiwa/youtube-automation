"""TOTP (Time-based One-Time Password) functionality for 2FA."""

import json
import secrets
import string

import pyotp


def generate_totp_secret() -> str:
    """Generate a new TOTP secret key.

    Returns:
        str: Base32 encoded secret key
    """
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "YouTube Automation") -> str:
    """Generate TOTP provisioning URI for QR code.

    Args:
        secret: TOTP secret key
        email: User email for identification
        issuer: Application name

    Returns:
        str: otpauth:// URI for QR code generation
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code.

    Args:
        secret: TOTP secret key
        code: 6-digit TOTP code to verify

    Returns:
        bool: True if code is valid
    """
    totp = pyotp.TOTP(secret)
    # valid_window=1 allows for 30 seconds clock drift
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate backup codes for 2FA recovery.

    Args:
        count: Number of backup codes to generate

    Returns:
        list[str]: List of backup codes
    """
    codes = []
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(count):
        # Generate 8-character backup code
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        codes.append(code)
    return codes


def encode_backup_codes(codes: list[str]) -> str:
    """Encode backup codes for storage.

    Args:
        codes: List of backup codes

    Returns:
        str: JSON encoded string
    """
    return json.dumps(codes)


def decode_backup_codes(encoded: str) -> list[str]:
    """Decode backup codes from storage.

    Args:
        encoded: JSON encoded string

    Returns:
        list[str]: List of backup codes
    """
    return json.loads(encoded)


def verify_backup_code(encoded_codes: str, code: str) -> tuple[bool, str | None]:
    """Verify and consume a backup code.

    Args:
        encoded_codes: JSON encoded backup codes
        code: Backup code to verify

    Returns:
        tuple[bool, str | None]: (is_valid, updated_encoded_codes)
            - If valid, returns (True, updated_codes_without_used_code)
            - If invalid, returns (False, None)
    """
    codes = decode_backup_codes(encoded_codes)
    code_upper = code.upper().replace("-", "").replace(" ", "")

    if code_upper in codes:
        codes.remove(code_upper)
        return True, encode_backup_codes(codes)

    return False, None


class TwoFactorSetup:
    """Data class for 2FA setup response."""

    def __init__(self, secret: str, uri: str, backup_codes: list[str]):
        self.secret = secret
        self.uri = uri
        self.backup_codes = backup_codes
