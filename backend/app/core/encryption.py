"""KMS-like encryption module for sensitive data.

Provides AES-256 encryption for OAuth tokens and other sensitive data.
Uses Fernet symmetric encryption which provides:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Automatic IV generation

This module now delegates to the KMS module for enhanced key management
with automatic key rotation support.

Requirements: 25.1 - OAuth tokens encrypted using KMS with automatic key rotation
"""

import base64
import hashlib
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
    # Use KMS key manager for enhanced key management
    from app.core.kms import get_key_manager
    return get_key_manager().get_fernet()


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token using AES-256 encryption via KMS.

    Args:
        plaintext: The plain text token to encrypt

    Returns:
        str: Base64-encoded encrypted token

    Raises:
        ValueError: If plaintext is empty
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty token")

    # Use KMS for encryption with key versioning support
    from app.core.kms import kms_encrypt_simple
    return kms_encrypt_simple(plaintext)


def decrypt_token(ciphertext: str) -> Optional[str]:
    """Decrypt an encrypted token via KMS.

    Args:
        ciphertext: The encrypted token string

    Returns:
        Optional[str]: Decrypted token or None if decryption fails
    """
    if not ciphertext:
        return None

    # Use KMS for decryption with multi-key support
    from app.core.kms import kms_decrypt_simple
    return kms_decrypt_simple(ciphertext)


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be encrypted (Fernet format).

    Args:
        value: The value to check

    Returns:
        bool: True if the value appears to be Fernet-encrypted
    """
    from app.core.kms import is_kms_encrypted
    return is_kms_encrypted(value)


def rotate_encryption_key(old_key: str, new_key: str, ciphertext: str) -> str:
    """Re-encrypt data with a new key (for key rotation).

    This function is maintained for backward compatibility.
    For new code, use kms_rotate_and_reencrypt from the kms module.

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


# Re-export KMS functions for convenience
def get_key_rotation_status() -> dict:
    """Get the current key rotation status.
    
    Returns:
        dict: Key rotation status information
    """
    from app.core.kms import get_key_rotation_status as _get_status
    return _get_status()


def rotate_kms_key(new_master_key: Optional[str] = None) -> None:
    """Rotate the KMS encryption key.
    
    Args:
        new_master_key: Optional new master key (uses existing if not provided)
    """
    from app.core.kms import get_key_manager
    get_key_manager().rotate_key(new_master_key)
