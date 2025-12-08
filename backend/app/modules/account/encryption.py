"""Encryption utilities for account module.

Provides mixin and helper functions for encrypted token handling.
"""

from typing import Optional

from app.core.encryption import decrypt_token, encrypt_token, is_encrypted


class EncryptedTokenMixin:
    """Mixin class providing encrypted token property helpers.

    This mixin can be used by any model that needs encrypted token storage.
    """

    @staticmethod
    def encrypt_value(value: Optional[str]) -> Optional[str]:
        """Encrypt a value if not None.

        Args:
            value: Plain text value to encrypt

        Returns:
            Optional[str]: Encrypted value or None
        """
        if value is None:
            return None
        return encrypt_token(value)

    @staticmethod
    def decrypt_value(value: Optional[str]) -> Optional[str]:
        """Decrypt a value if not None.

        Args:
            value: Encrypted value to decrypt

        Returns:
            Optional[str]: Decrypted value or None
        """
        if value is None:
            return None
        return decrypt_token(value)

    @staticmethod
    def is_value_encrypted(value: Optional[str]) -> bool:
        """Check if a value is encrypted.

        Args:
            value: Value to check

        Returns:
            bool: True if value is encrypted or None
        """
        if value is None:
            return True
        return is_encrypted(value)
