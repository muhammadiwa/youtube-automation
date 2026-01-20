"""YouTube Account service for account management operations.

Implements OAuth2 flow, token management, and account operations.
Requirements: 2.1, 2.2, 2.3, 2.5
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow, to_naive_utc
from app.modules.account.models import AccountStatus, YouTubeAccount
from app.modules.account.oauth import OAuthError, OAuthStateStore, YouTubeOAuthClient
from app.modules.account.repository import YouTubeAccountRepository
from app.modules.account.schemas import (
    AccountHealthResponse,
    ChannelMetadata,
    OAuthInitiateResponse,
    QuotaUsageResponse,
    YouTubeAccountResponse,
)

logger = logging.getLogger(__name__)


class AccountExistsError(Exception):
    """Exception raised when account already exists."""
    pass


class AccountNotFoundError(Exception):
    """Exception raised when account is not found."""
    pass


class YouTubeAccountService:
    """Service for YouTube account management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize account service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.repository = YouTubeAccountRepository(session)
        self.oauth_client = YouTubeOAuthClient()

    async def initiate_oauth(self, user_id: uuid.UUID) -> OAuthInitiateResponse:
        """Initiate OAuth2 flow for YouTube account connection.

        Creates a state parameter and returns the authorization URL.

        Args:
            user_id: User initiating the OAuth flow

        Returns:
            OAuthInitiateResponse: Authorization URL and state parameter
        """
        state = OAuthStateStore.create_state(user_id)
        authorization_url = self.oauth_client.get_authorization_url(state)

        return OAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state,
        )

    async def handle_oauth_callback(
        self,
        code: str,
        state: str,
    ) -> YouTubeAccount:
        """Handle OAuth2 callback and create account.

        Validates state, exchanges code for tokens, fetches channel info,
        and creates the YouTube account.

        Args:
            code: Authorization code from YouTube
            state: State parameter for verification

        Returns:
            YouTubeAccount: Created account instance

        Raises:
            OAuthError: If state is invalid or token exchange fails
            AccountExistsError: If channel is already connected
            LimitExceededError: If account limit reached
        """
        # Validate state and get user_id
        user_id = OAuthStateStore.validate_state(state)
        if user_id is None:
            raise OAuthError("Invalid or expired OAuth state")
        
        # Check account limit before proceeding
        from app.modules.billing.feature_gate import FeatureGateService, LimitExceededError
        feature_gate = FeatureGateService(self.session)
        await feature_gate.check_accounts_limit(user_id, raise_on_exceed=True)

        # Exchange code for tokens
        token_response = await self.oauth_client.exchange_code(code)

        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        if not refresh_token:
            raise OAuthError("No refresh token received. Please revoke access and try again.")

        # Calculate token expiration
        token_expires_at = to_naive_utc(utcnow()) + timedelta(seconds=expires_in)

        # Fetch channel information
        channel_info = await self.oauth_client.get_channel_info(access_token)

        # Check if channel already connected
        existing = await self.repository.get_by_channel_id(channel_info["channel_id"])
        if existing:
            raise AccountExistsError(
                f"Channel '{channel_info['channel_title']}' is already connected"
            )

        # Create account with encrypted tokens
        account = await self.repository.create(
            user_id=user_id,
            channel_id=channel_info["channel_id"],
            channel_title=channel_info["channel_title"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            thumbnail_url=channel_info.get("thumbnail_url"),
            subscriber_count=channel_info.get("subscriber_count", 0),
            video_count=channel_info.get("video_count", 0),
            is_monetized=channel_info.get("is_monetized", False),
            has_live_streaming_enabled=channel_info.get("has_live_streaming_enabled", False),
        )

        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        
        # Trigger account.connected webhook event
        # Requirements: 3.6 - Trigger account.connected event
        try:
            from app.modules.integration.webhook_trigger import trigger_account_connected
            await trigger_account_connected(
                session=self.session,
                user_id=user_id,
                account_id=account.id,
                account_data={
                    "channel_id": account.channel_id,
                    "channel_title": account.channel_title,
                    "thumbnail_url": account.thumbnail_url,
                    "subscriber_count": account.subscriber_count,
                    "video_count": account.video_count,
                    "is_monetized": account.is_monetized,
                    "has_live_streaming_enabled": account.has_live_streaming_enabled,
                },
            )
            logger.info(f"Triggered account.connected webhook for account {account.id}")
        except Exception as e:
            # Don't fail the account connection if webhook fails
            logger.error(f"Failed to trigger account.connected webhook: {e}")
        
        return account

    async def get_account(self, account_id: uuid.UUID) -> Optional[YouTubeAccount]:
        """Get account by ID.

        Args:
            account_id: Account UUID

        Returns:
            Optional[YouTubeAccount]: Account if found
        """
        return await self.repository.get_by_id(account_id)

    async def get_user_accounts(self, user_id: uuid.UUID) -> list[YouTubeAccount]:
        """Get all accounts for a user.

        Args:
            user_id: User UUID

        Returns:
            list[YouTubeAccount]: User's YouTube accounts
        """
        return await self.repository.get_by_user_id(user_id)

    async def get_account_health(
        self,
        account_id: uuid.UUID,
    ) -> AccountHealthResponse:
        """Get account health status.

        Args:
            account_id: Account UUID

        Returns:
            AccountHealthResponse: Health status information

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        return AccountHealthResponse(
            account_id=account.id,
            channel_title=account.channel_title,
            status=account.status,
            is_token_expired=account.is_token_expired(),
            is_token_expiring_soon=account.is_token_expiring_soon(hours=24),
            token_expires_at=account.token_expires_at,
            quota_usage_percent=account.get_quota_usage_percent(),
            daily_quota_used=account.daily_quota_used,
            last_sync_at=account.last_sync_at,
            last_error=account.last_error,
        )

    async def get_quota_usage(
        self,
        account_id: uuid.UUID,
        daily_limit: int = 10000,
    ) -> QuotaUsageResponse:
        """Get quota usage for an account.

        Args:
            account_id: Account UUID
            daily_limit: Daily quota limit

        Returns:
            QuotaUsageResponse: Quota usage information

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        usage_percent = account.get_quota_usage_percent(daily_limit)

        return QuotaUsageResponse(
            account_id=account.id,
            daily_quota_used=account.daily_quota_used,
            daily_limit=daily_limit,
            usage_percent=usage_percent,
            quota_reset_at=account.quota_reset_at,
            is_approaching_limit=usage_percent >= 80.0,
        )

    async def sync_channel_data(
        self,
        account_id: uuid.UUID,
    ) -> YouTubeAccount:
        """Sync channel data from YouTube API.

        Args:
            account_id: Account UUID

        Returns:
            YouTubeAccount: Updated account

        Raises:
            AccountNotFoundError: If account not found
            OAuthError: If API call fails
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        # Refresh token if expired
        if account.is_token_expired():
            await self._refresh_account_token(account)

        # Fetch channel info
        channel_info = await self.oauth_client.get_channel_info(account.access_token)

        # Update account metadata
        account = await self.repository.update_channel_metadata(
            account,
            channel_title=channel_info.get("channel_title"),
            thumbnail_url=channel_info.get("thumbnail_url"),
            subscriber_count=channel_info.get("subscriber_count"),
            video_count=channel_info.get("video_count"),
            view_count=channel_info.get("view_count"),
            is_monetized=channel_info.get("is_monetized"),
            has_live_streaming_enabled=channel_info.get("has_live_streaming_enabled"),
        )

        # Also try to sync stream key if live streaming is enabled
        if channel_info.get("has_live_streaming_enabled"):
            try:
                await self.sync_stream_key(account_id)
            except OAuthError:
                # Stream key sync failed, but channel sync succeeded
                # Don't fail the whole operation
                pass

        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        return account

    async def sync_stream_key(
        self,
        account_id: uuid.UUID,
    ) -> YouTubeAccount:
        """Sync stream key from YouTube Live Streaming API.

        Fetches the default live stream configuration including stream key.

        Args:
            account_id: Account UUID

        Returns:
            YouTubeAccount: Updated account with stream key

        Raises:
            AccountNotFoundError: If account not found
            OAuthError: If API call fails or live streaming not enabled
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        # Refresh token if expired
        if account.is_token_expired():
            await self._refresh_account_token(account)

        # Fetch live stream info
        stream_info = await self.oauth_client.get_live_stream_info(account.access_token)

        if not stream_info.get("has_streams"):
            raise OAuthError(stream_info.get("message", "No live streams found"))

        # Update stream key
        account = await self.repository.update_stream_key(
            account,
            stream_key=stream_info.get("stream_key"),
            rtmp_url=stream_info.get("rtmp_url"),
            default_stream_id=stream_info.get("stream_id"),
        )

        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        return account

    async def get_stream_key_status(
        self,
        account_id: uuid.UUID,
    ) -> dict:
        """Get stream key status for an account.

        Args:
            account_id: Account UUID

        Returns:
            dict: Stream key status information

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        return {
            "account_id": account.id,
            "channel_title": account.channel_title,
            "has_stream_key": account.has_stream_key(),
            "stream_key_masked": account.get_masked_stream_key(),
            "stream_key": account.stream_key,  # Return actual stream key for auto-fill
            "rtmp_url": account.rtmp_url,
            "default_stream_id": account.default_stream_id,
            "has_live_streaming_enabled": account.has_live_streaming_enabled,
            "last_sync_at": account.last_sync_at,
        }

    async def disconnect_account(self, account_id: uuid.UUID) -> None:
        """Disconnect a YouTube account.

        Args:
            account_id: Account UUID

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        # Store account data for webhook before deletion
        user_id = account.user_id
        account_data = {
            "channel_id": account.channel_id,
            "channel_title": account.channel_title,
            "thumbnail_url": account.thumbnail_url,
            "subscriber_count": account.subscriber_count,
            "video_count": account.video_count,
        }

        await self.repository.delete(account)
        await self.session.commit()
        
        # Trigger account.disconnected webhook event
        # Requirements: 3.7 - Trigger account.disconnected event
        try:
            from app.modules.integration.webhook_trigger import trigger_account_disconnected
            await trigger_account_disconnected(
                session=self.session,
                user_id=user_id,
                account_id=account_id,
                account_data=account_data,
            )
            logger.info(f"Triggered account.disconnected webhook for account {account_id}")
        except Exception as e:
            # Don't fail the disconnect if webhook fails
            logger.error(f"Failed to trigger account.disconnected webhook: {e}")

    async def refresh_account_token(
        self,
        account_id: uuid.UUID,
    ) -> YouTubeAccount:
        """Refresh access token for an account by ID.

        Args:
            account_id: Account UUID

        Returns:
            YouTubeAccount: Updated account with new tokens

        Raises:
            AccountNotFoundError: If account not found
            OAuthError: If token refresh fails
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        account = await self._refresh_account_token(account)
        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        return account

    async def increment_quota_usage(
        self,
        account_id: uuid.UUID,
        amount: int = 1,
    ) -> YouTubeAccount:
        """Increment quota usage for an account.

        Args:
            account_id: Account UUID
            amount: Amount to increment

        Returns:
            YouTubeAccount: Updated account

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        account = await self.repository.increment_quota_usage(account, amount)
        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        return account

    async def reset_quota(self, account_id: uuid.UUID) -> YouTubeAccount:
        """Reset daily quota for an account.

        Args:
            account_id: Account UUID

        Returns:
            YouTubeAccount: Updated account

        Raises:
            AccountNotFoundError: If account not found
        """
        account = await self.repository.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")

        account = await self.repository.reset_daily_quota(account)
        await self.session.commit()
        # Refresh account to get updated data after commit
        await self.session.refresh(account)
        return account

    async def get_accounts_approaching_quota_limit(
        self,
        threshold_percent: float = 80.0,
        daily_limit: int = 10000,
    ) -> list[YouTubeAccount]:
        """Get accounts approaching quota limit.

        Args:
            threshold_percent: Percentage threshold
            daily_limit: Daily quota limit

        Returns:
            list[YouTubeAccount]: Accounts approaching limit
        """
        return await self.repository.get_accounts_approaching_quota_limit(
            threshold_percent, daily_limit
        )

    async def refresh_token_if_needed(self, account: YouTubeAccount) -> YouTubeAccount:
        """Refresh access token if expired or expiring soon.

        Args:
            account: Account instance

        Returns:
            YouTubeAccount: Account with valid tokens
        """
        if account.is_token_expired() or account.is_token_expiring_soon(hours=1):
            account = await self._refresh_account_token(account)
            await self.session.commit()
            # Refresh account to get updated data after commit
            await self.session.refresh(account)
        return account

    async def _refresh_account_token(self, account: YouTubeAccount) -> YouTubeAccount:
        """Refresh access token for an account.

        Args:
            account: Account instance

        Returns:
            YouTubeAccount: Updated account with new tokens

        Raises:
            OAuthError: If token refresh fails
        """
        try:
            token_response = await self.oauth_client.refresh_access_token(
                account.refresh_token
            )

            access_token = token_response["access_token"]
            expires_in = token_response.get("expires_in", 3600)
            token_expires_at = to_naive_utc(utcnow()) + timedelta(seconds=expires_in)

            # Update tokens (refresh_token may or may not be returned)
            new_refresh_token = token_response.get("refresh_token")

            account = await self.repository.update_tokens(
                account,
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=token_expires_at,
            )

            return account

        except OAuthError as e:
            # Mark account as expired
            await self.repository.set_status(
                account,
                AccountStatus.EXPIRED,
                error=str(e),
            )
            
            # Trigger account.token_expired webhook event
            # Requirements: 3.7 (token expired notification)
            try:
                from app.modules.integration.webhook_trigger import trigger_account_token_expired
                await trigger_account_token_expired(
                    session=self.session,
                    user_id=account.user_id,
                    account_id=account.id,
                    account_data={
                        "channel_id": account.channel_id,
                        "channel_title": account.channel_title,
                        "error": str(e),
                    },
                )
                logger.info(f"Triggered account.token_expired webhook for account {account.id}")
            except Exception as webhook_error:
                # Don't fail if webhook fails
                logger.error(f"Failed to trigger account.token_expired webhook: {webhook_error}")
            
            raise

    async def get_valid_access_token(self, account: YouTubeAccount) -> str:
        """Get a valid access token, refreshing if necessary.

        Args:
            account: Account instance

        Returns:
            str: Valid access token

        Raises:
            OAuthError: If token refresh fails
        """
        if account.is_token_expired() or account.is_token_expiring_soon(hours=1):
            account = await self._refresh_account_token(account)
            await self.session.commit()
        return account.access_token


# Alias for backward compatibility
AccountService = YouTubeAccountService

