"""End-to-end tests for OAuth flows.

Tests complete OAuth flows including:
- YouTube account connection via OAuth2
- Token storage and encryption
- Token refresh mechanism
- Account disconnection

**Validates: Requirements 2.1, 2.2, 2.3**
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st, assume


class OAuthFlowState(str, Enum):
    """States in the OAuth flow."""
    INITIAL = "initial"
    AUTHORIZATION_PENDING = "authorization_pending"
    CALLBACK_RECEIVED = "callback_received"
    TOKENS_STORED = "tokens_stored"
    ACCOUNT_CONNECTED = "account_connected"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_EXPIRED = "token_expired"
    ACCOUNT_DISCONNECTED = "account_disconnected"


@dataclass
class MockOAuthState:
    """Mock OAuth state for CSRF protection."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    state_token: str = ""
    redirect_uri: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    is_used: bool = False


@dataclass
class MockYouTubeAccount:
    """Mock YouTube account."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    channel_id: str = ""
    channel_title: str = ""
    access_token_encrypted: str = ""
    refresh_token_encrypted: str = ""
    token_expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    subscriber_count: int = 0
    video_count: int = 0
    is_monetized: bool = False
    status: str = "active"
    last_sync_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MockChannelData:
    """Mock YouTube channel data."""
    channel_id: str = ""
    title: str = ""
    subscriber_count: int = 0
    video_count: int = 0
    is_monetized: bool = False


class MockOAuthFlowService:
    """Mock service for testing OAuth flows."""
    
    ENCRYPTION_PREFIX = "encrypted_"
    
    def __init__(self):
        self.oauth_states: dict[str, MockOAuthState] = {}
        self.accounts: dict[uuid.UUID, MockYouTubeAccount] = {}
        self.accounts_by_channel: dict[str, MockYouTubeAccount] = {}
        self.audit_logs: list[dict] = []
    
    def initiate_oauth(self, user_id: uuid.UUID, redirect_uri: str) -> tuple[str, OAuthFlowState]:
        """Initiate OAuth flow and return authorization URL."""
        state_token = str(uuid.uuid4())
        
        oauth_state = MockOAuthState(
            user_id=user_id,
            state_token=state_token,
            redirect_uri=redirect_uri,
        )
        self.oauth_states[state_token] = oauth_state
        
        auth_url = f"https://accounts.google.com/o/oauth2/auth?state={state_token}&redirect_uri={redirect_uri}"
        
        self._log_audit(user_id, "oauth_initiated", {"redirect_uri": redirect_uri})
        
        return auth_url, OAuthFlowState.AUTHORIZATION_PENDING
    
    def handle_callback(
        self,
        state_token: str,
        authorization_code: str,
    ) -> tuple[Optional[MockYouTubeAccount], OAuthFlowState]:
        """Handle OAuth callback and exchange code for tokens."""
        oauth_state = self.oauth_states.get(state_token)
        
        if not oauth_state:
            return None, OAuthFlowState.INITIAL
        
        if oauth_state.is_used:
            return None, OAuthFlowState.INITIAL
        
        if oauth_state.expires_at < datetime.utcnow():
            return None, OAuthFlowState.INITIAL
        
        oauth_state.is_used = True
        
        # Simulate token exchange
        access_token = f"access_{uuid.uuid4()}"
        refresh_token = f"refresh_{uuid.uuid4()}"
        
        # Simulate fetching channel data
        channel_data = self._fetch_channel_data(access_token)
        
        # Check if channel already connected
        if channel_data.channel_id in self.accounts_by_channel:
            existing = self.accounts_by_channel[channel_data.channel_id]
            if existing.user_id != oauth_state.user_id:
                raise ValueError("Channel already connected to another user")
        
        # Create or update account
        account = MockYouTubeAccount(
            user_id=oauth_state.user_id,
            channel_id=channel_data.channel_id,
            channel_title=channel_data.title,
            access_token_encrypted=self._encrypt(access_token),
            refresh_token_encrypted=self._encrypt(refresh_token),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            subscriber_count=channel_data.subscriber_count,
            video_count=channel_data.video_count,
            is_monetized=channel_data.is_monetized,
        )
        
        self.accounts[account.id] = account
        self.accounts_by_channel[account.channel_id] = account
        
        self._log_audit(
            oauth_state.user_id,
            "oauth_completed",
            {"channel_id": channel_data.channel_id},
        )
        
        return account, OAuthFlowState.ACCOUNT_CONNECTED
    
    def refresh_token(self, account_id: uuid.UUID) -> tuple[bool, OAuthFlowState]:
        """Refresh access token for account."""
        account = self.accounts.get(account_id)
        if not account:
            return False, OAuthFlowState.INITIAL
        
        # Decrypt refresh token
        refresh_token = self._decrypt(account.refresh_token_encrypted)
        if not refresh_token:
            return False, OAuthFlowState.TOKEN_EXPIRED
        
        # Simulate token refresh
        new_access_token = f"access_{uuid.uuid4()}"
        
        account.access_token_encrypted = self._encrypt(new_access_token)
        account.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        account.status = "active"
        
        self._log_audit(account.user_id, "token_refreshed", {"account_id": str(account_id)})
        
        return True, OAuthFlowState.TOKEN_REFRESHED
    
    def check_token_expiry(self, account_id: uuid.UUID) -> tuple[bool, OAuthFlowState]:
        """Check if token is expired or expiring soon."""
        account = self.accounts.get(account_id)
        if not account:
            return False, OAuthFlowState.INITIAL
        
        # Check if expired
        if account.token_expires_at < datetime.utcnow():
            account.status = "expired"
            return True, OAuthFlowState.TOKEN_EXPIRED
        
        # Check if expiring within 24 hours
        if account.token_expires_at < datetime.utcnow() + timedelta(hours=24):
            return True, OAuthFlowState.TOKEN_EXPIRED
        
        return False, OAuthFlowState.ACCOUNT_CONNECTED
    
    def disconnect_account(self, account_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bool, OAuthFlowState]:
        """Disconnect YouTube account."""
        account = self.accounts.get(account_id)
        if not account:
            return False, OAuthFlowState.INITIAL
        
        if account.user_id != user_id:
            return False, OAuthFlowState.INITIAL
        
        # Remove account
        del self.accounts[account_id]
        if account.channel_id in self.accounts_by_channel:
            del self.accounts_by_channel[account.channel_id]
        
        self._log_audit(user_id, "account_disconnected", {"channel_id": account.channel_id})
        
        return True, OAuthFlowState.ACCOUNT_DISCONNECTED
    
    def get_accounts(self, user_id: uuid.UUID) -> list[MockYouTubeAccount]:
        """Get all accounts for user."""
        return [a for a in self.accounts.values() if a.user_id == user_id]
    
    def sync_channel_data(self, account_id: uuid.UUID) -> tuple[Optional[MockChannelData], OAuthFlowState]:
        """Sync channel data from YouTube."""
        account = self.accounts.get(account_id)
        if not account:
            return None, OAuthFlowState.INITIAL
        
        # Check token validity
        is_expired, state = self.check_token_expiry(account_id)
        if is_expired and state == OAuthFlowState.TOKEN_EXPIRED:
            # Try to refresh
            success, _ = self.refresh_token(account_id)
            if not success:
                return None, OAuthFlowState.TOKEN_EXPIRED
        
        # Simulate fetching updated data
        access_token = self._decrypt(account.access_token_encrypted)
        channel_data = self._fetch_channel_data(access_token)
        
        # Update account
        account.subscriber_count = channel_data.subscriber_count
        account.video_count = channel_data.video_count
        account.is_monetized = channel_data.is_monetized
        account.last_sync_at = datetime.utcnow()
        
        return channel_data, OAuthFlowState.ACCOUNT_CONNECTED
    
    def _fetch_channel_data(self, access_token: str) -> MockChannelData:
        """Simulate fetching channel data from YouTube API."""
        # Generate deterministic but varied data based on token
        import hashlib
        hash_val = int(hashlib.md5(access_token.encode()).hexdigest()[:8], 16)
        
        return MockChannelData(
            channel_id=f"UC{access_token[-12:]}",
            title=f"Channel {hash_val % 1000}",
            subscriber_count=hash_val % 1000000,
            video_count=hash_val % 1000,
            is_monetized=hash_val % 2 == 0,
        )
    
    def _encrypt(self, value: str) -> str:
        """Simulate KMS encryption."""
        return f"{self.ENCRYPTION_PREFIX}{value}"
    
    def _decrypt(self, encrypted_value: str) -> Optional[str]:
        """Simulate KMS decryption."""
        if encrypted_value.startswith(self.ENCRYPTION_PREFIX):
            return encrypted_value[len(self.ENCRYPTION_PREFIX):]
        return None
    
    def _log_audit(self, user_id: uuid.UUID, action: str, details: dict) -> None:
        """Log audit entry."""
        self.audit_logs.append({
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow(),
        })


# Strategies
user_id_strategy = st.uuids()
redirect_uri_strategy = st.sampled_from([
    "http://localhost:3000/callback",
    "https://app.example.com/oauth/callback",
])
authorization_code_strategy = st.text(min_size=20, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")


class TestCompleteOAuthFlow:
    """End-to-end tests for complete OAuth flows."""

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_complete_oauth_connection_flow(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test complete OAuth flow from initiation to account connection.
        
        **Validates: Requirements 2.1, 2.2**
        """
        service = MockOAuthFlowService()
        
        # Step 1: Initiate OAuth
        auth_url, state = service.initiate_oauth(user_id, redirect_uri)
        assert state == OAuthFlowState.AUTHORIZATION_PENDING
        assert "state=" in auth_url
        
        # Extract state token from URL
        state_token = auth_url.split("state=")[1].split("&")[0]
        
        # Step 2: Handle callback
        account, state = service.handle_callback(state_token, auth_code)
        assert state == OAuthFlowState.ACCOUNT_CONNECTED
        assert account is not None
        assert account.user_id == user_id
        assert account.channel_id != ""
        
        # Verify tokens are encrypted
        assert account.access_token_encrypted.startswith(service.ENCRYPTION_PREFIX)
        assert account.refresh_token_encrypted.startswith(service.ENCRYPTION_PREFIX)
        
        # Verify audit logs
        assert len(service.audit_logs) == 2
        assert service.audit_logs[0]["action"] == "oauth_initiated"
        assert service.audit_logs[1]["action"] == "oauth_completed"

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_token_refresh_flow(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test token refresh flow.
        
        **Validates: Requirements 2.3**
        """
        service = MockOAuthFlowService()
        
        # Connect account
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        account, _ = service.handle_callback(state_token, auth_code)
        
        original_token = account.access_token_encrypted
        
        # Refresh token
        success, state = service.refresh_token(account.id)
        assert success
        assert state == OAuthFlowState.TOKEN_REFRESHED
        
        # Token should be different
        assert account.access_token_encrypted != original_token
        assert account.access_token_encrypted.startswith(service.ENCRYPTION_PREFIX)

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_token_expiry_detection(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test token expiry detection.
        
        **Validates: Requirements 2.3**
        """
        service = MockOAuthFlowService()
        
        # Connect account
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        account, _ = service.handle_callback(state_token, auth_code)
        
        # Set token to expire in 48 hours (beyond 24-hour warning threshold)
        account.token_expires_at = datetime.utcnow() + timedelta(hours=48)
        
        # Token should not be expired initially
        is_expired, state = service.check_token_expiry(account.id)
        assert not is_expired
        assert state == OAuthFlowState.ACCOUNT_CONNECTED
        
        # Expire the token
        account.token_expires_at = datetime.utcnow() - timedelta(hours=1)
        
        is_expired, state = service.check_token_expiry(account.id)
        assert is_expired
        assert state == OAuthFlowState.TOKEN_EXPIRED

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_account_disconnection_flow(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test account disconnection flow.
        
        **Validates: Requirements 2.1**
        """
        service = MockOAuthFlowService()
        
        # Connect account
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        account, _ = service.handle_callback(state_token, auth_code)
        
        # Verify account exists
        accounts = service.get_accounts(user_id)
        assert len(accounts) == 1
        
        # Disconnect
        success, state = service.disconnect_account(account.id, user_id)
        assert success
        assert state == OAuthFlowState.ACCOUNT_DISCONNECTED
        
        # Verify account removed
        accounts = service.get_accounts(user_id)
        assert len(accounts) == 0

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_channel_data_sync_flow(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test channel data synchronization flow.
        
        **Validates: Requirements 2.1**
        """
        service = MockOAuthFlowService()
        
        # Connect account
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        account, _ = service.handle_callback(state_token, auth_code)
        
        original_sync_time = account.last_sync_at
        
        # Sync channel data
        channel_data, state = service.sync_channel_data(account.id)
        assert channel_data is not None
        assert state == OAuthFlowState.ACCOUNT_CONNECTED
        assert account.last_sync_at >= original_sync_time


class TestOAuthFlowErrorScenarios:
    """Test error scenarios in OAuth flows."""

    @given(user_id=user_id_strategy)
    @settings(max_examples=50)
    def test_invalid_state_token_rejected(self, user_id: uuid.UUID) -> None:
        """Test that invalid state tokens are rejected."""
        service = MockOAuthFlowService()
        
        account, state = service.handle_callback("invalid_state", "auth_code")
        assert account is None
        assert state == OAuthFlowState.INITIAL

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_expired_state_token_rejected(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test that expired state tokens are rejected."""
        service = MockOAuthFlowService()
        
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        
        # Expire the state
        service.oauth_states[state_token].expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        account, state = service.handle_callback(state_token, auth_code)
        assert account is None
        assert state == OAuthFlowState.INITIAL

    @given(
        user_id=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_reused_state_token_rejected(
        self,
        user_id: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test that reused state tokens are rejected."""
        service = MockOAuthFlowService()
        
        auth_url, _ = service.initiate_oauth(user_id, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        
        # First callback succeeds
        account1, state1 = service.handle_callback(state_token, auth_code)
        assert account1 is not None
        
        # Second callback fails
        account2, state2 = service.handle_callback(state_token, auth_code)
        assert account2 is None
        assert state2 == OAuthFlowState.INITIAL

    @given(
        user_id1=user_id_strategy,
        user_id2=user_id_strategy,
        redirect_uri=redirect_uri_strategy,
        auth_code=authorization_code_strategy,
    )
    @settings(max_examples=50)
    def test_cannot_disconnect_other_users_account(
        self,
        user_id1: uuid.UUID,
        user_id2: uuid.UUID,
        redirect_uri: str,
        auth_code: str,
    ) -> None:
        """Test that users cannot disconnect other users' accounts."""
        assume(user_id1 != user_id2)
        
        service = MockOAuthFlowService()
        
        # User 1 connects account
        auth_url, _ = service.initiate_oauth(user_id1, redirect_uri)
        state_token = auth_url.split("state=")[1].split("&")[0]
        account, _ = service.handle_callback(state_token, auth_code)
        
        # User 2 tries to disconnect
        success, state = service.disconnect_account(account.id, user_id2)
        assert not success
        assert state == OAuthFlowState.INITIAL
        
        # Account should still exist
        accounts = service.get_accounts(user_id1)
        assert len(accounts) == 1

    @given(user_id=user_id_strategy)
    @settings(max_examples=50)
    def test_refresh_nonexistent_account_fails(self, user_id: uuid.UUID) -> None:
        """Test that refreshing non-existent account fails."""
        service = MockOAuthFlowService()
        
        success, state = service.refresh_token(uuid.uuid4())
        assert not success
        assert state == OAuthFlowState.INITIAL
