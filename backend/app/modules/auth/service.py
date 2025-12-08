"""Authentication service for user management and authentication."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.jwt import (
    AuthTokens,
    TokenPayload,
    blacklist_token,
    create_auth_tokens,
    validate_token,
)
from app.modules.auth.models import PasswordValidationError, User
from app.modules.auth.repository import UserRepository


class AuthenticationError(Exception):
    """Exception raised for authentication failures."""

    pass


class UserExistsError(Exception):
    """Exception raised when user already exists."""

    pass


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        """Initialize auth service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(
        self,
        email: str,
        password: str,
        name: str,
    ) -> User:
        """Register a new user.

        Args:
            email: User email address
            password: Plain text password
            name: User display name

        Returns:
            User: Created user

        Raises:
            UserExistsError: If email already registered
            PasswordValidationError: If password doesn't meet policy
        """
        # Normalize email
        email = email.lower().strip()

        # Check if user exists
        if await self.user_repo.exists_by_email(email):
            raise UserExistsError(f"User with email {email} already exists")

        # Create user (password validation happens in repository)
        user = await self.user_repo.create(
            email=email,
            password=password,
            name=name,
            validate_password=True,
        )

        return user

    async def login(
        self,
        email: str,
        password: str,
        totp_code: str | None = None,
    ) -> AuthTokens:
        """Authenticate user and return tokens.

        Args:
            email: User email address
            password: Plain text password
            totp_code: TOTP code if 2FA is enabled

        Returns:
            AuthTokens: Access and refresh tokens

        Raises:
            AuthenticationError: If credentials are invalid or 2FA required
        """
        email = email.lower().strip()

        # Get user
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Verify password
        if not user.verify_password(password):
            raise AuthenticationError("Invalid email or password")

        # Check 2FA if enabled
        if user.is_2fa_enabled:
            if totp_code is None:
                raise AuthenticationError("2FA code required")
            # 2FA verification will be implemented in task 2.4
            # For now, we'll import and use it when available

        # Update last login
        await self.user_repo.update_last_login(user)

        # Generate tokens
        return create_auth_tokens(user.id)

    async def refresh_tokens(self, refresh_token: str) -> AuthTokens:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            AuthTokens: New access and refresh tokens

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = validate_token(refresh_token, "refresh")
        if payload is None:
            raise AuthenticationError("Invalid or expired refresh token")

        # Get user
        user_id = uuid.UUID(payload.sub)
        user = await self.user_repo.get_by_id(user_id)

        if user is None or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        # Blacklist old refresh token (token rotation)
        blacklist_token(refresh_token)

        # Generate new tokens
        return create_auth_tokens(user.id)

    async def logout(self, access_token: str, refresh_token: str | None = None) -> bool:
        """Logout user by blacklisting tokens.

        Args:
            access_token: Access token to blacklist
            refresh_token: Optional refresh token to blacklist

        Returns:
            bool: True if logout successful
        """
        blacklist_token(access_token)
        if refresh_token:
            blacklist_token(refresh_token)
        return True

    async def validate_access_token(self, token: str) -> TokenPayload | None:
        """Validate an access token.

        Args:
            token: Access token to validate

        Returns:
            TokenPayload | None: Token payload if valid
        """
        return validate_token(token, "access")

    async def get_current_user(self, token: str) -> User | None:
        """Get current user from access token.

        Args:
            token: Valid access token

        Returns:
            User | None: User if token is valid
        """
        payload = validate_token(token, "access")
        if payload is None:
            return None

        user_id = uuid.UUID(payload.sub)
        return await self.user_repo.get_by_id(user_id)

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password.

        Args:
            user: User instance
            current_password: Current password for verification
            new_password: New password

        Returns:
            bool: True if password changed

        Raises:
            AuthenticationError: If current password is wrong
            PasswordValidationError: If new password doesn't meet policy
        """
        if not user.verify_password(current_password):
            raise AuthenticationError("Current password is incorrect")

        await self.user_repo.update_password(user, new_password, validate=True)
        return True


    async def setup_2fa(self, user: User) -> "TwoFactorSetup":
        """Set up 2FA for a user.

        Args:
            user: User instance

        Returns:
            TwoFactorSetup: Setup data including secret, URI, and backup codes
        """
        from app.modules.auth.totp import (
            TwoFactorSetup,
            encode_backup_codes,
            generate_backup_codes,
            generate_totp_secret,
            get_totp_uri,
        )

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, user.email)
        backup_codes = generate_backup_codes(10)

        # Store secret and backup codes (not enabled yet until verified)
        user.totp_secret = secret
        user.backup_codes = encode_backup_codes(backup_codes)
        await self.session.flush()

        return TwoFactorSetup(secret=secret, uri=uri, backup_codes=backup_codes)

    async def enable_2fa(self, user: User, code: str) -> bool:
        """Enable 2FA after verifying initial code.

        Args:
            user: User instance
            code: TOTP code to verify

        Returns:
            bool: True if 2FA enabled successfully

        Raises:
            AuthenticationError: If code is invalid or no secret set up
        """
        from app.modules.auth.totp import verify_totp_code

        if not user.totp_secret:
            raise AuthenticationError("2FA not set up. Call setup_2fa first.")

        if not verify_totp_code(user.totp_secret, code):
            raise AuthenticationError("Invalid 2FA code")

        user.is_2fa_enabled = True
        await self.session.flush()
        return True

    async def disable_2fa(self, user: User, code: str) -> bool:
        """Disable 2FA for a user.

        Args:
            user: User instance
            code: TOTP code to verify

        Returns:
            bool: True if 2FA disabled successfully

        Raises:
            AuthenticationError: If code is invalid
        """
        from app.modules.auth.totp import verify_totp_code

        if not user.is_2fa_enabled or not user.totp_secret:
            return True  # Already disabled

        if not verify_totp_code(user.totp_secret, code):
            raise AuthenticationError("Invalid 2FA code")

        await self.user_repo.disable_2fa(user)
        return True

    async def verify_2fa(self, user: User, code: str) -> bool:
        """Verify 2FA code during login.

        Args:
            user: User instance
            code: TOTP code or backup code

        Returns:
            bool: True if code is valid

        Raises:
            AuthenticationError: If 2FA not enabled or code invalid
        """
        from app.modules.auth.totp import verify_backup_code, verify_totp_code

        if not user.is_2fa_enabled:
            return True  # 2FA not required

        if not user.totp_secret:
            raise AuthenticationError("2FA configuration error")

        # Try TOTP code first
        if verify_totp_code(user.totp_secret, code):
            return True

        # Try backup code
        if user.backup_codes:
            is_valid, updated_codes = verify_backup_code(user.backup_codes, code)
            if is_valid:
                user.backup_codes = updated_codes
                await self.session.flush()
                return True

        raise AuthenticationError("Invalid 2FA code")

    async def get_remaining_backup_codes_count(self, user: User) -> int:
        """Get count of remaining backup codes.

        Args:
            user: User instance

        Returns:
            int: Number of remaining backup codes
        """
        from app.modules.auth.totp import decode_backup_codes

        if not user.backup_codes:
            return 0
        return len(decode_backup_codes(user.backup_codes))

    async def regenerate_backup_codes(self, user: User, code: str) -> list[str]:
        """Regenerate backup codes after verifying 2FA.

        Args:
            user: User instance
            code: TOTP code to verify

        Returns:
            list[str]: New backup codes

        Raises:
            AuthenticationError: If code is invalid
        """
        from app.modules.auth.totp import (
            encode_backup_codes,
            generate_backup_codes,
            verify_totp_code,
        )

        if not user.is_2fa_enabled or not user.totp_secret:
            raise AuthenticationError("2FA not enabled")

        if not verify_totp_code(user.totp_secret, code):
            raise AuthenticationError("Invalid 2FA code")

        backup_codes = generate_backup_codes(10)
        user.backup_codes = encode_backup_codes(backup_codes)
        await self.session.flush()

        return backup_codes


    async def request_password_reset(self, email: str) -> str | None:
        """Request a password reset.

        Args:
            email: User email address

        Returns:
            str | None: Reset token if user exists, None otherwise
                (In production, always return success to prevent email enumeration)
        """
        from app.modules.auth.password_reset import PasswordResetStore

        email = email.lower().strip()
        user = await self.user_repo.get_by_email(email)

        if user is None:
            # In production, we'd still return success to prevent enumeration
            return None

        # Create reset token (valid for 1 hour per Requirements 1.5)
        token = PasswordResetStore.create_token(user.id, expires_hours=1)

        # In production, send email here
        # await send_password_reset_email(user.email, token)

        return token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            bool: True if password reset successful

        Raises:
            AuthenticationError: If token is invalid or expired
            PasswordValidationError: If new password doesn't meet policy
        """
        from app.modules.auth.password_reset import PasswordResetStore

        user_id = PasswordResetStore.consume_token(token)
        if user_id is None:
            raise AuthenticationError("Invalid or expired reset token")

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("User not found")

        # Update password (validation happens in repository)
        await self.user_repo.update_password(user, new_password, validate=True)

        return True

    async def validate_reset_token(self, token: str) -> bool:
        """Validate a password reset token without consuming it.

        Args:
            token: Password reset token

        Returns:
            bool: True if token is valid
        """
        from app.modules.auth.password_reset import PasswordResetStore

        return PasswordResetStore.validate_token(token) is not None
