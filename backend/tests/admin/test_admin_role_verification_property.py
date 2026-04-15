"""Property-based tests for admin role verification.

**Feature: admin-panel, Property 1: Admin Role Verification**
**Validates: Requirements 1.1**

For any user attempting to access admin endpoints, the system SHALL verify 
the user has admin role and return 403 Forbidden for non-admin users.
"""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
import pytest


class UserRole(str, Enum):
    """User role types for testing."""
    REGULAR_USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


@dataclass
class MockUser:
    """Mock user for testing."""
    id: uuid.UUID
    email: str
    name: str
    is_active: bool = True


@dataclass
class MockAdmin:
    """Mock admin for testing."""
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    permissions: list[str]
    is_active: bool = True
    
    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN.value


class AdminAccessVerifier:
    """
    Verifies admin access based on user role.
    
    This class implements the core logic for Property 1: Admin Role Verification.
    For any user attempting to access admin endpoints, the system SHALL verify 
    the user has admin role and return 403 Forbidden for non-admin users.
    """
    
    def __init__(self, admins: dict[uuid.UUID, MockAdmin]):
        """
        Initialize verifier with admin registry.
        
        Args:
            admins: Dictionary mapping user_id to Admin record
        """
        self.admins = admins
    
    def verify_admin_access(self, user_id: uuid.UUID) -> tuple[bool, Optional[MockAdmin], int]:
        """
        Verify if a user has admin access.
        
        Args:
            user_id: User ID to verify
            
        Returns:
            tuple: (has_access, admin_record, http_status_code)
                - has_access: True if user has admin access
                - admin_record: Admin record if found and active
                - http_status_code: 200 for success, 403 for forbidden
        """
        admin = self.admins.get(user_id)
        
        # User is not an admin
        if admin is None:
            return (False, None, 403)
        
        # Admin is inactive
        if not admin.is_active:
            return (False, None, 403)
        
        # Valid admin access
        return (True, admin, 200)
    
    def has_permission(self, user_id: uuid.UUID, permission: str) -> bool:
        """
        Check if admin has a specific permission.
        
        Args:
            user_id: User ID to check
            permission: Permission to verify
            
        Returns:
            bool: True if admin has the permission
        """
        admin = self.admins.get(user_id)
        if admin is None or not admin.is_active:
            return False
        return permission in admin.permissions


# Strategies for generating test data
uuid_strategy = st.uuids()
email_strategy = st.emails()
name_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Zs")))
role_strategy = st.sampled_from([UserRole.ADMIN, UserRole.SUPER_ADMIN])
permission_strategy = st.lists(
    st.sampled_from([
        "view_users", "manage_users", "view_billing", "manage_billing",
        "view_system", "manage_system", "view_moderation", "manage_moderation",
        "view_analytics", "export_data", "view_audit_logs", "manage_admins"
    ]),
    min_size=0,
    max_size=12,
    unique=True
)


