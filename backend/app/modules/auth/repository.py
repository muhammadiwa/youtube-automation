"""User repository for database operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    """Repository for User CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create(
        self,
        email: str,
        password: str,
        name: str,
        validate_password: bool = True,
    ) -> User:
        """Create a new user.

        Args:
            email: User email address
            password: Plain text password
            name: User display name
            validate_password: Whether to validate password policy

        Returns:
            User: Created user instance
        """
        user = User(email=email, name=name, password_hash="")
        user.set_password(password, validate=validate_password)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User | None: User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            User | None: User if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()


    async def update(self, user: User, **kwargs) -> User:
        """Update user attributes.

        Args:
            user: User instance to update
            **kwargs: Attributes to update

        Returns:
            User: Updated user instance
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def update_password(
        self,
        user: User,
        new_password: str,
        validate: bool = True,
    ) -> User:
        """Update user password.

        Args:
            user: User instance
            new_password: New plain text password
            validate: Whether to validate password policy

        Returns:
            User: Updated user instance
        """
        user.set_password(new_password, validate=validate)
        await self.session.flush()
        return user

    async def update_last_login(self, user: User) -> User:
        """Update user's last login timestamp.

        Args:
            user: User instance

        Returns:
            User: Updated user instance
        """
        user.last_login_at = datetime.utcnow()
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        """Delete a user.

        Args:
            user: User instance to delete
        """
        await self.session.delete(user)
        await self.session.flush()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: Email address to check

        Returns:
            bool: True if user exists
        """
        result = await self.session.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def enable_2fa(self, user: User, totp_secret: str, backup_codes: str) -> User:
        """Enable 2FA for user.

        Args:
            user: User instance
            totp_secret: TOTP secret key
            backup_codes: JSON encoded backup codes

        Returns:
            User: Updated user instance
        """
        user.is_2fa_enabled = True
        user.totp_secret = totp_secret
        user.backup_codes = backup_codes
        await self.session.flush()
        return user

    async def disable_2fa(self, user: User) -> User:
        """Disable 2FA for user.

        Args:
            user: User instance

        Returns:
            User: Updated user instance
        """
        user.is_2fa_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        await self.session.flush()
        return user

    async def update_country(self, user: User, country: str | None) -> User:
        """Update user's country based on IP geolocation.

        Args:
            user: User instance
            country: ISO 3166-1 alpha-2 country code (e.g., "US", "ID")

        Returns:
            User: Updated user instance
        """
        if country and len(country) == 2:
            user.country = country.upper()
            await self.session.flush()
        return user
