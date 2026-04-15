"""Admin module for platform administration.

This module provides administrative functionality for the YouTube Automation platform,
including user management, system monitoring, billing administration, and compliance.

Requirements: 1.1, 1.2, 1.3 - Admin Authentication, 2FA, and Audit Logging
"""

from app.modules.admin.router import router as admin_router
from app.modules.admin.models import Admin, AdminRole, AdminPermission
from app.modules.admin.middleware import (
    verify_admin_access,
    verify_super_admin,
    verify_admin_2fa_session,
    require_permission,
    require_any_permission,
    require_2fa_and_permission,
    Admin2FARequired,
    AdminAccessDenied,
)
from app.modules.admin.audit import (
    AdminAuditService,
    AdminAuditEvent,
    AdminAuditEntry,
)

__all__ = [
    # Router
    "admin_router",
    # Models
    "Admin",
    "AdminRole",
    "AdminPermission",
    # Middleware
    "verify_admin_access",
    "verify_super_admin",
    "verify_admin_2fa_session",
    "require_permission",
    "require_any_permission",
    "require_2fa_and_permission",
    "Admin2FARequired",
    "AdminAccessDenied",
    # Audit
    "AdminAuditService",
    "AdminAuditEvent",
    "AdminAuditEntry",
]
