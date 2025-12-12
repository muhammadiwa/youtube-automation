"""API Router for Admin module.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5 - Admin Authentication & Authorization
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Subscription & Revenue Management
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    verify_admin_access,
    verify_super_admin,
    require_permission,
    get_current_user_id,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.schemas import (
    AdminCreate,
    AdminListResponse,
    AdminResponse,
    AdminUpdate,
    AdminAccessVerification,
    Admin2FARequest,
    Admin2FAResponse,
    AdminPermissionCheck,
    AdminPermissionCheckResponse,
)
from app.modules.admin.service import (
    AdminService,
    AdminExistsError,
    AdminNotFoundError,
)
from app.modules.admin.user_service import (
    AdminUserService,
    UserNotFoundError,
    UserAlreadySuspendedError,
    UserNotSuspendedError,
)
from app.modules.admin.schemas import (
    UserFilters,
    UserListResponse,
    UserDetail,
    UserSuspendRequest,
    UserSuspendResponse,
    UserActivateResponse,
    ImpersonateRequest,
    ImpersonateResponse,
    PasswordResetResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Include billing router
from app.modules.admin.billing_router import router as billing_router
router.include_router(billing_router, prefix="", tags=["admin-billing"])

# Include promotional router
from app.modules.admin.promotional_router import router as promotional_router
router.include_router(promotional_router, prefix="/promotions", tags=["admin-promotions"])

# Include moderation router
from app.modules.admin.moderation_router import router as moderation_router
router.include_router(moderation_router, prefix="", tags=["admin-moderation"])

# Include system router
from app.modules.admin.system_router import router as system_router
router.include_router(system_router, prefix="", tags=["admin-system"])

# Include quota router
from app.modules.admin.quota_router import router as quota_router
router.include_router(quota_router, prefix="", tags=["admin-quota"])


# ==================== Admin Access Verification ====================

@router.get("/verify-access", response_model=AdminAccessVerification)
async def verify_admin_access_endpoint(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Verify if current user has admin access.
    
    Requirements: 1.1 - Verify admin role before granting access
    
    Returns 403 for non-admin users.
    """
    service = AdminService(session)
    admin = await service.verify_admin_access(user_id)
    
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges",
        )
    
    return AdminAccessVerification(
        is_admin=True,
        admin_id=admin.id,
        role=admin.role,
        permissions=admin.permissions,
        requires_2fa=True,  # Always require 2FA for admin
    )


