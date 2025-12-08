"""KMS-like encryption module for sensitive data.

Provides AES-256 encryption for OAuth tokens and other sensitive data.
Uses Fernet symmetric encryption which provides:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Automatic IV generation
"""

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _derive_key(key: str) -> bytes:
    """Derive a Fernet-compatible key from the configuration key.

    Args:
        key: The raw encryption key string

    Returns:
        bytes: A 32-byte URL-safe base64-encoded key for Fernet
    """
    # Use SHA-256 to derive a consistent 32-byte key
    key_bytes = hashlib.sha256(key.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def get_fernet() -> Fernet:
    """Get a Fernet instance with the configured encryption key.

    Returns:
        Fernet: Configured Fernet encryption instance
    """
    key = _derive_key(settings.KMS_ENCRYPTION_KEY)
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token using AES-256 encryption.

    Args:
        plaintext: The plain text token to encrypt

    Returns:
        str: Base64-encoded encrypted token

    Raises:
        ValueError: If plaintext is empty
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty token")

    fernet = get_fernet()
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_token(ciphertext: str) -> Optional[str]:
    """Decrypt an encrypted token.

    Args:
        ciphertext: The encrypted token string

    Returns:
        Optional[str]: Decrypted token or None if decryption fails
    """
    if not ciphertext:
        return None

    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except (InvalidToken, ValueError):
        return None


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be encrypted (Fernet format).

    Args:
        value: The value to check

    Returns:
        bool: True if the value appears to be Fernet-encrypted
    """
    if not value:
        return False

    try:
        # Fernet tokens are base64-encoded and start with 'gAAAAA'
        return value.startswith("gAAAAA") and len(value) > 50
    except Exception:
        return False


def rotate_encryption_key(old_key: str, new_key: str, ciphertext: str) -> str:
    """Re-encrypt data with a new key (for key rotation).

    Args:
        old_key: The current encryption key
        new_key: The new encryption key
        ciphertext: The encrypted data

    Returns:
        str: Data re-encrypted with the new key

    Raises:
        ValueError: If decryption with old key fails
    """
    # Decrypt with old key
    old_fernet = Fernet(_derive_key(old_key))
    try:
        plaintext = old_fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt with old key")

    # Encrypt with new key
    new_fernet = Fernet(_derive_key(new_key))
    return new_fernet.encrypt(plaintext.encode()).decode()
