"""JWT token management for authentication."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    jti: str  # JWT ID for blacklisting


class AuthTokens(BaseModel):
    """Authentication tokens response."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class TokenBlacklist:
    """In-memory token blacklist for logout functionality.

    In production, this should use Redis for distributed blacklisting.
    """

    _blacklisted_tokens: set[str] = set()

    @classmethod
    def add(cls, jti: str) -> None:
        """Add token JTI to blacklist."""
        cls._blacklisted_tokens.add(jti)

    @classmethod
    def is_blacklisted(cls, jti: str) -> bool:
        """Check if token JTI is blacklisted."""
        return jti in cls._blacklisted_tokens

    @classmethod
    def clear(cls) -> None:
        """Clear all blacklisted tokens (for testing)."""
        cls._blacklisted_tokens.clear()


def create_token(
    user_id: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str]:
    """Create a JWT token.

    Args:
        user_id: User UUID
        token_type: "access" or "refresh"
        expires_delta: Token expiration time

    Returns:
        tuple[str, str]: (token, jti) - The encoded token and its unique ID
    """
    jti = str(uuid.uuid4())
    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": token_type,
        "jti": jti,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, jti


def create_access_token(user_id: uuid.UUID) -> tuple[str, str]:
    """Create an access token.

    Args:
        user_id: User UUID

    Returns:
        tuple[str, str]: (token, jti)
    """
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(user_id, "access", expires_delta)


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    """Create a refresh token.

    Args:
        user_id: User UUID

    Returns:
        tuple[str, str]: (token, jti)
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(user_id, "refresh", expires_delta)


def create_auth_tokens(user_id: uuid.UUID) -> AuthTokens:
    """Create both access and refresh tokens.

    Args:
        user_id: User UUID

    Returns:
        AuthTokens: Access and refresh tokens
    """
    access_token, _ = create_access_token(user_id)
    refresh_token, _ = create_refresh_token(user_id)

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT token

    Returns:
        TokenPayload | None: Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.utcfromtimestamp(payload["exp"]),
            iat=datetime.utcfromtimestamp(payload["iat"]),
            type=payload["type"],
            jti=payload["jti"],
        )
    except JWTError:
        return None


def validate_token(token: str, expected_type: str = "access") -> TokenPayload | None:
    """Validate a JWT token.

    Args:
        token: Encoded JWT token
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        TokenPayload | None: Decoded payload if valid, None otherwise
    """
    payload = decode_token(token)

    if payload is None:
        return None

    # Check token type
    if payload.type != expected_type:
        return None

    # Check if blacklisted
    if TokenBlacklist.is_blacklisted(payload.jti):
        return None

    # Check expiration
    if payload.exp < datetime.utcnow():
        return None

    return payload


def blacklist_token(token: str) -> bool:
    """Blacklist a token for logout.

    Args:
        token: Encoded JWT token

    Returns:
        bool: True if successfully blacklisted
    """
    payload = decode_token(token)
    if payload is None:
        return False

    TokenBlacklist.add(payload.jti)
    return True


def get_user_id_from_token(token: str) -> uuid.UUID | None:
    """Extract user ID from a valid access token.

    Args:
        token: Encoded JWT token

    Returns:
        uuid.UUID | None: User ID if token is valid
    """
    payload = validate_token(token, "access")
    if payload is None:
        return None

    try:
        return uuid.UUID(payload.sub)
    except ValueError:
        return None