class TestAdminRoleVerification:
    """
    Property tests for admin role verification.
    
    **Feature: admin-panel, Property 1: Admin Role Verification**
    **Validates: Requirements 1.1**
    """

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_non_admin_user_gets_403(self, user_id: uuid.UUID) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any user who is not in the admin registry, access SHALL be denied
        with HTTP 403 Forbidden.
        """
        # Empty admin registry - no admins exist
        verifier = AdminAccessVerifier(admins={})
        
        has_access, admin, status_code = verifier.verify_admin_access(user_id)
        
        assert has_access is False
        assert admin is None
        assert status_code == 403

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        role=role_strategy,
        permissions=permission_strategy
    )
    @settings(max_examples=100)
    def test_active_admin_gets_access(
        self, 
        user_id: uuid.UUID, 
        admin_id: uuid.UUID,
        role: UserRole,
        permissions: list[str]
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any user who is an active admin, access SHALL be granted
        with HTTP 200 OK.
        """
        admin = MockAdmin(
            id=admin_id,
            user_id=user_id,
            role=role.value,
            permissions=permissions,
            is_active=True
        )
        verifier = AdminAccessVerifier(admins={user_id: admin})
        
        has_access, returned_admin, status_code = verifier.verify_admin_access(user_id)
        
        assert has_access is True
        assert returned_admin is not None
        assert returned_admin.user_id == user_id
        assert status_code == 200

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        role=role_strategy,
        permissions=permission_strategy
    )
    @settings(max_examples=100)
    def test_inactive_admin_gets_403(
        self, 
        user_id: uuid.UUID, 
        admin_id: uuid.UUID,
        role: UserRole,
        permissions: list[str]
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any user who is an inactive admin, access SHALL be denied
        with HTTP 403 Forbidden.
        """
        admin = MockAdmin(
            id=admin_id,
            user_id=user_id,
            role=role.value,
            permissions=permissions,
            is_active=False  # Inactive admin
        )
        verifier = AdminAccessVerifier(admins={user_id: admin})
        
        has_access, returned_admin, status_code = verifier.verify_admin_access(user_id)
        
        assert has_access is False
        assert returned_admin is None
        assert status_code == 403

    @given(
        admin_user_id=uuid_strategy,
        non_admin_user_id=uuid_strategy,
        admin_id=uuid_strategy,
        role=role_strategy,
        permissions=permission_strategy
    )
    @settings(max_examples=100)
    def test_admin_and_non_admin_differentiation(
        self,
        admin_user_id: uuid.UUID,
        non_admin_user_id: uuid.UUID,
        admin_id: uuid.UUID,
        role: UserRole,
        permissions: list[str]
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any system with both admin and non-admin users, the system SHALL
        correctly differentiate between them - granting access to admins and
        denying access to non-admins.
        """
        # Ensure different user IDs
        assume(admin_user_id != non_admin_user_id)
        
        admin = MockAdmin(
            id=admin_id,
            user_id=admin_user_id,
            role=role.value,
            permissions=permissions,
            is_active=True
        )
        verifier = AdminAccessVerifier(admins={admin_user_id: admin})
        
        # Admin user should get access
        admin_access, admin_record, admin_status = verifier.verify_admin_access(admin_user_id)
        assert admin_access is True
        assert admin_status == 200
        
        # Non-admin user should be denied
        non_admin_access, non_admin_record, non_admin_status = verifier.verify_admin_access(non_admin_user_id)
        assert non_admin_access is False
        assert non_admin_status == 403

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        permissions=permission_strategy
    )
    @settings(max_examples=100)
    def test_super_admin_gets_access(
        self, 
        user_id: uuid.UUID, 
        admin_id: uuid.UUID,
        permissions: list[str]
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any user who is a super_admin, access SHALL be granted.
        """
        admin = MockAdmin(
            id=admin_id,
            user_id=user_id,
            role=UserRole.SUPER_ADMIN.value,
            permissions=permissions,
            is_active=True
        )
        verifier = AdminAccessVerifier(admins={user_id: admin})
        
        has_access, returned_admin, status_code = verifier.verify_admin_access(user_id)
        
        assert has_access is True
        assert returned_admin is not None
        assert returned_admin.is_super_admin is True
        assert status_code == 200

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        permissions=permission_strategy
    )
    @settings(max_examples=100)
    def test_regular_admin_gets_access(
        self, 
        user_id: uuid.UUID, 
        admin_id: uuid.UUID,
        permissions: list[str]
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any user who is a regular admin, access SHALL be granted.
        """
        admin = MockAdmin(
            id=admin_id,
            user_id=user_id,
            role=UserRole.ADMIN.value,
            permissions=permissions,
            is_active=True
        )
        verifier = AdminAccessVerifier(admins={user_id: admin})
        
        has_access, returned_admin, status_code = verifier.verify_admin_access(user_id)
        
        assert has_access is True
        assert returned_admin is not None
        assert returned_admin.is_super_admin is False
        assert status_code == 200

    @given(
        num_admins=st.integers(min_value=1, max_value=10),
        num_non_admins=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_multiple_users_verification(
        self,
        num_admins: int,
        num_non_admins: int
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any system with multiple admin and non-admin users, the system SHALL
        correctly verify each user's access status.
        """
        # Create admin users
        admins = {}
        admin_user_ids = []
        for i in range(num_admins):
            user_id = uuid.uuid4()
            admin_id = uuid.uuid4()
            admin_user_ids.append(user_id)
            admins[user_id] = MockAdmin(
                id=admin_id,
                user_id=user_id,
                role=UserRole.ADMIN.value if i % 2 == 0 else UserRole.SUPER_ADMIN.value,
                permissions=["view_users"],
                is_active=True
            )
        
        # Create non-admin user IDs
        non_admin_user_ids = [uuid.uuid4() for _ in range(num_non_admins)]
        
        verifier = AdminAccessVerifier(admins=admins)
        
        # All admin users should get access
        for user_id in admin_user_ids:
            has_access, _, status_code = verifier.verify_admin_access(user_id)
            assert has_access is True
            assert status_code == 200
        
        # All non-admin users should be denied
        for user_id in non_admin_user_ids:
            has_access, _, status_code = verifier.verify_admin_access(user_id)
            assert has_access is False
            assert status_code == 403

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        role=role_strategy,
        permission=st.sampled_from([
            "view_users", "manage_users", "view_billing", "manage_billing",
            "view_system", "manage_system", "view_moderation", "manage_moderation"
        ])
    )
    @settings(max_examples=100)
    def test_admin_permission_check(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        role: UserRole,
        permission: str
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any admin with specific permissions, the system SHALL correctly
        report whether they have a given permission.
        """
        # Admin with the permission
        admin_with_perm = MockAdmin(
            id=admin_id,
            user_id=user_id,
            role=role.value,
            permissions=[permission],
            is_active=True
        )
        verifier_with = AdminAccessVerifier(admins={user_id: admin_with_perm})
        assert verifier_with.has_permission(user_id, permission) is True
        
        # Admin without the permission
        other_user_id = uuid.uuid4()
        admin_without_perm = MockAdmin(
            id=uuid.uuid4(),
            user_id=other_user_id,
            role=role.value,
            permissions=[],  # No permissions
            is_active=True
        )
        verifier_without = AdminAccessVerifier(admins={other_user_id: admin_without_perm})
        assert verifier_without.has_permission(other_user_id, permission) is False

    @given(user_id=uuid_strategy, permission=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_non_admin_has_no_permissions(
        self,
        user_id: uuid.UUID,
        permission: str
    ) -> None:
        """
        **Feature: admin-panel, Property 1: Admin Role Verification**
        
        For any non-admin user, permission checks SHALL always return False.
        """
        verifier = AdminAccessVerifier(admins={})
        assert verifier.has_permission(user_id, permission) is False
