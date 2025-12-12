"""Admin models for database entities.

Requirements: 1.1, 1.4 - Admin Authentication & Authorization
Requirements: 14.1 - Promotional Tools (Discount Codes)
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DiscountType(str, Enum):
    """Discount code types.
    
    Requirements: 14.1 - Percentage or fixed discount
    """
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class AdminRole(str, Enum):
    """Admin role types."""
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AdminPermission(str, Enum):
    """Admin permission types."""
    # User management
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    IMPERSONATE_USERS = "impersonate_users"
    
    # Billing management
    VIEW_BILLING = "view_billing"
    MANAGE_BILLING = "manage_billing"
    PROCESS_REFUNDS = "process_refunds"
    
    # System management
    VIEW_SYSTEM = "view_system"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_CONFIG = "manage_config"
    
    # Moderation
    VIEW_MODERATION = "view_moderation"
    MANAGE_MODERATION = "manage_moderation"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    
    # Compliance
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_COMPLIANCE = "manage_compliance"
    
    # Admin management (super_admin only)
    MANAGE_ADMINS = "manage_admins"


# Default permissions per role
DEFAULT_PERMISSIONS = {
    AdminRole.ADMIN: [
        AdminPermission.VIEW_USERS,
        AdminPermission.MANAGE_USERS,
        AdminPermission.VIEW_BILLING,
        AdminPermission.VIEW_SYSTEM,
        AdminPermission.VIEW_MODERATION,
        AdminPermission.MANAGE_MODERATION,
        AdminPermission.VIEW_ANALYTICS,
        AdminPermission.VIEW_AUDIT_LOGS,
    ],
    AdminRole.SUPER_ADMIN: [p for p in AdminPermission],  # All permissions
}


class Admin(Base):
    """Admin model for administrative users.
    
    Requirements: 1.1, 1.4 - Admin role verification and management
    """

    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AdminRole.ADMIN.value
    )
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    def has_permission(self, permission: AdminPermission) -> bool:
        """Check if admin has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if admin has the permission
        """
        return permission.value in self.permissions
    
    def has_any_permission(self, permissions: list[AdminPermission]) -> bool:
        """Check if admin has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if admin has any of the permissions
        """
        return any(p.value in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: list[AdminPermission]) -> bool:
        """Check if admin has all of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if admin has all of the permissions
        """
        return all(p.value in self.permissions for p in permissions)
    
    @property
    def is_super_admin(self) -> bool:
        """Check if admin is a super admin."""
        return self.role == AdminRole.SUPER_ADMIN.value


class DiscountCode(Base):
    """Discount code model for promotional campaigns.
    
    Requirements: 14.1 - Create discount codes with percentage or fixed discount,
    validity period, and usage limit.
    
    Property 15: Discount Code Validation
    - Code is valid only if current_date is between valid_from and valid_until
    - Code is valid only if usage_count < usage_limit (when usage_limit is set)
    """

    __tablename__ = "discount_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DiscountType.PERCENTAGE.value
    )
    discount_value: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    applicable_plans: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def is_valid(self, current_date: Optional[datetime] = None) -> bool:
        """Check if discount code is currently valid.
        
        Property 15: Discount Code Validation
        - Code is valid only if current_date is between valid_from and valid_until
        - Code is valid only if usage_count < usage_limit (when usage_limit is set)
        
        Args:
            current_date: Date to check validity against (defaults to now)
            
        Returns:
            bool: True if code is valid
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Check if code is active
        if not self.is_active:
            return False
        
        # Check date validity
        if current_date < self.valid_from or current_date > self.valid_until:
            return False
        
        # Check usage limit
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        
        return True

    def calculate_discount(self, original_price: float) -> float:
        """Calculate the discounted price.
        
        Args:
            original_price: Original price before discount
            
        Returns:
            float: Discount amount
        """
        if self.discount_type == DiscountType.PERCENTAGE.value:
            return original_price * (self.discount_value / 100)
        else:  # FIXED
            return min(self.discount_value, original_price)