@router.post("/verify-2fa", response_model=Admin2FAResponse)
async def verify_admin_2fa(
    request: Request,
    data: Admin2FARequest,
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session),
):
    """Verify 2FA for admin access.
    
    Requirements: 1.2 - Require additional 2FA verification for admin login
    
    All admin logins require TOTP verification regardless of user settings.
    Returns an admin session token that must be included in subsequent requests.
    """
    from app.modules.auth.repository import UserRepository
    from app.modules.auth.totp import verify_totp_code
    from app.modules.auth.audit import AuditLogger, AuditAction
    from app.modules.security.admin_auth import AdminSessionManager
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(admin.user_id)
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify TOTP code - 2FA is mandatory for admin access
    if not user.totp_secret:
        # Log 2FA not set up
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin.user_id,
            details={
                "event": "admin_2fa_not_setup",
                "admin_id": str(admin.id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up for this user. Admin access requires 2FA.",
        )
    
    if not verify_totp_code(user.totp_secret, data.totp_code):
        # Log failed 2FA attempt
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin.user_id,
            details={
                "event": "admin_2fa_failed",
                "admin_id": str(admin.id),
                "reason": "invalid_totp_code",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code",
        )
    
    # Create admin session - proves 2FA was completed
    admin_session = AdminSessionManager.create_session(
        user_id=admin.user_id,
        action="admin_access",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Log successful 2FA verification
    AuditLogger.log(
        action=AuditAction.ADMIN_ACTION,
        user_id=admin.user_id,
        details={
            "event": "admin_2fa_verified",
            "admin_id": str(admin.id),
            "session_expires_at": admin_session.expires_at.isoformat(),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Update last login
    service = AdminService(session)
    await service.update_last_login(
        admin,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return Admin2FAResponse(
        verified=True,
        admin_session_token=admin_session.token,
        expires_at=admin_session.expires_at,
    )


# ==================== Admin Management (Super Admin Only) ====================

@router.post("/admins", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    request: Request,
    data: AdminCreate,
    admin: Admin = Depends(verify_super_admin),
    session: AsyncSession = Depends(get_session),
):
    """Create a new admin.
    
    Requirements: 1.4 - Super admin can create new admins with role assignment
    
    Only super admins can create new admins.
    """
    service = AdminService(session)
    
    try:
        return await service.create_admin(
            data=data,
            created_by=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AdminExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/admins", response_model=AdminListResponse)
async def list_admins(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_inactive: bool = Query(False, description="Include inactive admins"),
    admin: Admin = Depends(verify_super_admin),
    session: AsyncSession = Depends(get_session),
):
    """List all admins.
    
    Requirements: 1.5 - Display all admins with roles, last login, status
    
    Only super admins can view admin list.
    """
    service = AdminService(session)
    return await service.get_all_admins(
        page=page,
        page_size=page_size,
        include_inactive=include_inactive,
    )


@router.get("/admins/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: uuid.UUID,
    admin: Admin = Depends(verify_super_admin),
    session: AsyncSession = Depends(get_session),
):
    """Get admin by ID.
    
    Only super admins can view admin details.
    """
    service = AdminService(session)
    
    try:
        return await service.get_admin(admin_id)
    except AdminNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin(
    request: Request,
    admin_id: uuid.UUID,
    data: AdminUpdate,
    admin: Admin = Depends(verify_super_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update admin.
    
    Only super admins can update admin details.
    """
    service = AdminService(session)
    
    try:
        return await service.update_admin(
            admin_id=admin_id,
            data=data,
            updated_by=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AdminNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/admins/{admin_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_admin(
    request: Request,
    admin_id: uuid.UUID,
    admin: Admin = Depends(verify_super_admin),
    session: AsyncSession = Depends(get_session),
):
    """Deactivate an admin.
    
    Only super admins can deactivate admins.
    Cannot deactivate the last super admin.
    """
    service = AdminService(session)
    
    try:
        await service.deactivate_admin(
            admin_id=admin_id,
            deactivated_by=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AdminNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Permission Check ====================

@router.post("/check-permission", response_model=AdminPermissionCheckResponse)
async def check_permission(
    data: AdminPermissionCheck,
    admin: Admin = Depends(verify_admin_access),
):
    """Check if current admin has a specific permission.
    
    Useful for frontend to determine UI visibility.
    """
    return AdminPermissionCheckResponse(
        has_permission=admin.has_permission(data.permission),
        permission=data.permission.value,
        admin_role=admin.role,
    )


# ==================== Current Admin Info ====================

@router.get("/me", response_model=AdminResponse)
async def get_current_admin(
    admin: Admin = Depends(verify_admin_access),
    session: AsyncSession = Depends(get_session),
):
    """Get current admin's information."""
    service = AdminService(session)
    result = await service.get_admin_by_user_id(admin.user_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    
    return result


# ==================== User Management (Requirements 3.1-3.6) ====================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (active, suspended)"),
    plan: Optional[str] = Query(None, description="Filter by subscription plan"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    registered_after: Optional[str] = Query(None, description="Filter by registration date (ISO format)"),
    registered_before: Optional[str] = Query(None, description="Filter by registration date (ISO format)"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """List all users with pagination and filters.
    
    Requirements: 3.1 - Display paginated list with search, filter by status, plan, registration date
    
    Requires VIEW_USERS permission.
    """
    from datetime import datetime
    
    # Parse date filters
    reg_after = None
    reg_before = None
    if registered_after:
        try:
            reg_after = datetime.fromisoformat(registered_after.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registered_after date format",
            )
    if registered_before:
        try:
            reg_before = datetime.fromisoformat(registered_before.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registered_before date format",
            )
    
    filters = UserFilters(
        status=status,
        plan=plan,
        search=search,
        registered_after=reg_after,
        registered_before=reg_before,
    )
    
    service = AdminUserService(session)
    return await service.get_users(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed user information.
    
    Requirements: 3.2 - Show profile info, subscription, connected accounts, usage stats, activity history
    
    Requires VIEW_USERS permission.
    """
    service = AdminUserService(session)
    
    try:
        return await service.get_user_detail(user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/users/{user_id}/suspend", response_model=UserSuspendResponse)
async def suspend_user(
    request: Request,
    user_id: uuid.UUID,
    data: UserSuspendRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Suspend a user account.
    
    Requirements: 3.3 - Disable user access, pause all scheduled jobs, send notification email
    
    Requires MANAGE_USERS permission.
    """
    service = AdminUserService(session)
    
    try:
        return await service.suspend_user(
            user_id=user_id,
            reason=data.reason,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UserAlreadySuspendedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/users/{user_id}/activate", response_model=UserActivateResponse)
async def activate_user(
    request: Request,
    user_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Activate a suspended user account.
    
    Requirements: 3.4 - Restore access and resume paused jobs
    
    Requires MANAGE_USERS permission.
    """
    service = AdminUserService(session)
    
    try:
        return await service.activate_user(
            user_id=user_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UserNotSuspendedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/users/{user_id}/impersonate", response_model=ImpersonateResponse)
async def impersonate_user(
    request: Request,
    user_id: uuid.UUID,
    data: Optional[ImpersonateRequest] = None,
    admin: Admin = Depends(require_permission(AdminPermission.IMPERSONATE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Create an impersonation session for a user.
    
    Requirements: 3.5 - Create temporary session for support purposes with full audit logging
    
    Requires IMPERSONATE_USERS permission.
    """
    service = AdminUserService(session)
    
    try:
        return await service.impersonate_user(
            user_id=user_id,
            admin_id=admin.user_id,
            reason=data.reason if data else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    request: Request,
    user_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Initiate password reset for a user.
    
    Requirements: 3.6 - Send secure reset link to user email
    
    Requires MANAGE_USERS permission.
    """
    service = AdminUserService(session)
    
    try:
        return await service.reset_user_password(
            user_id=user_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== User Warning (Requirements 6.5) ====================

from app.modules.admin.schemas import UserWarnRequest, UserWarnResponse
from app.modules.admin.moderation_service import AdminModerationService
from app.modules.admin.moderation_service import UserNotFoundError as ModerationUserNotFoundError


@router.post("/users/{user_id}/warn", response_model=UserWarnResponse)
async def warn_user(
    request: Request,
    user_id: uuid.UUID,
    data: UserWarnRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Issue a warning to a user.
    
    Requirements: 6.5 - Send warning notification and increment user warning count
    
    Property 11: User Warning Counter
    - Increments user's warning_count by 1
    - Creates a UserWarning record
    
    Requires MANAGE_MODERATION permission.
    """
    service = AdminModerationService(session)
    
    try:
        return await service.warn_user(
            user_id=user_id,
            admin_id=admin.user_id,
            reason=data.reason,
            related_report_id=data.related_report_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ModerationUserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
