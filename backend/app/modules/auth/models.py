"""User model for authentication."""

import re
import uuid
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING, List

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.account.models import YouTubeAccount

# Password hashing context with bcrypt (cost factor 12 as per design)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class PasswordValidationError(Exception):
    """Exception raised when password doesn't meet policy requirements."""

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__(f"Password policy violations: {', '.join(violations)}")


def validate_password_policy(password: str) -> list[str]:
    """Validate password against policy requirements.

    Policy requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Returns:
        list[str]: List of policy violations (empty if valid)
    """
    violations = []

    if len(password) < 8:
        violations.append("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        violations.append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        violations.append("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        violations.append("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        violations.append("Password must contain at least one special character")

    return violations


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


class User(Base):
    """User model for authentication and account management."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    backup_codes: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON encoded list
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)  # ISO 3166-1 alpha-2
    
    # Relationships
    youtube_accounts: Mapped[List["YouTubeAccount"]] = relationship(
        "YouTubeAccount", back_populates="user", lazy="selectin"
    )

    def set_password(self, password: str, validate: bool = True) -> None:
        """Set user password with optional validation.

        Args:
            password: Plain text password
            validate: Whether to validate against policy (default True)

        Raises:
            PasswordValidationError: If password doesn't meet policy requirements
        """
        if validate:
            violations = validate_password_policy(password)
            if violations:
                raise PasswordValidationError(violations)
        self.password_hash = hash_password(password)

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            bool: True if password matches
        """
        return verify_password(password, self.password_hash)
