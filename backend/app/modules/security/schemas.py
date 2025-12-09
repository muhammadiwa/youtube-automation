"""Security module schemas and data models.

Requirements:
- 25.1: OAuth tokens encrypted using KMS with automatic key rotation
- 25.2: TLS 1.3 enforcement for all connections
- 25.3: Additional authentication factor for admin functions
- 25.4: Security scanning with vulnerability detection
- 25.5: Complete audit log export
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class VulnerabilitySeverity(str, Enum):
    """Severity levels for security vulnerabilities."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Types of security vulnerabilities."""
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    CODE = "code"
    INFRASTRUCTURE = "infrastructure"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ENCRYPTION = "encryption"
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"


class Vulnerability(BaseModel):
    """Individual vulnerability finding."""
    id: str
    type: VulnerabilityType
    severity: VulnerabilitySeverity
    title: str
    description: str
    affected_component: str
    recommendation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class VulnerabilityReport(BaseModel):
    """Complete vulnerability scan report."""
    id: str
    scan_started_at: datetime
    scan_completed_at: datetime
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    vulnerabilities: list[Vulnerability]
    scan_type: str = "full"
    
    class Config:
        use_enum_values = True


class SecurityScanRequest(BaseModel):
    """Request to initiate a security scan."""
    scan_type: str = "full"  # full, quick, dependencies, configuration
    include_dependencies: bool = True
    include_configuration: bool = True
    include_code: bool = True


class SecurityScanResult(BaseModel):
    """Result of a security scan."""
    scan_id: str
    status: str  # pending, running, completed, failed
    started_at: datetime
    completed_at: Optional[datetime] = None
    report: Optional[VulnerabilityReport] = None
    error: Optional[str] = None


class TLSVersion(str, Enum):
    """Supported TLS versions."""
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


class TLSConfig(BaseModel):
    """TLS configuration settings."""
    minimum_version: TLSVersion = TLSVersion.TLS_1_3
    enforce_tls: bool = True
    cipher_suites: list[str] = Field(default_factory=lambda: [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256",
    ])
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    verify_client: bool = False
    
    class Config:
        use_enum_values = True


class TLSStatus(BaseModel):
    """Current TLS status and configuration."""
    enabled: bool
    version: str
    cipher_suite: Optional[str] = None
    certificate_valid: bool = True
    certificate_expires_at: Optional[datetime] = None
    is_compliant: bool = True  # True if TLS 1.3 is enforced


class AdminAuthRequest(BaseModel):
    """Request for additional admin authentication."""
    user_id: uuid.UUID
    action: str
    totp_code: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AdminAuthResponse(BaseModel):
    """Response for admin authentication."""
    authorized: bool
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


class AdminAction(str, Enum):
    """Actions requiring additional admin authentication."""
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    KEY_ROTATION = "key_rotation"
    AUDIT_EXPORT = "audit_export"
    SECURITY_SCAN = "security_scan"
    BACKUP_RESTORE = "backup_restore"
    API_KEY_REVOKE = "api_key_revoke"


class AuditExportFormat(str, Enum):
    """Supported audit export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class AuditExportRequest(BaseModel):
    """Request to export audit logs."""
    start_date: datetime
    end_date: datetime
    user_id: Optional[uuid.UUID] = None
    actions: Optional[list[str]] = None
    format: AuditExportFormat = AuditExportFormat.JSON
    include_details: bool = True


class AuditExportResponse(BaseModel):
    """Response containing exported audit logs."""
    export_id: str
    format: AuditExportFormat
    record_count: int
    file_path: Optional[str] = None
    file_content: Optional[str] = None  # For JSON/CSV inline content
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: datetime
    end_date: datetime
    
    class Config:
        use_enum_values = True


class KeyRotationRequest(BaseModel):
    """Request to rotate encryption keys."""
    new_master_key: Optional[str] = None  # If None, derives new key from existing
    reencrypt_existing: bool = True  # Re-encrypt existing data with new key


class KeyRotationStatus(BaseModel):
    """Status of key rotation."""
    current_version: int
    total_keys: int
    active_keys: int
    current_key_age_days: int
    rotation_recommended: bool
    rotation_interval_days: int
    last_rotation_at: Optional[datetime] = None


class SecurityAlert(BaseModel):
    """Security alert notification."""
    id: str
    severity: VulnerabilitySeverity
    title: str
    description: str
    source: str  # scan, monitoring, user_report
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
