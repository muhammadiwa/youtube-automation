"""Authentication module."""

from app.modules.auth.audit import (
    AuditAction,
    AuditLog,
    AuditLogEntry,
    AuditLogger,
    audit_2fa_action,
    audit_login,
    audit_logout,
    audit_password_change,
    audit_sensitive_action,
)
from app.modules.auth.jwt import (
    AuthTokens,
    TokenBlacklist,
    TokenPayload,
    blacklist_token,
    create_access_token,
    create_auth_tokens,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
    validate_token,
)
from app.modules.auth.models import (
    PasswordValidationError,
    User,
    hash_password,
    validate_password_policy,
    verify_password,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.password_reset import PasswordResetStore, PasswordResetToken
from app.modules.auth.service import AuthenticationError, AuthService, UserExistsError
from app.modules.auth.totp import (
    TwoFactorSetup,
    decode_backup_codes,
    encode_backup_codes,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_uri,
    verify_backup_code,
    verify_totp_code,
)

__all__ = [
    # Models
    "User",
    "PasswordValidationError",
    # Password utilities
    "hash_password",
    "verify_password",
    "validate_password_policy",
    # Repository
    "UserRepository",
    # JWT
    "AuthTokens",
    "TokenPayload",
    "TokenBlacklist",
    "create_access_token",
    "create_refresh_token",
    "create_auth_tokens",
    "decode_token",
    "validate_token",
    "blacklist_token",
    "get_user_id_from_token",
    # TOTP / 2FA
    "TwoFactorSetup",
    "generate_totp_secret",
    "get_totp_uri",
    "verify_totp_code",
    "generate_backup_codes",
    "encode_backup_codes",
    "decode_backup_codes",
    "verify_backup_code",
    # Password Reset
    "PasswordResetStore",
    "PasswordResetToken",
    # Audit
    "AuditAction",
    "AuditLog",
    "AuditLogEntry",
    "AuditLogger",
    "audit_login",
    "audit_logout",
    "audit_password_change",
    "audit_2fa_action",
    "audit_sensitive_action",
    # Service
    "AuthService",
    "AuthenticationError",
    "UserExistsError",
]
