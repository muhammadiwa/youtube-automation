"""End-to-end tests for authentication flows.

Tests complete user authentication flows including:
- User registration
- Login with credentials
- 2FA setup and verification
- Password reset flow
- Session management

**Validates: Requirements 1.1, 1.2, 1.4, 1.5**
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import pytest
from hypothesis import given, settings, strategies as st, assume


class AuthFlowState(str, Enum):
    """States in the authentication flow."""
    INITIAL = "initial"
    REGISTERED = "registered"
    LOGGED_IN = "logged_in"
    TWO_FA_PENDING = "2fa_pending"
    TWO_FA_ENABLED = "2fa_enabled"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    LOGGED_OUT = "logged_out"


@dataclass
class MockUser:
    """Mock user for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = ""
    password_hash: str = ""
    name: str = ""
    is_2fa_enabled: bool = False
    totp_secret: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


@dataclass
class MockSession:
    """Mock session for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    access_token: str = ""
    refresh_token: str = ""
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    is_active: bool = True


@dataclass
class MockPasswordResetToken:
    """Mock password reset token."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    token: str = ""
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    is_used: bool = False


class MockAuthFlowService:
    """Mock service for testing complete auth flows."""
    
    def __init__(self):
        self.users: dict[uuid.UUID, MockUser] = {}
        self.users_by_email: dict[str, MockUser] = {}
        self.sessions: dict[uuid.UUID, MockSession] = {}
        self.reset_tokens: dict[str, MockPasswordResetToken] = {}
        self.audit_logs: list[dict] = []
    
    def register(self, email: str, password: str, name: str) -> tuple[MockUser, AuthFlowState]:
        """Register a new user."""
        if email in self.users_by_email:
            raise ValueError("Email already registered")
        
        if not self._validate_password(password):
            raise ValueError("Password does not meet policy requirements")
        
        user = MockUser(
            email=email,
            password_hash=self._hash_password(password),
            name=name,
        )
        self.users[user.id] = user
        self.users_by_email[email] = user
        
        self._log_audit(user.id, "user_registered", {"email": email})
        
        return user, AuthFlowState.REGISTERED
    
    def login(self, email: str, password: str) -> tuple[Optional[MockSession], AuthFlowState]:
        """Login with credentials."""
        user = self.users_by_email.get(email)
        if not user:
            return None, AuthFlowState.INITIAL
        
        if not self._verify_password(password, user.password_hash):
            self._log_audit(user.id, "login_failed", {"reason": "invalid_password"})
            return None, AuthFlowState.INITIAL
        
        if user.is_2fa_enabled:
            # Return partial session, needs 2FA verification
            session = MockSession(
                user_id=user.id,
                access_token="",  # Not issued until 2FA verified
                refresh_token="",
                is_active=False,
            )
            self.sessions[session.id] = session
            return session, AuthFlowState.TWO_FA_PENDING
        
        # Create full session
        session = self._create_session(user)
        user.last_login_at = datetime.utcnow()
        
        self._log_audit(user.id, "login_success", {})
        
        return session, AuthFlowState.LOGGED_IN
    
    def verify_2fa(self, session_id: uuid.UUID, totp_code: str) -> tuple[Optional[MockSession], AuthFlowState]:
        """Verify 2FA code and complete login."""
        session = self.sessions.get(session_id)
        if not session or session.is_active:
            return None, AuthFlowState.INITIAL
        
        user = self.users.get(session.user_id)
        if not user or not user.is_2fa_enabled:
            return None, AuthFlowState.INITIAL
        
        if not self._verify_totp(user.totp_secret, totp_code):
            self._log_audit(user.id, "2fa_verification_failed", {})
            return None, AuthFlowState.TWO_FA_PENDING
        
        # Activate session
        session.access_token = self._generate_token()
        session.refresh_token = self._generate_token()
        session.is_active = True
        user.last_login_at = datetime.utcnow()
        
        self._log_audit(user.id, "2fa_verification_success", {})
        
        return session, AuthFlowState.LOGGED_IN
    
    def enable_2fa(self, user_id: uuid.UUID) -> tuple[str, AuthFlowState]:
        """Enable 2FA for user."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        totp_secret = self._generate_totp_secret()
        user.totp_secret = totp_secret
        user.is_2fa_enabled = True
        
        self._log_audit(user_id, "2fa_enabled", {})
        
        return totp_secret, AuthFlowState.TWO_FA_ENABLED
    
    def request_password_reset(self, email: str) -> tuple[Optional[str], AuthFlowState]:
        """Request password reset."""
        user = self.users_by_email.get(email)
        if not user:
            # Don't reveal if email exists
            return None, AuthFlowState.PASSWORD_RESET_REQUESTED
        
        token = MockPasswordResetToken(
            user_id=user.id,
            token=self._generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        self.reset_tokens[token.token] = token
        
        self._log_audit(user.id, "password_reset_requested", {})
        
        return token.token, AuthFlowState.PASSWORD_RESET_REQUESTED
    
    def reset_password(self, token: str, new_password: str) -> tuple[bool, AuthFlowState]:
        """Reset password using token."""
        reset_token = self.reset_tokens.get(token)
        if not reset_token:
            return False, AuthFlowState.INITIAL
        
        if reset_token.is_used:
            return False, AuthFlowState.INITIAL
        
        if reset_token.expires_at < datetime.utcnow():
            return False, AuthFlowState.INITIAL
        
        if not self._validate_password(new_password):
            raise ValueError("Password does not meet policy requirements")
        
        user = self.users.get(reset_token.user_id)
        if not user:
            return False, AuthFlowState.INITIAL
        
        user.password_hash = self._hash_password(new_password)
        reset_token.is_used = True
        
        self._log_audit(user.id, "password_reset_completed", {})
        
        return True, AuthFlowState.PASSWORD_RESET_COMPLETED
    
    def logout(self, session_id: uuid.UUID) -> AuthFlowState:
        """Logout and invalidate session."""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            self._log_audit(session.user_id, "logout", {})
        
        return AuthFlowState.LOGGED_OUT
    
    def refresh_session(self, refresh_token: str) -> Optional[MockSession]:
        """Refresh session using refresh token."""
        for session in self.sessions.values():
            if session.refresh_token == refresh_token and session.is_active:
                session.access_token = self._generate_token()
                session.expires_at = datetime.utcnow() + timedelta(hours=1)
                return session
        return None
    
    def _create_session(self, user: MockUser) -> MockSession:
        """Create a new session for user."""
        session = MockSession(
            user_id=user.id,
            access_token=self._generate_token(),
            refresh_token=self._generate_token(),
            is_active=True,
        )
        self.sessions[session.id] = session
        return session
    
    def _validate_password(self, password: str) -> bool:
        """Validate password meets policy."""
        if len(password) < 8:
            return False
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_upper and has_lower and has_digit
    
    def _hash_password(self, password: str) -> str:
        """Hash password (mock)."""
        return f"hashed_{password}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash (mock)."""
        return password_hash == f"hashed_{password}"
    
    def _generate_token(self) -> str:
        """Generate a random token."""
        return str(uuid.uuid4())
    
    def _generate_totp_secret(self) -> str:
        """Generate TOTP secret."""
        return str(uuid.uuid4())[:16].upper()
    
    def _verify_totp(self, secret: Optional[str], code: str) -> bool:
        """Verify TOTP code (mock - accepts 6-digit codes)."""
        if not secret:
            return False
        return len(code) == 6 and code.isdigit()
    
    def _log_audit(self, user_id: uuid.UUID, action: str, details: dict) -> None:
        """Log audit entry."""
        self.audit_logs.append({
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow(),
        })


