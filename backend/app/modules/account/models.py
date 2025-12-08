"""YouTube Account model for multi-account management.

Implements encrypted token storage for OAuth credentials as per Requirements 2.1, 2.2, 25.1.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.encryption import decrypt_token, encrypt_token, is_encrypted


class AccountStatus(str, Enum):
    """Status of a YouTube account connection."""

    ACTIVE = "active"
    EXPIRED = "expired"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class YouTubeAccount(Base):
    """YouTube Account model with encrypted OAuth token storage.

    Stores YouTube channel information and OAuth credentials.
    Tokens are encrypted using AES-256 (KMS) before storage.
    """

    __tablename__ = "youtube_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # YouTube channel information
    channel_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    channel_title: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Channel statistics
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    # Monetization and streaming
    is_monetized: Mapped[bool] = mapped_column(Boolean, default=False)
    has_live_streaming_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Strike information
    strike_count: Mapped[int] = mapped_column(Integer, default=0)

    # OAuth tokens (encrypted)
    _access_token: Mapped[Optional[str]] = mapped_column(
        "access_token", Text, nullable=True
    )
    _refresh_token: Mapped[Optional[str]] = mapped_column(
        "refresh_token", Text, nullable=True
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Quota tracking
    daily_quota_used: Mapped[int] = mapped_column(Integer, default=0)
    quota_reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Account status
    status: Mapped[str] = mapped_column(
        String(50), default=AccountStatus.ACTIVE.value
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def access_token(self) -> Optional[str]:
        """Get decrypted access token.

        Returns:
            Optional[str]: Decrypted access token or None
        """
        if not self._access_token:
            return None
        return decrypt_token(self._access_token)

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set and encrypt access token.

        Args:
            value: Plain text access token to encrypt and store
        """
        if value is None:
            self._access_token = None
        else:
            self._access_token = encrypt_token(value)

    @property
    def refresh_token(self) -> Optional[str]:
        """Get decrypted refresh token.

        Returns:
            Optional[str]: Decrypted refresh token or None
        """
        if not self._refresh_token:
            return None
        return decrypt_token(self._refresh_token)

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Set and encrypt refresh token.

        Args:
            value: Plain text refresh token to encrypt and store
        """
        if value is None:
            self._refresh_token = None
        else:
            self._refresh_token = encrypt_token(value)

    def is_token_encrypted(self) -> bool:
        """Check if tokens are properly encrypted.

        Returns:
            bool: True if both tokens are encrypted (or None)
        """
        access_encrypted = self._access_token is None or is_encrypted(self._access_token)
        refresh_encrypted = self._refresh_token is None or is_encrypted(self._refresh_token)
        return access_encrypted and refresh_encrypted

    def is_token_expired(self) -> bool:
        """Check if the access token is expired.

        Returns:
            bool: True if token is expired or expiry is unknown
        """
        if self.token_expires_at is None:
            return True
        return datetime.utcnow() >= self.token_expires_at.replace(tzinfo=None)

    def is_token_expiring_soon(self, hours: int = 24) -> bool:
        """Check if the token is expiring within the specified hours.

        Args:
            hours: Number of hours to check (default 24)

        Returns:
            bool: True if token expires within the specified hours
        """
        if self.token_expires_at is None:
            return True
        from datetime import timedelta
        expiry_threshold = datetime.utcnow() + timedelta(hours=hours)
        return self.token_expires_at.replace(tzinfo=None) <= expiry_threshold

    def get_quota_usage_percent(self, daily_limit: int = 10000) -> float:
        """Calculate quota usage percentage.

        Args:
            daily_limit: Daily quota limit (default 10000)

        Returns:
            float: Percentage of quota used (0-100)
        """
        if daily_limit <= 0:
            return 100.0
        return min(100.0, (self.daily_quota_used / daily_limit) * 100)

    def __repr__(self) -> str:
        return f"<YouTubeAccount(id={self.id}, channel={self.channel_title}, status={self.status})>"
