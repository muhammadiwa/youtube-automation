"""Admin authentication module with additional security factor.

Provides enhanced authentication for admin functions per requirement 25.3.

Admin operations require:
1. Valid user session (JWT token)
2. Additional 2FA verification
3. Short-lived admin session token

This ensures sensitive operations have an extra layer of protection.
"""

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from app.modules.auth.audit import AuditLogger, AuditAction


class AdminAction(str, Enum):
    """Actions requiring additional admin authentication."""
    
    # User management
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"
    USER_SUSPEND = "user_suspend"
    
    # System configuration
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    FEATURE_FLAG_TOGGLE = "feature_flag_toggle"
    
    # Security operations
    KEY_ROTATION = "key_rotation"
    SECURITY_SCAN = "security_scan"
    AUDIT_EXPORT = "audit_export"
    
    # Data operations
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    
    # API management
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    WEBHOOK_MANAGE = "webhook_manage"
    
    # Billing operations
    SUBSCRIPTION_CHANGE = "subscription_change"
    REFUND_PROCESS = "refund_process"


@dataclass
class AdminSession:
    """Represents an authenticated admin session."""
    token: str
    user_id: uuid.UUID
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None


class AdminSessionManager:
    """Manages admin session tokens for sensitive operations.
    
    Admin sessions are:
    - Short-lived (15 minutes by default)
    - Single-use (consumed after first use)
    - Action-specific (tied to a specific operation)
    - Audited (all creations and uses are logged)
    """
    
    _sessions: dict[str, AdminSession] = {}
    SESSION_DURATION_MINUTES = 15
    MAX_SESSIONS_PER_USER = 5
    
    @classmethod
    def create_session(
        cls,
        user_id: uuid.UUID,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminSession:
        """Create a new admin session.
        
        Args:
            user_id: User ID for the session
            action: The admin action being authorized
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AdminSession: The created session
        """
        # Clean up old sessions for this user
        cls._cleanup_user_sessions(user_id)
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=cls.SESSION_DURATION_MINUTES)
        
        session = AdminSession(
            token=token,
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            expires_at=expires_at,
        )
        
        cls._sessions[token] = session
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=user_id,
            details={
                "event": "admin_session_created",
                "admin_action": action,
                "expires_at": expires_at.isoformat(),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return session
    
    @classmethod
    def validate_session(
        cls,
        token: str,
        user_id: uuid.UUID,
        action: Optional[str] = None,
        consume: bool = True,
    ) -> tuple[bool, Optional[str]]:
        """Validate an admin session token.
        
        Args:
            token: Session token to validate
            user_id: Expected user ID
            action: Optional action to validate against
            consume: Whether to mark session as used
            
        Returns:
            tuple: (is_valid, error_message)
        """
        session = cls._sessions.get(token)
        
        if not session:
            return False, "Invalid session token"
        
        # Check expiration
        if datetime.utcnow() > session.expires_at:
            del cls._sessions[token]
            return False, "Session expired"
        
        # Check if already used
        if session.used:
            return False, "Session already used"
        
        # Check user ID
        if session.user_id != user_id:
            return False, "Session user mismatch"
        
        # Check action if specified
        if action and session.action != action:
            return False, f"Session not authorized for action: {action}"
        
        # Mark as used if consuming
        if consume:
            session.used = True
            session.used_at = datetime.utcnow()
            
            # Audit log
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=user_id,
                details={
                    "event": "admin_session_used",
                    "admin_action": session.action,
                },
                ip_address=session.ip_address,
                user_agent=session.user_agent,
            )
        
        return True, None
    
    @classmethod
    def revoke_session(cls, token: str) -> bool:
        """Revoke an admin session.
        
        Args:
            token: Session token to revoke
            
        Returns:
            bool: True if session was revoked
        """
        if token in cls._sessions:
            session = cls._sessions[token]
            
            # Audit log
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=session.user_id,
                details={
                    "event": "admin_session_revoked",
                    "admin_action": session.action,
                },
                ip_address=session.ip_address,
            )
            
            del cls._sessions[token]
            return True
        return False
    
    @classmethod
    def revoke_all_user_sessions(cls, user_id: uuid.UUID) -> int:
        """Revoke all admin sessions for a user.
        
        Args:
            user_id: User ID to revoke sessions for
            
        Returns:
            int: Number of sessions revoked
        """
        tokens_to_revoke = [
            token for token, session in cls._sessions.items()
            if session.user_id == user_id
        ]
        
        for token in tokens_to_revoke:
            cls.revoke_session(token)
        
        return len(tokens_to_revoke)
    
    @classmethod
    def get_user_sessions(cls, user_id: uuid.UUID) -> list[AdminSession]:
        """Get all active sessions for a user.
        
        Args:
            user_id: User ID to get sessions for
            
        Returns:
            list: Active admin sessions
        """
        now = datetime.utcnow()
        return [
            session for session in cls._sessions.values()
            if session.user_id == user_id
            and session.expires_at > now
            and not session.used
        ]
    
    @classmethod
    def _cleanup_user_sessions(cls, user_id: uuid.UUID) -> None:
        """Clean up expired and excess sessions for a user.
        
        Args:
            user_id: User ID to clean up sessions for
        """
        now = datetime.utcnow()
        
        # Remove expired sessions
        expired = [
            token for token, session in cls._sessions.items()
            if session.expires_at < now
        ]
        for token in expired:
            del cls._sessions[token]
        
        # Remove excess sessions for user (keep most recent)
        user_sessions = [
            (token, session) for token, session in cls._sessions.items()
            if session.user_id == user_id and not session.used
        ]
        
        if len(user_sessions) >= cls.MAX_SESSIONS_PER_USER:
            # Sort by creation time, remove oldest
            user_sessions.sort(key=lambda x: x[1].created_at)
            for token, _ in user_sessions[:-cls.MAX_SESSIONS_PER_USER + 1]:
                del cls._sessions[token]
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove all expired sessions.
        
        Returns:
            int: Number of sessions removed
        """
        now = datetime.utcnow()
        expired = [
            token for token, session in cls._sessions.items()
            if session.expires_at < now
        ]
        for token in expired:
            del cls._sessions[token]
        return len(expired)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all sessions (for testing)."""
        cls._sessions.clear()


