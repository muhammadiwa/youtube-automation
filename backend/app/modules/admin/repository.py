"""Repository for Admin database operations.

Requirements: 1.1, 1.4 - Admin Authentication & Authorization
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import Admin, AdminRole, DEFAULT_PERMISSIONS
from app.modules.auth.models import User


class AdminRepository:
    """Repository for Admin CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        role: AdminRole = AdminRole.ADMIN,
        permissions: Optional[list[str]] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Admin:
        """Create a new admin.

        Args:
            user_id: User ID to grant admin access
            role: Admin role
            permissions: Custom permissions (uses default if None)
            created_by: ID of admin who created this admin

        Returns:
            Admin: Created admin instance
        """
        # Use default permissions for role if not specified
        if permissions is None:
            permissions = [p.value for p in DEFAULT_PERMISSIONS.get(role, [])]
        
        admin = Admin(
            user_id=user_id,
            role=role.value,
            permissions=permissions,
            created_by=created_by,
        )
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def get_by_id(self, admin_id: uuid.UUID) -> Optional[Admin]:
        """Get admin by ID.

        Args:
            admin_id: Admin UUID

        Returns:
            Admin | None: Admin if found, None otherwise
        """
        result = await self.session.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Admin]:
        """Get admin by user ID.

        Args:
            user_id: User UUID

        Returns:
            Admin | None: Admin if found, None otherwise
        """
        result = await self.session.execute(
            select(Admin).where(Admin.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
    ) -> tuple[list[Admin], int]:
        """Get all admins with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            include_inactive: Whether to include inactive admins

        Returns:
            tuple: (list of admins, total count)
        """
        query = select(Admin)
        count_query = select(func.count(Admin.id))
        
        if not include_inactive:
            query = query.where(Admin.is_active == True)
            count_query = count_query.where(Admin.is_active == True)
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Admin.created_at.desc())
        
        result = await self.session.execute(query)
        admins = list(result.scalars().all())
        
        return admins, total

    async def update(
        self,
        admin: Admin,
        role: Optional[AdminRole] = None,
        permissions: Optional[list[str]] = None,
        is_active: Optional[bool] = None,
    ) -> Admin:
        """Update admin attributes.

        Args:
            admin: Admin instance to update
            role: New role
            permissions: New permissions
            is_active: New active status

        Returns:
            Admin: Updated admin instance
        """
        if role is not None:
            admin.role = role.value
        if permissions is not None:
            admin.permissions = permissions
        if is_active is not None:
            admin.is_active = is_active
        
        await self.session.flush()
        return admin

    async def update_last_login(self, admin: Admin) -> Admin:
        """Update admin's last login timestamp.

        Args:
            admin: Admin instance

        Returns:
            Admin: Updated admin instance
        """
        admin.last_login_at = datetime.utcnow()
        await self.session.flush()
        return admin

    async def delete(self, admin: Admin) -> None:
        """Delete an admin.

        Args:
            admin: Admin instance to delete
        """
        await self.session.delete(admin)
        await self.session.flush()

    async def exists_by_user_id(self, user_id: uuid.UUID) -> bool:
        """Check if admin exists by user ID.

        Args:
            user_id: User ID to check

        Returns:
            bool: True if admin exists
        """
        result = await self.session.execute(
            select(Admin.id).where(Admin.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_admin_with_user(
        self, user_id: uuid.UUID
    ) -> Optional[tuple[Admin, User]]:
        """Get admin with associated user data.

        Args:
            user_id: User UUID

        Returns:
            tuple | None: (Admin, User) if found, None otherwise
        """
        result = await self.session.execute(
            select(Admin, User)
            .join(User, Admin.user_id == User.id)
            .where(Admin.user_id == user_id)
        )
        row = result.first()
        if row:
            return row[0], row[1]
        return None

    async def count_super_admins(self) -> int:
        """Count the number of super admins.

        Returns:
            int: Number of active super admins
        """
        result = await self.session.execute(
            select(func.count(Admin.id)).where(
                Admin.role == AdminRole.SUPER_ADMIN.value,
                Admin.is_active == True,
            )
        )
        return result.scalar() or 0
