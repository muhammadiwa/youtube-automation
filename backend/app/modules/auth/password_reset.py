"""Password reset functionality."""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import NamedTuple


class PasswordResetToken(NamedTuple):
    """Password reset token data."""

    token: str
    user_id: uuid.UUID
    expires_at: datetime


class PasswordResetStore:
    """In-memory store for password reset tokens.

    In production, this should use Redis with TTL.
    """

    _tokens: dict[str, PasswordResetToken] = {}

    @classmethod
    def create_token(cls, user_id: uuid.UUID, expires_hours: int = 1) -> str:
        """Create a password reset token.

        Args:
            user_id: User UUID
            expires_hours: Token validity in hours (default 1)

        Returns:
            str: Reset token
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        cls._tokens[token] = PasswordResetToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )

        return token

    @classmethod
    def validate_token(cls, token: str) -> uuid.UUID | None:
        """Validate a password reset token.

        Args:
            token: Reset token to validate

        Returns:
            uuid.UUID | None: User ID if valid, None otherwise
        """
        reset_token = cls._tokens.get(token)

        if reset_token is None:
            return None

        if reset_token.expires_at < datetime.utcnow():
            # Token expired, remove it
            cls._tokens.pop(token, None)
            return None

        return reset_token.user_id

    @classmethod
    def consume_token(cls, token: str) -> uuid.UUID | None:
        """Validate and consume a password reset token.

        Args:
            token: Reset token to consume

        Returns:
            uuid.UUID | None: User ID if valid, None otherwise
        """
        user_id = cls.validate_token(token)
        if user_id is not None:
            cls._tokens.pop(token, None)
        return user_id

    @classmethod
    def clear(cls) -> None:
        """Clear all tokens (for testing)."""
        cls._tokens.clear()

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired tokens.

        Returns:
            int: Number of tokens removed
        """
        now = datetime.utcnow()
        expired = [
            token for token, data in cls._tokens.items()
            if data.expires_at < now
        ]
        for token in expired:
            cls._tokens.pop(token, None)
        return len(expired)
