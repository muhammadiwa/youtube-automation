"""Admin middleware for role verification.

Requirements: 1.1, 1.2 - Admin role verification and 2FA enforcement
"""

import uuid
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.repository import AdminRepository
from app.modules.auth.jwt import validate_token
from app.modules.auth.audit import AuditLogger, AuditAction, AuditLog


async def log_audit_to_db(
    session: AsyncSession,
    action: AuditAction | str,
    user_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Log audit event to database.
    
    Args:
        session: Database session
        action: Type of action being logged
        user_id: User performing the action
        details: Additional details about the action
        ip_address: Client IP address
        user_agent: Client user agent string
    """
    action_str = action.value if isinstance(action, AuditAction) else action
    
    db_log = AuditLog(
        user_id=user_id,
        action=action_str,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    session.add(db_log)
    # Don't commit here - let the caller handle transaction
    # Also log to in-memory for backward compatibility
    AuditLogger.log(
        action=action,
        user_id=user_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


security = HTTPBearer()


# Header name for admin session token (proves 2FA was completed)
ADMIN_SESSION_HEADER = "X-Admin-Session"


class AdminAccessDenied(HTTPException):
    """Exception raised when admin access is denied."""
    
    def __init__(self, detail: str = "Admin access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class Admin2FARequired(HTTPException):
    """Exception raised when admin 2FA is required."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin 2FA verification required",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    """Extract user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        uuid.UUID: User ID from token
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = validate_token(token, "access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return uuid.UUID(payload.sub)


async def verify_admin_access(
    request: Request,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> Admin:
    """Verify that the current user has admin access.
    
    Requirements: 1.1 - Verify admin role before granting access
    
    Args:
        request: FastAPI request object
        user_id: Current user ID from token
        session: Database session
        
    Returns:
        Admin: Admin instance if verified
        
    Raises:
        AdminAccessDenied: If user is not an admin or is inactive
    """
    repo = AdminRepository(session)
    admin = await repo.get_by_user_id(user_id)
    
    if admin is None:
        # Log failed access attempt to database
        await log_audit_to_db(
            session=session,
            action=AuditAction.ADMIN_ACTION,
            user_id=user_id,
            details={
                "event": "admin_access_denied",
                "reason": "not_admin",
                "path": str(request.url.path),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await session.commit()
        raise AdminAccessDenied("User does not have admin privileges")
    
    if not admin.is_active:
        # Log failed access attempt to database
        await log_audit_to_db(
            session=session,
            action=AuditAction.ADMIN_ACTION,
            user_id=user_id,
            details={
                "event": "admin_access_denied",
                "reason": "admin_inactive",
                "admin_id": str(admin.id),
                "path": str(request.url.path),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await session.commit()
        raise AdminAccessDenied("Admin account is inactive")
    
    return admin


async def verify_super_admin(
    admin: Admin = Depends(verify_admin_access),
) -> Admin:
    """Verify that the current admin is a super admin.
    
    Args:
        admin: Admin instance from verify_admin_access
        
    Returns:
        Admin: Admin instance if super admin
        
    Raises:
        AdminAccessDenied: If admin is not a super admin
    """
    if not admin.is_super_admin:
        raise AdminAccessDenied("Super admin privileges required")
    
    return admin


def require_super_admin():
    """Dependency factory for requiring super admin privileges.
    
    Returns:
        Dependency function that verifies super admin status
    """
    async def verify_super_admin_permission(
        request: Request,
        admin: Admin = Depends(verify_admin_access),
    ) -> Admin:
        """Verify admin is a super admin.
        
        Args:
            request: FastAPI request object
            admin: Admin instance
            
        Returns:
            Admin: Admin instance if super admin
            
        Raises:
            AdminAccessDenied: If admin is not a super admin
        """
        if not admin.is_super_admin:
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=admin.user_id,
                details={
                    "event": "super_admin_required",
                    "admin_id": str(admin.id),
                    "path": str(request.url.path),
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise AdminAccessDenied("Super admin privileges required")
        
        return admin
    
    return verify_super_admin_permission


def require_permission(permission: AdminPermission):
    """Dependency factory for requiring specific admin permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function that verifies the permission
    """
    async def verify_permission(
        request: Request,
        admin: Admin = Depends(verify_admin_access),
        session: AsyncSession = Depends(get_session),
    ) -> Admin:
        """Verify admin has the required permission.
        
        Args:
            request: FastAPI request object
            admin: Admin instance
            session: Database session
            
        Returns:
            Admin: Admin instance if permission verified
            
        Raises:
            AdminAccessDenied: If admin lacks the permission
        """
        if not admin.has_permission(permission):
            await log_audit_to_db(
                session=session,
                action=AuditAction.ADMIN_ACTION,
                user_id=admin.user_id,
                details={
                    "event": "permission_denied",
                    "required_permission": permission.value,
                    "admin_permissions": admin.permissions,
                    "path": str(request.url.path),
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            await session.commit()
            raise AdminAccessDenied(f"Permission '{permission.value}' required")
        
        return admin
    
    return verify_permission


def require_any_permission(permissions: list[AdminPermission]):
    """Dependency factory for requiring any of the specified permissions.
    
    Args:
        permissions: List of acceptable permissions
        
    Returns:
        Dependency function that verifies at least one permission
    """
    async def verify_any_permission(
        request: Request,
        admin: Admin = Depends(verify_admin_access),
    ) -> Admin:
        """Verify admin has at least one of the required permissions.
        
        Args:
            request: FastAPI request object
            admin: Admin instance
            
        Returns:
            Admin: Admin instance if any permission verified
            
        Raises:
            AdminAccessDenied: If admin lacks all permissions
        """
        if not admin.has_any_permission(permissions):
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=admin.user_id,
                details={
                    "event": "permission_denied",
                    "required_permissions": [p.value for p in permissions],
                    "admin_permissions": admin.permissions,
                    "path": str(request.url.path),
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise AdminAccessDenied(
                f"One of these permissions required: {[p.value for p in permissions]}"
            )
        
        return admin
    
    return verify_any_permission


async def verify_admin_2fa_session(
    request: Request,
    admin: Admin = Depends(verify_admin_access),
    admin_session_token: Optional[str] = Header(None, alias=ADMIN_SESSION_HEADER),
) -> Admin:
    """Verify that admin has completed 2FA verification.
    
    Requirements: 1.2 - Require additional 2FA verification for admin login
    
    This dependency ensures that the admin has a valid admin session token,
    which is only issued after successful 2FA verification.
    
    Args:
        request: FastAPI request object
        admin: Admin instance from verify_admin_access
        admin_session_token: Admin session token from header
        
    Returns:
        Admin: Admin instance if 2FA verified
        
    Raises:
        Admin2FARequired: If 2FA verification is required
        AdminAccessDenied: If session is invalid
    """
    from app.modules.security.admin_auth import AdminSessionManager
    
    if admin_session_token is None:
        # Log 2FA required
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin.user_id,
            details={
                "event": "admin_2fa_required",
                "admin_id": str(admin.id),
                "path": str(request.url.path),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        raise Admin2FARequired()
    
    # Validate the admin session token (don't consume it - allow reuse within session)
    is_valid, error_message = AdminSessionManager.validate_session(
        token=admin_session_token,
        user_id=admin.user_id,
        consume=False,  # Don't consume - allow multiple operations per session
    )
    
    if not is_valid:
        # Log invalid session
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin.user_id,
            details={
                "event": "admin_session_invalid",
                "admin_id": str(admin.id),
                "error": error_message,
                "path": str(request.url.path),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        raise AdminAccessDenied(f"Invalid admin session: {error_message}")
    
    return admin


def require_2fa_and_permission(permission: AdminPermission):
    """Dependency factory for requiring 2FA and specific permission.
    
    Requirements: 1.2 - Require 2FA for sensitive admin operations
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function that verifies 2FA and permission
    """
    async def verify_2fa_and_permission(
        request: Request,
        admin: Admin = Depends(verify_admin_2fa_session),
    ) -> Admin:
        """Verify admin has completed 2FA and has the required permission.
        
        Args:
            request: FastAPI request object
            admin: Admin instance (already 2FA verified)
            
        Returns:
            Admin: Admin instance if permission verified
            
        Raises:
            AdminAccessDenied: If admin lacks the permission
        """
        if not admin.has_permission(permission):
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=admin.user_id,
                details={
                    "event": "permission_denied",
                    "required_permission": permission.value,
                    "admin_permissions": admin.permissions,
                    "path": str(request.url.path),
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            raise AdminAccessDenied(f"Permission '{permission.value}' required")
        
        return admin
    
    return verify_2fa_and_permission