# Strategies
email_strategy = st.emails()
name_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "Zs")))
# Password must be 8+ chars with uppercase, lowercase, and digit
valid_password_strategy = st.from_regex(r"[A-Z][a-z]{5,}[0-9]{2,}", fullmatch=True)
invalid_password_strategy = st.text(min_size=1, max_size=7)  # Too short
totp_code_strategy = st.from_regex(r"[0-9]{6}", fullmatch=True)


class TestCompleteAuthFlow:
    """End-to-end tests for complete authentication flows."""

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_registration_to_login_flow(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test complete registration to login flow.
        
        **Validates: Requirements 1.1, 1.4**
        """
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        # Step 1: Register
        user, state = service.register(email, password, name)
        assert state == AuthFlowState.REGISTERED
        assert user.email == email
        
        # Step 2: Login
        session, state = service.login(email, password)
        assert state == AuthFlowState.LOGGED_IN
        assert session is not None
        assert session.is_active
        assert session.access_token != ""
        
        # Verify audit logs
        assert len(service.audit_logs) >= 2
        assert service.audit_logs[0]["action"] == "user_registered"
        assert service.audit_logs[1]["action"] == "login_success"

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
        totp_code=totp_code_strategy,
    )
    @settings(max_examples=50)
    def test_registration_with_2fa_flow(
        self,
        email: str,
        password: str,
        name: str,
        totp_code: str,
    ) -> None:
        """Test registration with 2FA setup and login.
        
        **Validates: Requirements 1.1, 1.2**
        """
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        # Step 1: Register
        user, _ = service.register(email, password, name)
        
        # Step 2: Login (no 2FA yet)
        session, state = service.login(email, password)
        assert state == AuthFlowState.LOGGED_IN
        
        # Step 3: Enable 2FA
        totp_secret, state = service.enable_2fa(user.id)
        assert state == AuthFlowState.TWO_FA_ENABLED
        assert totp_secret is not None
        
        # Step 4: Logout
        service.logout(session.id)
        
        # Step 5: Login again (now requires 2FA)
        session2, state = service.login(email, password)
        assert state == AuthFlowState.TWO_FA_PENDING
        assert session2 is not None
        assert not session2.is_active
        
        # Step 6: Verify 2FA
        session3, state = service.verify_2fa(session2.id, totp_code)
        assert state == AuthFlowState.LOGGED_IN
        assert session3 is not None
        assert session3.is_active

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        new_password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_password_reset_flow(
        self,
        email: str,
        password: str,
        new_password: str,
        name: str,
    ) -> None:
        """Test complete password reset flow.
        
        **Validates: Requirements 1.5**
        """
        assume(len(name.strip()) > 0)
        assume(password != new_password)
        
        service = MockAuthFlowService()
        
        # Step 1: Register
        service.register(email, password, name)
        
        # Step 2: Request password reset
        token, state = service.request_password_reset(email)
        assert state == AuthFlowState.PASSWORD_RESET_REQUESTED
        assert token is not None
        
        # Step 3: Reset password
        success, state = service.reset_password(token, new_password)
        assert success
        assert state == AuthFlowState.PASSWORD_RESET_COMPLETED
        
        # Step 4: Login with new password
        session, state = service.login(email, new_password)
        assert state == AuthFlowState.LOGGED_IN
        
        # Step 5: Old password should not work
        session2, state = service.login(email, password)
        assert state == AuthFlowState.INITIAL
        assert session2 is None

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_session_refresh_flow(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test session refresh flow.
        
        **Validates: Requirements 1.1**
        """
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        # Register and login
        service.register(email, password, name)
        session, _ = service.login(email, password)
        
        original_access_token = session.access_token
        refresh_token = session.refresh_token
        
        # Refresh session
        refreshed = service.refresh_session(refresh_token)
        assert refreshed is not None
        assert refreshed.access_token != original_access_token
        assert refreshed.is_active

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_logout_invalidates_session(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test that logout properly invalidates session.
        
        **Validates: Requirements 1.1**
        """
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        # Register and login
        service.register(email, password, name)
        session, _ = service.login(email, password)
        
        assert session.is_active
        
        # Logout
        state = service.logout(session.id)
        assert state == AuthFlowState.LOGGED_OUT
        assert not session.is_active
        
        # Refresh should fail
        refreshed = service.refresh_session(session.refresh_token)
        assert refreshed is None


class TestAuthFlowErrorScenarios:
    """Test error scenarios in authentication flows."""

    @given(
        email=email_strategy,
        password=invalid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_registration_with_weak_password_fails(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test that weak passwords are rejected.
        
        **Validates: Requirements 1.4**
        """
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        with pytest.raises(ValueError, match="Password does not meet policy"):
            service.register(email, password, name)

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_duplicate_registration_fails(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test that duplicate email registration fails."""
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        # First registration succeeds
        service.register(email, password, name)
        
        # Second registration fails
        with pytest.raises(ValueError, match="Email already registered"):
            service.register(email, password, name)

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        wrong_password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_login_with_wrong_password_fails(
        self,
        email: str,
        password: str,
        wrong_password: str,
        name: str,
    ) -> None:
        """Test that wrong password login fails."""
        assume(len(name.strip()) > 0)
        assume(password != wrong_password)
        
        service = MockAuthFlowService()
        
        service.register(email, password, name)
        
        session, state = service.login(email, wrong_password)
        assert state == AuthFlowState.INITIAL
        assert session is None

    @given(email=email_strategy)
    @settings(max_examples=50)
    def test_password_reset_for_nonexistent_email(self, email: str) -> None:
        """Test password reset for non-existent email doesn't reveal info."""
        service = MockAuthFlowService()
        
        # Should not reveal if email exists
        token, state = service.request_password_reset(email)
        assert state == AuthFlowState.PASSWORD_RESET_REQUESTED
        # Token is None but state is same to not reveal email existence
        assert token is None

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_expired_reset_token_fails(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test that expired reset tokens are rejected."""
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        service.register(email, password, name)
        token, _ = service.request_password_reset(email)
        
        # Expire the token
        reset_token = service.reset_tokens[token]
        reset_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        success, state = service.reset_password(token, "NewPass123")
        assert not success
        assert state == AuthFlowState.INITIAL

    @given(
        email=email_strategy,
        password=valid_password_strategy,
        name=name_strategy,
    )
    @settings(max_examples=50)
    def test_used_reset_token_fails(
        self,
        email: str,
        password: str,
        name: str,
    ) -> None:
        """Test that used reset tokens cannot be reused."""
        assume(len(name.strip()) > 0)
        
        service = MockAuthFlowService()
        
        service.register(email, password, name)
        token, _ = service.request_password_reset(email)
        
        # Use the token
        service.reset_password(token, "NewPass123")
        
        # Try to use again
        success, state = service.reset_password(token, "AnotherPass456")
        assert not success
        assert state == AuthFlowState.INITIAL
