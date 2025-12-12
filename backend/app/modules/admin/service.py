"""Admin service for business logic.

Requirements: 1.1, 1.2, 1.3, 1.4 - Admin Authentication & Authorization
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import Admin, AdminPermission, AdminRole, DEFAULT_PERMISSIONS
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    AdminCreate,
    AdminListResponse,
    AdminResponse,
    AdminUpdate,
)
from app.modules.auth.audit import AuditAction, AuditLogger
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository


class AdminServiceError(Exception):
    """Base exception for admin service errors."""
    pass


class AdminNotFoundError(AdminServiceError):
    """Exception raised when admin is not found."""
    pass


class AdminExistsError(AdminServiceError):
    """Exception raised when admin already exists."""
    pass


class AdminService:
    """Service for admin operations."""

    def __init__(self, session: AsyncSession):
        """Initialize admin service.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.admin_repo = AdminRepository(session)
        self.user_repo = UserRepository(session)

    async def verify_admin_access(self, user_id: uuid.UUID) -> Optional[Admin]:
        """Verify if a user has admin access.
        
        Requirements: 1.1 - Verify admin role before granting access
        
        Args:
            user_id: User ID to verify
            
        Returns:
            Admin | None: Admin instance if user is admin, None otherwise
        """
        admin = await self.admin_repo.get_by_user_id(user_id)
        
        if admin is None or not admin.is_active:
            return None
        
        return admin

    async def create_admin(
        self,
        data: AdminCreate,
        created_by: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminResponse:
        """Create a new admin.
        
        Requirements: 1.4 - Super admin can create new admins with role assignment
        
        Args:
            data: Admin creation data
            created_by: ID of admin creating this admin
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AdminResponse: Created admin
            
        Raises:
            AdminExistsError: If user is already an admin
            ValueError: If user doesn't exist
        """
        # Check if user exists
        user = await self.user_repo.get_by_id(data.user_id)
        if user is None:
            raise ValueError(f"User with ID {data.user_id} not found")
        
        # Check if already admin
        if await self.admin_repo.exists_by_user_id(data.user_id):
            raise AdminExistsError(f"User {data.user_id} is already an admin")
        
        # Create admin
        admin = await self.admin_repo.create(
            user_id=data.user_id,
            role=data.role,
            permissions=data.permissions,
            created_by=created_by,
        )
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=created_by,
            details={
                "event": "admin_created",
                "new_admin_id": str(admin.id),
                "new_admin_user_id": str(data.user_id),
                "role": data.role.value,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return AdminResponse(
            id=admin.id,
            user_id=admin.user_id,
            role=admin.role,
            permissions=admin.permissions,
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
            created_by=admin.created_by,
            user_email=user.email,
            user_name=user.name,
        )

    async def get_admin(self, admin_id: uuid.UUID) -> AdminResponse:
        """Get admin by ID.
        
        Args:
            admin_id: Admin ID
            
        Returns:
            AdminResponse: Admin data
            
        Raises:
            AdminNotFoundError: If admin not found
        """
        admin = await self.admin_repo.get_by_id(admin_id)
        if admin is None:
            raise AdminNotFoundError(f"Admin with ID {admin_id} not found")
        
        # Get user info
        user = await self.user_repo.get_by_id(admin.user_id)
        
        return AdminResponse(
            id=admin.id,
            user_id=admin.user_id,
            role=admin.role,
            permissions=admin.permissions,
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
            created_by=admin.created_by,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
        )

    async def get_admin_by_user_id(self, user_id: uuid.UUID) -> Optional[AdminResponse]:
        """Get admin by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            AdminResponse | None: Admin data if found
        """
        result = await self.admin_repo.get_admin_with_user(user_id)
        if result is None:
            return None
        
        admin, user = result
        
        return AdminResponse(
            id=admin.id,
            user_id=admin.user_id,
            role=admin.role,
            permissions=admin.permissions,
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
            created_by=admin.created_by,
            user_email=user.email,
            user_name=user.name,
        )

    async def get_all_admins(
        self,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
    ) -> AdminListResponse:
        """Get all admins with pagination.
        
        Requirements: 1.5 - Display all admins with roles, last login, status
        
        Args:
            page: Page number
            page_size: Items per page
            include_inactive: Include inactive admins
            
        Returns:
            AdminListResponse: Paginated admin list
        """
        admins, total = await self.admin_repo.get_all(
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )
        
        # Get user info for each admin
        items = []
        for admin in admins:
            user = await self.user_repo.get_by_id(admin.user_id)
            items.append(AdminResponse(
                id=admin.id,
                user_id=admin.user_id,
                role=admin.role,
                permissions=admin.permissions,
                is_active=admin.is_active,
                last_login_at=admin.last_login_at,
                created_at=admin.created_at,
                updated_at=admin.updated_at,
                created_by=admin.created_by,
                user_email=user.email if user else None,
                user_name=user.name if user else None,
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return AdminListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_admin(
        self,
        admin_id: uuid.UUID,
        data: AdminUpdate,
        updated_by: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminResponse:
        """Update admin.
        
        Args:
            admin_id: Admin ID to update
            data: Update data
            updated_by: ID of admin performing update
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AdminResponse: Updated admin
            
        Raises:
            AdminNotFoundError: If admin not found
        """
        admin = await self.admin_repo.get_by_id(admin_id)
        if admin is None:
            raise AdminNotFoundError(f"Admin with ID {admin_id} not found")
        
        # Track changes for audit
        changes = {}
        if data.role is not None and data.role.value != admin.role:
            changes["role"] = {"from": admin.role, "to": data.role.value}
        if data.permissions is not None and data.permissions != admin.permissions:
            changes["permissions"] = {"from": admin.permissions, "to": data.permissions}
        if data.is_active is not None and data.is_active != admin.is_active:
            changes["is_active"] = {"from": admin.is_active, "to": data.is_active}
        
        # Update admin
        admin = await self.admin_repo.update(
            admin=admin,
            role=data.role,
            permissions=data.permissions,
            is_active=data.is_active,
        )
        
        # Audit log
        if changes:
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=updated_by,
                details={
                    "event": "admin_updated",
                    "admin_id": str(admin_id),
                    "changes": changes,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        # Get user info
        user = await self.user_repo.get_by_id(admin.user_id)
        
        return AdminResponse(
            id=admin.id,
            user_id=admin.user_id,
            role=admin.role,
            permissions=admin.permissions,
            is_active=admin.is_active,
            last_login_at=admin.last_login_at,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
            created_by=admin.created_by,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
        )

    async def deactivate_admin(
        self,
        admin_id: uuid.UUID,
        deactivated_by: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Deactivate an admin.
        
        Args:
            admin_id: Admin ID to deactivate
            deactivated_by: ID of admin performing deactivation
            ip_address: Client IP address
            user_agent: Client user agent
            
        Raises:
            AdminNotFoundError: If admin not found
            ValueError: If trying to deactivate last super admin
        """
        admin = await self.admin_repo.get_by_id(admin_id)
        if admin is None:
            raise AdminNotFoundError(f"Admin with ID {admin_id} not found")
        
        # Prevent deactivating last super admin
        if admin.is_super_admin:
            super_admin_count = await self.admin_repo.count_super_admins()
            if super_admin_count <= 1:
                raise ValueError("Cannot deactivate the last super admin")
        
        # Deactivate
        await self.admin_repo.update(admin, is_active=False)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=deactivated_by,
            details={
                "event": "admin_deactivated",
                "admin_id": str(admin_id),
                "admin_user_id": str(admin.user_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def update_last_login(
        self,
        admin: Admin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Update admin's last login timestamp.
        
        Args:
            admin: Admin instance
            ip_address: Client IP address
            user_agent: Client user agent
        """
        await self.admin_repo.update_last_login(admin)
        
        # Audit log
        AuditLogger.log(
            action=AuditAction.ADMIN_ACTION,
            user_id=admin.user_id,
            details={
                "event": "admin_login",
                "admin_id": str(admin.id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
