"""Pydantic schemas for Admin module.

Requirements: 1.1, 1.4 - Admin Authentication & Authorization
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.admin.models import AdminPermission, AdminRole


class AdminBase(BaseModel):
    """Base schema for Admin."""
    role: AdminRole = Field(default=AdminRole.ADMIN, description="Admin role")
    permissions: list[str] = Field(default_factory=list, description="Admin permissions")
    is_active: bool = Field(default=True, description="Whether admin is active")


class AdminCreate(BaseModel):
    """Schema for creating an admin."""
    user_id: uuid.UUID = Field(..., description="User ID to grant admin access")
    role: AdminRole = Field(default=AdminRole.ADMIN, description="Admin role")
    permissions: Optional[list[str]] = Field(
        default=None, 
        description="Custom permissions (if None, uses default for role)"
    )


class AdminUpdate(BaseModel):
    """Schema for updating an admin."""
    role: Optional[AdminRole] = Field(default=None, description="New admin role")
    permissions: Optional[list[str]] = Field(default=None, description="New permissions")
    is_active: Optional[bool] = Field(default=None, description="Active status")


class AdminResponse(BaseModel):
    """Schema for admin response."""
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    permissions: list[str]
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID]
    
    # User info (populated from join)
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    """Schema for paginated admin list."""
    items: list[AdminResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminAccessVerification(BaseModel):
    """Schema for admin access verification result."""
    is_admin: bool
    admin_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)
    requires_2fa: bool = True


class Admin2FARequest(BaseModel):
    """Schema for admin 2FA verification request."""
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP code")


class Admin2FAResponse(BaseModel):
    """Schema for admin 2FA verification response."""
    verified: bool
    admin_session_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class AdminPermissionCheck(BaseModel):
    """Schema for permission check request."""
    permission: AdminPermission


class AdminPermissionCheckResponse(BaseModel):
    """Schema for permission check response."""
    has_permission: bool
    permission: str
    admin_role: str
