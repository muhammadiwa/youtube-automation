"""Security module for comprehensive security features.

This module provides:
- KMS encryption with automatic key rotation (Requirements: 25.1)
- TLS 1.3 enforcement (Requirements: 25.2)
- Admin security with additional auth factor (Requirements: 25.3)
- Security scanning and vulnerability detection (Requirements: 25.4)
- Audit log export (Requirements: 25.5)
"""

from app.modules.security.service import SecurityService
from app.modules.security.schemas import (
    SecurityScanResult,
    VulnerabilityReport,
    AuditExportRequest,
    AuditExportResponse,
    TLSConfig,
    AdminAuthRequest,
)

__all__ = [
    "SecurityService",
    "SecurityScanResult",
    "VulnerabilityReport",
    "AuditExportRequest",
    "AuditExportResponse",
    "TLSConfig",
    "AdminAuthRequest",
]
