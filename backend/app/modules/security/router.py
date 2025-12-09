"""Security API router.

Provides endpoints for:
- KMS key rotation status and management
- TLS configuration
- Admin authentication
- Security scanning
- Audit log export

Requirements: 25.1, 25.2, 25.3, 25.4, 25.5
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.security.schemas import (
    AdminAuthRequest,
    AdminAuthResponse,
    AuditExportRequest,
    AuditExportResponse,
    KeyRotationStatus,
    SecurityAlert,
    SecurityScanRequest,
    SecurityScanResult,
    TLSConfig,
    TLSStatus,
    VulnerabilitySeverity,
)
from app.modules.security.service import SecurityService

router = APIRouter(prefix="/security", tags=["security"])


def get_security_service() -> SecurityService:
    """Dependency to get security service instance."""
    return SecurityService()


# ==================== KMS Key Management (Requirement 25.1) ====================

@router.get("/kms/status", response_model=KeyRotationStatus)
async def get_key_rotation_status(
    service: SecurityService = Depends(get_security_service),
) -> KeyRotationStatus:
    """Get the current KMS key rotation status.
    
    Returns information about:
    - Current key version
    - Key age
    - Whether rotation is recommended
    """
    return service.get_key_rotation_status()


@router.post("/kms/rotate", response_model=KeyRotationStatus)
async def rotate_encryption_key(
    service: SecurityService = Depends(get_security_service),
) -> KeyRotationStatus:
    """Rotate the KMS encryption key.
    
    Creates a new key version while keeping old keys active for decryption.
    This allows seamless key rotation without data loss.
    
    Note: In production, this endpoint should require admin authentication.
    """
    return service.rotate_encryption_key()


# ==================== TLS Configuration (Requirement 25.2) ====================

@router.get("/tls/status", response_model=TLSStatus)
async def get_tls_status(
    service: SecurityService = Depends(get_security_service),
) -> TLSStatus:
    """Get the current TLS status and configuration.
    
    Returns:
    - Whether TLS is enabled
    - Current TLS version
    - Cipher suite in use
    - Compliance status (TLS 1.3 required)
    """
    return service.get_tls_status()


@router.get("/tls/config", response_model=TLSConfig)
async def get_tls_config(
    service: SecurityService = Depends(get_security_service),
) -> TLSConfig:
    """Get the current TLS configuration."""
    return service.get_tls_config()


@router.put("/tls/config", response_model=TLSConfig)
async def update_tls_config(
    config: TLSConfig,
    service: SecurityService = Depends(get_security_service),
) -> TLSConfig:
    """Update TLS configuration.
    
    Note: In production, this endpoint should require admin authentication.
    """
    return service.set_tls_config(config)


@router.post("/tls/enforce-1.3", response_model=TLSConfig)
async def enforce_tls_1_3(
    service: SecurityService = Depends(get_security_service),
) -> TLSConfig:
    """Enforce TLS 1.3 for all connections.
    
    This is the recommended configuration per requirement 25.2.
    """
    return service.enforce_tls_1_3()


# ==================== Admin Authentication (Requirement 25.3) ====================

@router.post("/admin/verify", response_model=AdminAuthResponse)
async def verify_admin_auth(
    request: AdminAuthRequest,
    service: SecurityService = Depends(get_security_service),
) -> AdminAuthResponse:
    """Verify additional authentication for admin functions.
    
    Requires 2FA verification for sensitive admin operations.
    Returns a short-lived session token for the authorized action.
    
    Note: In production, this would look up the user's 2FA status and secret.
    """
    # In production, we would look up the user and their 2FA configuration
    # For now, we'll simulate with a placeholder
    # This would be integrated with the auth service
    
    # Simulated user lookup - in production, get from database
    user_has_2fa = True  # Assume user has 2FA enabled for admin
    totp_secret = None  # Would be fetched from user record
    
    return await service.verify_admin_auth(
        request=request,
        user_has_2fa=user_has_2fa,
        totp_secret=totp_secret,
    )


@router.post("/admin/revoke/{token}")
async def revoke_admin_session(
    token: str,
    service: SecurityService = Depends(get_security_service),
) -> dict:
    """Revoke an admin session token."""
    success = service.revoke_admin_session(token)
    return {"revoked": success}


# ==================== Security Scanning (Requirement 25.4) ====================

@router.post("/scan", response_model=SecurityScanResult)
async def run_security_scan(
    request: SecurityScanRequest = SecurityScanRequest(),
    service: SecurityService = Depends(get_security_service),
) -> SecurityScanResult:
    """Run a security scan to detect vulnerabilities.
    
    Scans for:
    - Dependency vulnerabilities
    - Configuration issues
    - Code security issues
    
    Alerts are generated within 24 hours for critical/high vulnerabilities.
    """
    return await service.run_security_scan(request)


@router.get("/alerts", response_model=list[SecurityAlert])
async def get_security_alerts(
    severity: Optional[VulnerabilitySeverity] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100,
    service: SecurityService = Depends(get_security_service),
) -> list[SecurityAlert]:
    """Get security alerts.
    
    Args:
        severity: Filter by severity level
        acknowledged: Filter by acknowledgment status
        limit: Maximum number of alerts to return
    """
    return service.get_security_alerts(severity, acknowledged, limit)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user_id: uuid.UUID,
    service: SecurityService = Depends(get_security_service),
) -> dict:
    """Acknowledge a security alert."""
    success = service.acknowledge_alert(alert_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return {"acknowledged": True}


# ==================== Audit Export (Requirement 25.5) ====================

@router.post("/audit/export", response_model=AuditExportResponse)
async def export_audit_logs(
    request: AuditExportRequest,
    service: SecurityService = Depends(get_security_service),
) -> AuditExportResponse:
    """Export audit logs for specified time period.
    
    Provides complete action logs for compliance and security review.
    Supports JSON and CSV export formats.
    
    Note: In production, this endpoint should require admin authentication.
    """
    return await service.export_audit_logs(request)