async def verify_admin_authentication(
    user_id: uuid.UUID,
    totp_code: str,
    action: str,
    totp_secret: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[bool, Optional[AdminSession], Optional[str]]:
    """Verify admin authentication with 2FA.
    
    Args:
        user_id: User ID requesting admin access
        totp_code: TOTP code for verification
        action: Admin action being requested
        totp_secret: User's TOTP secret
        ip_address: Client IP address
        user_agent: Client user agent
        
    Returns:
        tuple: (success, session, error_message)
    """
    from app.modules.auth.totp import verify_totp_code
    
    # Verify TOTP code
    if not verify_totp_code(totp_secret, totp_code):
        # Audit failed attempt
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=user_id,
            details={
                "event": "admin_auth_failed",
                "admin_action": action,
                "reason": "invalid_totp",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return False, None, "Invalid 2FA code"
    
    # Create admin session
    session = AdminSessionManager.create_session(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return True, session, None


def require_admin_session(
    token: str,
    user_id: uuid.UUID,
    action: str,
) -> tuple[bool, Optional[str]]:
    """Decorator helper to require admin session for an operation.
    
    Args:
        token: Admin session token
        user_id: User ID performing the action
        action: Action being performed
        
    Returns:
        tuple: (is_valid, error_message)
    """
    return AdminSessionManager.validate_session(
        token=token,
        user_id=user_id,
        action=action,
        consume=True,
    )


# List of actions that require admin authentication
ADMIN_REQUIRED_ACTIONS = [
    AdminAction.USER_DELETE,
    AdminAction.USER_ROLE_CHANGE,
    AdminAction.SYSTEM_CONFIG_CHANGE,
    AdminAction.KEY_ROTATION,
    AdminAction.AUDIT_EXPORT,
    AdminAction.BACKUP_RESTORE,
    AdminAction.DATA_DELETE,
    AdminAction.API_KEY_REVOKE,
    AdminAction.SUBSCRIPTION_CHANGE,
    AdminAction.REFUND_PROCESS,
]


def is_admin_action_required(action: str) -> bool:
    """Check if an action requires admin authentication.
    
    Args:
        action: Action to check
        
    Returns:
        bool: True if admin auth is required
    """
    try:
        admin_action = AdminAction(action)
        return admin_action in ADMIN_REQUIRED_ACTIONS
    except ValueError:
        return False
