"""YouTube Account repository for database operations.

Implements CRUD operations for YouTube accounts with encrypted token handling.
Requirements: 2.1, 2.2, 25.1
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import AccountStatus, YouTubeAccount


class YouTubeAccountRepository:
    """Repository for YouTubeAccount CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        channel_id: str,
        channel_title: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: Optional[datetime] = None,
        thumbnail_url: Optional[str] = None,
        subscriber_count: int = 0,
        video_count: int = 0,
        is_monetized: bool = False,
        has_live_streaming_enabled: bool = False,
    ) -> YouTubeAccount:
        """Create a new YouTube account connection.

        Args:
            user_id: Owner user UUID
            channel_id: YouTube channel ID
            channel_title: Channel display name
            access_token: OAuth access token (will be encrypted)
            refresh_token: OAuth refresh token (will be encrypted)
            token_expires_at: Token expiration datetime
            thumbnail_url: Channel thumbnail URL
            subscriber_count: Current subscriber count
            video_count: Total video count
            is_monetized: Whether channel is monetized
            has_live_streaming_enabled: Whether live streaming is enabled

        Returns:
            YouTubeAccount: Created account instance
        """
        account = YouTubeAccount(
            user_id=user_id,
            channel_id=channel_id,
            channel_title=channel_title,
            thumbnail_url=thumbnail_url,
            subscriber_count=subscriber_count,
            video_count=video_count,
            is_monetized=is_monetized,
            has_live_streaming_enabled=has_live_streaming_enabled,
            token_expires_at=token_expires_at,
            status=AccountStatus.ACTIVE.value,
            last_sync_at=datetime.utcnow(),
        )
        # Set tokens through properties to ensure encryption
        account.access_token = access_token
        account.refresh_token = refresh_token

        self.session.add(account)
        await self.session.flush()
        return account

    async def get_by_id(self, account_id: uuid.UUID) -> Optional[YouTubeAccount]:
        """Get account by ID.

        Args:
            account_id: Account UUID

        Returns:
            Optional[YouTubeAccount]: Account if found, None otherwise
        """
        result = await self.session.execute(
            select(YouTubeAccount).where(YouTubeAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_channel_id(self, channel_id: str) -> Optional[YouTubeAccount]:
        """Get account by YouTube channel ID.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Optional[YouTubeAccount]: Account if found, None otherwise
        """
        result = await self.session.execute(
            select(YouTubeAccount).where(YouTubeAccount.channel_id == channel_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[YouTubeAccount]:
        """Get all accounts for a user.

        Args:
            user_id: User UUID

        Returns:
            list[YouTubeAccount]: List of user's YouTube accounts
        """
        result = await self.session.execute(
            select(YouTubeAccount)
            .where(YouTubeAccount.user_id == user_id)
            .order_by(YouTubeAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_accounts_with_expiring_tokens(
        self, hours: int = 24
    ) -> list[YouTubeAccount]:
        """Get accounts with tokens expiring within specified hours.

        Args:
            hours: Hours until expiration threshold

        Returns:
            list[YouTubeAccount]: Accounts with expiring tokens
        """
        from datetime import timedelta
        threshold = datetime.utcnow() + timedelta(hours=hours)
        result = await self.session.execute(
            select(YouTubeAccount)
            .where(YouTubeAccount.status == AccountStatus.ACTIVE.value)
            .where(YouTubeAccount.token_expires_at <= threshold)
            .where(YouTubeAccount.token_expires_at > datetime.utcnow())
        )
        return list(result.scalars().all())

    async def update(self, account: YouTubeAccount, **kwargs) -> YouTubeAccount:
        """Update account attributes.

        Args:
            account: Account instance to update
            **kwargs: Attributes to update

        Returns:
            YouTubeAccount: Updated account instance
        """
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        await self.session.flush()
        return account

    async def update_tokens(
        self,
        account: YouTubeAccount,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> YouTubeAccount:
        """Update OAuth tokens for an account.

        Args:
            account: Account instance
            access_token: New access token (will be encrypted)
            refresh_token: New refresh token (will be encrypted), optional
            expires_at: Token expiration datetime

        Returns:
            YouTubeAccount: Updated account instance
        """
        account.access_token = access_token
        if refresh_token is not None:
            account.refresh_token = refresh_token
        if expires_at is not None:
            account.token_expires_at = expires_at
        account.status = AccountStatus.ACTIVE.value
        account.last_error = None
        await self.session.flush()
        return account

    async def update_channel_metadata(
        self,
        account: YouTubeAccount,
        channel_title: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        subscriber_count: Optional[int] = None,
        video_count: Optional[int] = None,
        view_count: Optional[int] = None,
        is_monetized: Optional[bool] = None,
        has_live_streaming_enabled: Optional[bool] = None,
        strike_count: Optional[int] = None,
    ) -> YouTubeAccount:
        """Update channel metadata from YouTube API sync.

        Args:
            account: Account instance
            channel_title: Updated channel title
            thumbnail_url: Updated thumbnail URL
            subscriber_count: Updated subscriber count
            video_count: Updated video count
            view_count: Updated view count
            is_monetized: Updated monetization status
            has_live_streaming_enabled: Updated streaming status
            strike_count: Updated strike count

        Returns:
            YouTubeAccount: Updated account instance
        """
        if channel_title is not None:
            account.channel_title = channel_title
        if thumbnail_url is not None:
            account.thumbnail_url = thumbnail_url
        if subscriber_count is not None:
            account.subscriber_count = subscriber_count
        if video_count is not None:
            account.video_count = video_count
        if view_count is not None:
            account.view_count = view_count
        if is_monetized is not None:
            account.is_monetized = is_monetized
        if has_live_streaming_enabled is not None:
            account.has_live_streaming_enabled = has_live_streaming_enabled
        if strike_count is not None:
            account.strike_count = strike_count

        account.last_sync_at = datetime.utcnow()
        await self.session.flush()
        return account

    async def update_quota_usage(
        self, account: YouTubeAccount, quota_used: int
    ) -> YouTubeAccount:
        """Update quota usage for an account.

        Args:
            account: Account instance
            quota_used: New quota usage value

        Returns:
            YouTubeAccount: Updated account instance
        """
        account.daily_quota_used = quota_used
        await self.session.flush()
        return account

    async def increment_quota_usage(
        self, account: YouTubeAccount, amount: int = 1
    ) -> YouTubeAccount:
        """Increment quota usage for an account.

        Args:
            account: Account instance
            amount: Amount to increment

        Returns:
            YouTubeAccount: Updated account instance
        """
        account.daily_quota_used += amount
        await self.session.flush()
        return account

    async def reset_daily_quota(self, account: YouTubeAccount) -> YouTubeAccount:
        """Reset daily quota for an account.

        Args:
            account: Account instance

        Returns:
            YouTubeAccount: Updated account instance
        """
        account.daily_quota_used = 0
        account.quota_reset_at = datetime.utcnow()
        await self.session.flush()
        return account

    async def set_status(
        self,
        account: YouTubeAccount,
        status: AccountStatus,
        error: Optional[str] = None,
    ) -> YouTubeAccount:
        """Set account status.

        Args:
            account: Account instance
            status: New status
            error: Error message if status is ERROR

        Returns:
            YouTubeAccount: Updated account instance
        """
        account.status = status.value
        account.last_error = error
        await self.session.flush()
        return account

    async def delete(self, account: YouTubeAccount) -> None:
        """Delete a YouTube account connection.

        Args:
            account: Account instance to delete
        """
        await self.session.delete(account)
        await self.session.flush()

    async def exists_by_channel_id(self, channel_id: str) -> bool:
        """Check if account exists by channel ID.

        Args:
            channel_id: YouTube channel ID to check

        Returns:
            bool: True if account exists
        """
        result = await self.session.execute(
            select(YouTubeAccount.id).where(YouTubeAccount.channel_id == channel_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_accounts_by_status(
        self, status: AccountStatus
    ) -> list[YouTubeAccount]:
        """Get all accounts with a specific status.

        Args:
            status: Account status to filter by

        Returns:
            list[YouTubeAccount]: Accounts with the specified status
        """
        result = await self.session.execute(
            select(YouTubeAccount).where(YouTubeAccount.status == status.value)
        )
        return list(result.scalars().all())

    async def get_accounts_approaching_quota_limit(
        self, threshold_percent: float = 80.0, daily_limit: int = 10000
    ) -> list[YouTubeAccount]:
        """Get accounts approaching quota limit.

        Args:
            threshold_percent: Percentage threshold (default 80%)
            daily_limit: Daily quota limit

        Returns:
            list[YouTubeAccount]: Accounts approaching quota limit
        """
        threshold_value = int(daily_limit * threshold_percent / 100)
        result = await self.session.execute(
            select(YouTubeAccount)
            .where(YouTubeAccount.status == AccountStatus.ACTIVE.value)
            .where(YouTubeAccount.daily_quota_used >= threshold_value)
        )
        return list(result.scalars().all())
