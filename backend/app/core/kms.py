"""KMS (Key Management Service) module for secure encryption with key rotation.

Provides enterprise-grade encryption for OAuth tokens and sensitive data with:
- AES-256 encryption using Fernet
- Automatic key rotation support
- Key versioning for seamless rotation
- Secure key derivation using PBKDF2

Requirements: 25.1 - OAuth tokens encrypted using KMS with automatic key rotation
"""

import base64
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


@dataclass
class KeyVersion:
    """Represents a versioned encryption key."""
    version: int
    key: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class KMSKeyManager:
    """Manages encryption keys with versioning and rotation support.
    
    Supports multiple active keys for seamless rotation:
    - New data is encrypted with the latest key
    - Old data can be decrypted with any valid key version
    - Keys can be rotated without downtime
    """
    
    _instance: Optional["KMSKeyManager"] = None
    _keys: dict[int, KeyVersion] = {}
    _current_version: int = 1
    _rotation_interval_days: int = 90  # Default rotation interval
    
    def __new__(cls) -> "KMSKeyManager":
        """Singleton pattern for key manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the key manager with the primary key."""
        self._keys = {}
        self._current_version = 1
        
        # Derive the primary key from configuration
        primary_key = self._derive_key(settings.KMS_ENCRYPTION_KEY, version=1)
        self._keys[1] = KeyVersion(
            version=1,
            key=primary_key,
            created_at=datetime.utcnow(),
            is_active=True
        )
    
    def _derive_key(self, master_key: str, version: int = 1, salt: Optional[bytes] = None) -> bytes:
        """Derive a Fernet-compatible key using PBKDF2.
        
        Args:
            master_key: The master encryption key
            version: Key version for derivation
            salt: Optional salt (generated if not provided)
            
        Returns:
            bytes: A 32-byte URL-safe base64-encoded key for Fernet
        """
        if salt is None:
            # Use a deterministic salt based on version for reproducibility
            salt = hashlib.sha256(f"kms-salt-v{version}".encode()).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key_bytes = kdf.derive(master_key.encode())
        return base64.urlsafe_b64encode(key_bytes)
    
    def get_current_key(self) -> KeyVersion:
        """Get the current active encryption key.
        
        Returns:
            KeyVersion: The current active key
        """
        return self._keys[self._current_version]
    
    def get_key(self, version: int) -> Optional[KeyVersion]:
        """Get a specific key version.
        
        Args:
            version: Key version number
            
        Returns:
            Optional[KeyVersion]: The key if found
        """
        return self._keys.get(version)
    
    def get_all_active_keys(self) -> list[KeyVersion]:
        """Get all active keys for decryption.
        
        Returns:
            list[KeyVersion]: All active keys, newest first
        """
        return sorted(
            [k for k in self._keys.values() if k.is_active],
            key=lambda x: x.version,
            reverse=True
        )
    
    def rotate_key(self, new_master_key: Optional[str] = None) -> KeyVersion:
        """Rotate to a new encryption key.
        
        Args:
            new_master_key: Optional new master key (uses existing if not provided)
            
        Returns:
            KeyVersion: The new key version
        """
        new_version = self._current_version + 1
        master_key = new_master_key or settings.KMS_ENCRYPTION_KEY
        
        new_key = self._derive_key(master_key, version=new_version)
        key_version = KeyVersion(
            version=new_version,
            key=new_key,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self._keys[new_version] = key_version
        self._current_version = new_version
        
        return key_version
    
    def deactivate_key(self, version: int) -> bool:
        """Deactivate an old key version.
        
        Args:
            version: Key version to deactivate
            
        Returns:
            bool: True if deactivated successfully
        """
        if version == self._current_version:
            return False  # Cannot deactivate current key
        
        if version in self._keys:
            self._keys[version].is_active = False
            return True
        return False
    
    def should_rotate(self) -> bool:
        """Check if key rotation is needed based on age.
        
        Returns:
            bool: True if rotation is recommended
        """
        current_key = self.get_current_key()
        age = datetime.utcnow() - current_key.created_at
        return age > timedelta(days=self._rotation_interval_days)
    
    def get_fernet(self) -> Fernet:
        """Get a Fernet instance with the current key.
        
        Returns:
            Fernet: Configured Fernet encryption instance
        """
        return Fernet(self.get_current_key().key)
    
    def get_multi_fernet(self) -> MultiFernet:
        """Get a MultiFernet instance with all active keys.
        
        This allows decryption with any active key version while
        encrypting with the newest key.
        
        Returns:
            MultiFernet: Configured MultiFernet instance
        """
        active_keys = self.get_all_active_keys()
        fernets = [Fernet(k.key) for k in active_keys]
        return MultiFernet(fernets)
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
        cls._keys = {}
        cls._current_version = 1


# Global key manager instance
_key_manager: Optional[KMSKeyManager] = None


def get_key_manager() -> KMSKeyManager:
    """Get the global KMS key manager instance.
    
    Returns:
        KMSKeyManager: The key manager instance
    """
    global _key_manager
    if _key_manager is None:
        _key_manager = KMSKeyManager()
    return _key_manager


def reset_key_manager() -> None:
    """Reset the key manager (for testing)."""
    global _key_manager
    KMSKeyManager.reset()
    _key_manager = None


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata."""
    ciphertext: str
    key_version: int
    encrypted_at: datetime
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "ciphertext": self.ciphertext,
            "key_version": self.key_version,
            "encrypted_at": self.encrypted_at.isoformat()
        })
    
    @classmethod
    def from_json(cls, data: str) -> "EncryptedData":
        """Deserialize from JSON string."""
        parsed = json.loads(data)
        return cls(
            ciphertext=parsed["ciphertext"],
            key_version=parsed["key_version"],
            encrypted_at=datetime.fromisoformat(parsed["encrypted_at"])
        )


def kms_encrypt(plaintext: str) -> EncryptedData:
    """Encrypt data using KMS with key versioning.
    
    Args:
        plaintext: The plain text to encrypt
        
    Returns:
        EncryptedData: Encrypted data with metadata
        
    Raises:
        ValueError: If plaintext is empty
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty data")
    
    km = get_key_manager()
    fernet = km.get_fernet()
    ciphertext = fernet.encrypt(plaintext.encode()).decode()
    
    return EncryptedData(
        ciphertext=ciphertext,
        key_version=km._current_version,
        encrypted_at=datetime.utcnow()
    )


def kms_decrypt(encrypted_data: EncryptedData) -> Optional[str]:
    """Decrypt data using KMS with multi-key support.
    
    Args:
        encrypted_data: The encrypted data container
        
    Returns:
        Optional[str]: Decrypted plaintext or None if decryption fails
    """
    if not encrypted_data.ciphertext:
        return None
    
    km = get_key_manager()
    
    # Try with MultiFernet for backward compatibility
    try:
        multi_fernet = km.get_multi_fernet()
        decrypted = multi_fernet.decrypt(encrypted_data.ciphertext.encode())
        return decrypted.decode()
    except InvalidToken:
        return None


def kms_encrypt_simple(plaintext: str) -> str:
    """Simple encryption that returns just the ciphertext.
    
    For backward compatibility with existing code.
    
    Args:
        plaintext: The plain text to encrypt
        
    Returns:
        str: Encrypted ciphertext
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty data")
    
    km = get_key_manager()
    fernet = km.get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def kms_decrypt_simple(ciphertext: str) -> Optional[str]:
    """Simple decryption from ciphertext string.
    
    For backward compatibility with existing code.
    
    Args:
        ciphertext: The encrypted ciphertext
        
    Returns:
        Optional[str]: Decrypted plaintext or None if decryption fails
    """
    if not ciphertext:
        return None
    
    km = get_key_manager()
    
    try:
        multi_fernet = km.get_multi_fernet()
        decrypted = multi_fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except InvalidToken:
        return None


def kms_rotate_and_reencrypt(ciphertext: str, new_master_key: Optional[str] = None) -> str:
    """Rotate key and re-encrypt data with the new key.
    
    Args:
        ciphertext: The current encrypted data
        new_master_key: Optional new master key
        
    Returns:
        str: Data re-encrypted with the new key
        
    Raises:
        ValueError: If decryption fails
    """
    km = get_key_manager()
    
    # Decrypt with current keys
    plaintext = kms_decrypt_simple(ciphertext)
    if plaintext is None:
        raise ValueError("Failed to decrypt data for re-encryption")
    
    # Rotate to new key
    km.rotate_key(new_master_key)
    
    # Re-encrypt with new key
    return kms_encrypt_simple(plaintext)


def is_kms_encrypted(value: str) -> bool:
    """Check if a value appears to be KMS-encrypted (Fernet format).
    
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


def get_key_rotation_status() -> dict[str, Any]:
    """Get the current key rotation status.
    
    Returns:
        dict: Key rotation status information
    """
    km = get_key_manager()
    current_key = km.get_current_key()
    
    return {
        "current_version": km._current_version,
        "total_keys": len(km._keys),
        "active_keys": len(km.get_all_active_keys()),
        "current_key_age_days": (datetime.utcnow() - current_key.created_at).days,
        "rotation_recommended": km.should_rotate(),
        "rotation_interval_days": km._rotation_interval_days
    }
