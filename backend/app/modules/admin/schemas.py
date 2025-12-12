"""Pydantic schemas for Admin module.

Requirements: 1.1, 1.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6 - Admin Authentication & User Management
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, EmailStr

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


# ==================== User Management Schemas (Requirements 3.1-3.6) ====================

from enum import Enum


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserFilters(BaseModel):
    """Filters for user list query."""
    status: Optional[str] = Field(None, description="Filter by status (active, suspended, pending)")
    plan: Optional[str] = Field(None, description="Filter by subscription plan")
    search: Optional[str] = Field(None, description="Search by email or name")
    registered_after: Optional[datetime] = Field(None, description="Filter by registration date")
    registered_before: Optional[datetime] = Field(None, description="Filter by registration date")


class SubscriptionInfo(BaseModel):
    """Subscription information for user detail."""
    id: Optional[uuid.UUID] = None
    plan_name: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None


class YouTubeAccountSummary(BaseModel):
    """Summary of connected YouTube account."""
    id: uuid.UUID
    channel_id: str
    channel_name: str
    subscriber_count: Optional[int] = None
    is_active: bool


class UsageStats(BaseModel):
    """User usage statistics."""
    total_videos: int = 0
    total_streams: int = 0
    storage_used_gb: float = 0.0
    bandwidth_used_gb: float = 0.0
    ai_generations_used: int = 0


class ActivityLog(BaseModel):
    """User activity log entry."""
    id: uuid.UUID
    action: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime


class UserSummary(BaseModel):
    """Summary user info for list view."""
    id: uuid.UUID
    email: str
    name: str
    status: str
    is_active: bool
    plan_name: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    warning_count: int = 0

    class Config:
        from_attributes = True


class UserDetail(BaseModel):
    """Detailed user information for admin view.
    
    Requirements: 3.2 - Show profile info, subscription, connected accounts, usage stats, activity history
    """
    id: uuid.UUID
    email: str
    name: str
    status: str
    is_active: bool
    is_2fa_enabled: bool
    subscription: Optional[SubscriptionInfo] = None
    connected_accounts: list[YouTubeAccountSummary] = Field(default_factory=list)
    usage_stats: UsageStats = Field(default_factory=UsageStats)
    activity_history: list[ActivityLog] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    warning_count: int = 0

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response.
    
    Requirements: 3.1 - Paginated list with search, filter by status, plan, registration date
    """
    items: list[UserSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserSuspendRequest(BaseModel):
    """Request to suspend a user.
    
    Requirements: 3.3 - Suspend user with reason
    """
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for suspension")


class UserSuspendResponse(BaseModel):
    """Response after suspending a user."""
    user_id: uuid.UUID
    status: str
    suspended_at: datetime
    reason: str
    jobs_paused: int
    notification_sent: bool


class UserActivateResponse(BaseModel):
    """Response after activating a user.
    
    Requirements: 3.4 - Activate suspended user
    """
    user_id: uuid.UUID
    status: str
    activated_at: datetime
    jobs_resumed: int


class ImpersonationSession(BaseModel):
    """Impersonation session info.
    
    Requirements: 3.5 - Create temporary session for support purposes
    """
    session_id: uuid.UUID
    admin_id: uuid.UUID
    user_id: uuid.UUID
    access_token: str
    expires_at: datetime
    audit_log_id: uuid.UUID


class ImpersonateRequest(BaseModel):
    """Request to impersonate a user."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for impersonation")


class ImpersonateResponse(BaseModel):
    """Response after starting impersonation."""
    session: ImpersonationSession
    message: str


class PasswordResetResponse(BaseModel):
    """Response after admin-initiated password reset.
    
    Requirements: 3.6 - Send secure reset link to user email
    """
    user_id: uuid.UUID
    email: str
    reset_link_sent: bool
    expires_at: datetime


class UserWarning(BaseModel):
    """User warning record."""
    id: uuid.UUID
    user_id: uuid.UUID
    admin_id: uuid.UUID
    reason: str
    warning_number: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Admin Billing Schemas (Requirements 4.1-4.5) ====================


class AdminSubscriptionFilters(BaseModel):
    """Filters for admin subscription list query."""
    plan: Optional[str] = Field(None, description="Filter by plan tier")
    status: Optional[str] = Field(None, description="Filter by subscription status")
    user_search: Optional[str] = Field(None, description="Search by user email or name")


class AdminSubscriptionResponse(BaseModel):
    """Admin subscription response with user info.
    
    Requirements: 4.1 - Display all subscriptions with user, plan, status, dates
    """
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    plan_tier: str
    status: str
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminSubscriptionListResponse(BaseModel):
    """Paginated admin subscription list response."""
    items: list[AdminSubscriptionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade a subscription.
    
    Requirements: 4.2 - Upgrade subscription with prorated billing
    """
    new_plan: str = Field(..., description="New plan tier to upgrade to")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for upgrade")


class SubscriptionDowngradeRequest(BaseModel):
    """Request to downgrade a subscription.
    
    Requirements: 4.2 - Downgrade subscription with prorated billing
    """
    new_plan: str = Field(..., description="New plan tier to downgrade to")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for downgrade")


class SubscriptionExtendRequest(BaseModel):
    """Request to extend a subscription.
    
    Requirements: 4.3 - Add days to subscription without additional charge
    """
    days: int = Field(..., ge=1, le=365, description="Number of days to add")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for extension")


class RefundRequest(BaseModel):
    """Request to process a refund.
    
    Requirements: 4.4 - Process refund through original payment gateway
    """
    amount: Optional[float] = Field(None, gt=0, description="Partial refund amount (full refund if None)")
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for refund")


class RefundResponse(BaseModel):
    """Response after processing a refund."""
    refund_id: str
    payment_id: uuid.UUID
    amount: float
    currency: str
    status: str
    gateway: str
    processed_at: datetime


class RevenueByPlan(BaseModel):
    """Revenue breakdown by plan."""
    plan: str
    revenue: float
    transaction_count: int


class RevenueByGateway(BaseModel):
    """Revenue breakdown by payment gateway."""
    gateway: str
    revenue: float
    transaction_count: int


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response.
    
    Requirements: 4.5 - Display MRR, ARR, revenue by plan, revenue by gateway, refund rate
    """
    mrr: float = Field(..., description="Monthly Recurring Revenue")
    arr: float = Field(..., description="Annual Recurring Revenue")
    total_revenue: float = Field(..., description="Total revenue in period")
    total_refunds: float = Field(..., description="Total refunds in period")
    refund_rate: float = Field(..., description="Refund rate percentage")
    refund_count: int = Field(..., description="Number of refunds")
    growth_rate: float = Field(..., description="Revenue growth rate vs previous period")
    revenue_by_plan: list[RevenueByPlan]
    revenue_by_gateway: list[RevenueByGateway]
    period_start: datetime
    period_end: datetime


# ==================== Discount Code Schemas (Requirements 14.1, 14.2) ====================


class DiscountCodeCreate(BaseModel):
    """Request to create a discount code.
    
    Requirements: 14.1 - Create discount code with percentage or fixed discount,
    validity period, and usage limit.
    """
    code: str = Field(..., min_length=3, max_length=50, description="Unique discount code")
    discount_type: Literal["percentage", "fixed"] = Field(..., description="Type of discount")
    discount_value: float = Field(..., gt=0, description="Discount value (percentage or fixed amount)")
    valid_from: datetime = Field(..., description="Start date of validity")
    valid_until: datetime = Field(..., description="End date of validity")
    usage_limit: Optional[int] = Field(None, ge=1, description="Maximum number of uses (None for unlimited)")
    applicable_plans: list[str] = Field(default_factory=list, description="Plans this code applies to (empty for all)")


class DiscountCodeUpdate(BaseModel):
    """Request to update a discount code."""
    discount_type: Optional[Literal["percentage", "fixed"]] = Field(None, description="Type of discount")
    discount_value: Optional[float] = Field(None, gt=0, description="Discount value")
    valid_from: Optional[datetime] = Field(None, description="Start date of validity")
    valid_until: Optional[datetime] = Field(None, description="End date of validity")
    usage_limit: Optional[int] = Field(None, ge=1, description="Maximum number of uses")
    applicable_plans: Optional[list[str]] = Field(None, description="Plans this code applies to")
    is_active: Optional[bool] = Field(None, description="Whether the code is active")


class DiscountCodeResponse(BaseModel):
    """Response for a discount code.
    
    Requirements: 14.2 - Display all codes with usage count and revenue impact
    """
    id: uuid.UUID
    code: str
    discount_type: str
    discount_value: float
    valid_from: datetime
    valid_until: datetime
    usage_limit: Optional[int]
    usage_count: int
    applicable_plans: list[str]
    is_active: bool
    is_valid: bool = Field(..., description="Whether the code is currently valid")
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscountCodeListResponse(BaseModel):
    """Paginated list of discount codes."""
    items: list[DiscountCodeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DiscountCodeValidationRequest(BaseModel):
    """Request to validate a discount code."""
    code: str = Field(..., description="Discount code to validate")
    plan: Optional[str] = Field(None, description="Plan to check applicability")


class DiscountCodeValidationResponse(BaseModel):
    """Response for discount code validation."""
    is_valid: bool
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    message: str
