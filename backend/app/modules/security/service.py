"""Security service for comprehensive security management.

Requirements:
- 25.1: OAuth tokens encrypted using KMS with automatic key rotation
- 25.2: TLS 1.3 enforcement for all connections
- 25.3: Additional authentication factor for admin functions
- 25.4: Security scanning with vulnerability detection (alert within 24 hours)
- 25.5: Complete audit log export for specified time period
"""

import csv
import io
import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from app.core.kms import (
    get_key_manager,
    get_key_rotation_status,
    kms_encrypt_simple,
    kms_decrypt_simple,
    kms_rotate_and_reencrypt,
)
from app.modules.auth.audit import AuditLogger, AuditLogEntry
from app.modules.security.schemas import (
    AdminAction,
    AdminAuthRequest,
    AdminAuthResponse,
    AuditExportFormat,
    AuditExportRequest,
    AuditExportResponse,
    KeyRotationStatus,
    SecurityAlert,
    SecurityScanRequest,
    SecurityScanResult,
    TLSConfig,
    TLSStatus,
    TLSVersion,
    Vulnerability,
    VulnerabilityReport,
    VulnerabilitySeverity,
    VulnerabilityType,
)


class AdminSessionStore:
    """In-memory store for admin session tokens.
    
    Admin sessions provide additional authentication for sensitive operations.
    Sessions are short-lived (15 minutes) and require 2FA verification.
    """
    
    _sessions: dict[str, dict[str, Any]] = {}
    SESSION_DURATION_MINUTES = 15
    
    @classmethod
    def create_session(
        cls,
        user_id: uuid.UUID,
        action: str,
        ip_address: Optional[str] = None,
    ) -> tuple[str, datetime]:
        """Create a new admin session.
        
        Args:
            user_id: User ID for the session
            action: The admin action being authorized
            ip_address: Client IP address
            
        Returns:
            tuple: (session_token, expires_at)
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=cls.SESSION_DURATION_MINUTES)
        
        cls._sessions[token] = {
            "user_id": user_id,
            "action": action,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }
        
        return token, expires_at
    
    @classmethod
    def validate_session(
        cls,
        token: str,
        user_id: uuid.UUID,
        action: Optional[str] = None,
    ) -> bool:
        """Validate an admin session token.
        
        Args:
            token: Session token to validate
            user_id: Expected user ID
            action: Optional action to validate against
            
        Returns:
            bool: True if session is valid
        """
        session = cls._sessions.get(token)
        if not session:
            return False
        
        # Check expiration
        if datetime.utcnow() > session["expires_at"]:
            del cls._sessions[token]
            return False
        
        # Check user ID
        if session["user_id"] != user_id:
            return False
        
        # Check action if specified
        if action and session["action"] != action:
            return False
        
        return True
    
    @classmethod
    def revoke_session(cls, token: str) -> bool:
        """Revoke an admin session.
        
        Args:
            token: Session token to revoke
            
        Returns:
            bool: True if session was revoked
        """
        if token in cls._sessions:
            del cls._sessions[token]
            return True
        return False
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired sessions.
        
        Returns:
            int: Number of sessions removed
        """
        now = datetime.utcnow()
        expired = [
            token for token, session in cls._sessions.items()
            if now > session["expires_at"]
        ]
        for token in expired:
            del cls._sessions[token]
        return len(expired)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all sessions (for testing)."""
        cls._sessions.clear()


class SecurityAlertStore:
    """In-memory store for security alerts.
    
    Tracks security alerts from scans and monitoring.
    Alerts are retained for 30 days by default.
    """
    
    _alerts: list[SecurityAlert] = []
    RETENTION_DAYS = 30
    
    @classmethod
    def add_alert(cls, alert: SecurityAlert) -> None:
        """Add a new security alert.
        
        Args:
            alert: The security alert to add
        """
        cls._alerts.append(alert)
    
    @classmethod
    def get_alerts(
        cls,
        severity: Optional[VulnerabilitySeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> list[SecurityAlert]:
        """Get security alerts with optional filtering.
        
        Args:
            severity: Filter by severity level
            acknowledged: Filter by acknowledgment status
            limit: Maximum number of alerts to return
            
        Returns:
            list: Matching security alerts
        """
        alerts = cls._alerts
        
        if severity is not None:
            alerts = [a for a in alerts if a.severity == severity]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        # Return most recent first
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]
    
    @classmethod
    def acknowledge_alert(
        cls,
        alert_id: str,
        user_id: uuid.UUID,
    ) -> bool:
        """Acknowledge a security alert.
        
        Args:
            alert_id: Alert ID to acknowledge
            user_id: User acknowledging the alert
            
        Returns:
            bool: True if alert was acknowledged
        """
        for alert in cls._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user_id
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False
    
    @classmethod
    def cleanup_old(cls) -> int:
        """Remove alerts older than retention period.
        
        Returns:
            int: Number of alerts removed
        """
        cutoff = datetime.utcnow() - timedelta(days=cls.RETENTION_DAYS)
        original_count = len(cls._alerts)
        cls._alerts = [a for a in cls._alerts if a.created_at > cutoff]
        return original_count - len(cls._alerts)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all alerts (for testing)."""
        cls._alerts.clear()


class SecurityService:
    """Service for comprehensive security management.
    
    Provides:
    - KMS encryption with automatic key rotation
    - TLS 1.3 configuration and enforcement
    - Admin authentication with additional factor
    - Security scanning and vulnerability detection
    - Audit log export
    """
    
    def __init__(self):
        """Initialize the security service."""
        self._tls_config = TLSConfig()
    
    # ==================== KMS Encryption (Requirement 25.1) ====================
    
    def encrypt_oauth_token(self, token: str) -> str:
        """Encrypt an OAuth token using KMS.
        
        Args:
            token: Plain text OAuth token
            
        Returns:
            str: Encrypted token
        """
        return kms_encrypt_simple(token)
    
    def decrypt_oauth_token(self, encrypted_token: str) -> Optional[str]:
        """Decrypt an OAuth token using KMS.
        
        Args:
            encrypted_token: Encrypted OAuth token
            
        Returns:
            Optional[str]: Decrypted token or None if decryption fails
        """
        return kms_decrypt_simple(encrypted_token)
    
    def get_key_rotation_status(self) -> KeyRotationStatus:
        """Get the current key rotation status.
        
        Returns:
            KeyRotationStatus: Current key rotation information
        """
        status = get_key_rotation_status()
        km = get_key_manager()
        current_key = km.get_current_key()
        
        return KeyRotationStatus(
            current_version=status["current_version"],
            total_keys=status["total_keys"],
            active_keys=status["active_keys"],
            current_key_age_days=status["current_key_age_days"],
            rotation_recommended=status["rotation_recommended"],
            rotation_interval_days=status["rotation_interval_days"],
            last_rotation_at=current_key.created_at if current_key.version > 1 else None,
        )
    
    def rotate_encryption_key(self, new_master_key: Optional[str] = None) -> KeyRotationStatus:
        """Rotate the encryption key.
        
        Args:
            new_master_key: Optional new master key
            
        Returns:
            KeyRotationStatus: Updated key rotation status
        """
        km = get_key_manager()
        km.rotate_key(new_master_key)
        return self.get_key_rotation_status()
    
    def reencrypt_token(self, encrypted_token: str) -> str:
        """Re-encrypt a token with the current key.
        
        Useful after key rotation to update old encrypted data.
        
        Args:
            encrypted_token: Token encrypted with an older key
            
        Returns:
            str: Token re-encrypted with current key
        """
        plaintext = kms_decrypt_simple(encrypted_token)
        if plaintext is None:
            raise ValueError("Failed to decrypt token")
        return kms_encrypt_simple(plaintext)
    
    # ==================== TLS Configuration (Requirement 25.2) ====================
    
    def get_tls_config(self) -> TLSConfig:
        """Get the current TLS configuration.
        
        Returns:
            TLSConfig: Current TLS settings
        """
        return self._tls_config
    
    def set_tls_config(self, config: TLSConfig) -> TLSConfig:
        """Update TLS configuration.
        
        Args:
            config: New TLS configuration
            
        Returns:
            TLSConfig: Updated configuration
        """
        self._tls_config = config
        return self._tls_config
    
    def get_tls_status(self) -> TLSStatus:
        """Get the current TLS status.
        
        Returns:
            TLSStatus: Current TLS status
        """
        return TLSStatus(
            enabled=self._tls_config.enforce_tls,
            version=self._tls_config.minimum_version.value,
            cipher_suite=self._tls_config.cipher_suites[0] if self._tls_config.cipher_suites else None,
            certificate_valid=True,  # Would check actual certificate in production
            is_compliant=self._tls_config.minimum_version == TLSVersion.TLS_1_3,
        )
    
    def enforce_tls_1_3(self) -> TLSConfig:
        """Enforce TLS 1.3 for all connections.
        
        Returns:
            TLSConfig: Updated configuration with TLS 1.3 enforced
        """
        self._tls_config.minimum_version = TLSVersion.TLS_1_3
        self._tls_config.enforce_tls = True
        return self._tls_config
    
    # ==================== Admin Security (Requirement 25.3) ====================
    
    async def verify_admin_auth(
        self,
        request: AdminAuthRequest,
        user_has_2fa: bool,
        totp_secret: Optional[str] = None,
    ) -> AdminAuthResponse:
        """Verify additional authentication for admin functions.
        
        Requires 2FA verification for sensitive admin operations.
        
        Args:
            request: Admin authentication request
            user_has_2fa: Whether user has 2FA enabled
            totp_secret: User's TOTP secret for verification
            
        Returns:
            AdminAuthResponse: Authentication result
        """
        # Admin functions require 2FA
        if not user_has_2fa:
            return AdminAuthResponse(
                authorized=False,
                reason="2FA must be enabled for admin functions"
            )
        
        if not totp_secret:
            return AdminAuthResponse(
                authorized=False,
                reason="TOTP secret not configured"
            )
        
        # Verify TOTP code
        from app.modules.auth.totp import verify_totp_code
        
        if not verify_totp_code(totp_secret, request.totp_code):
            return AdminAuthResponse(
                authorized=False,
                reason="Invalid 2FA code"
            )
        
        # Create admin session
        token, expires_at = AdminSessionStore.create_session(
            user_id=request.user_id,
            action=request.action,
            ip_address=request.ip_address,
        )
        
        return AdminAuthResponse(
            authorized=True,
            session_token=token,
            expires_at=expires_at,
        )
    
    def validate_admin_session(
        self,
        token: str,
        user_id: uuid.UUID,
        action: Optional[str] = None,
    ) -> bool:
        """Validate an admin session token.
        
        Args:
            token: Session token to validate
            user_id: Expected user ID
            action: Optional action to validate against
            
        Returns:
            bool: True if session is valid
        """
        return AdminSessionStore.validate_session(token, user_id, action)
    
    def revoke_admin_session(self, token: str) -> bool:
        """Revoke an admin session.
        
        Args:
            token: Session token to revoke
            
        Returns:
            bool: True if session was revoked
        """
        return AdminSessionStore.revoke_session(token)
    
    # ==================== Security Scanning (Requirement 25.4) ====================
    
    async def run_security_scan(
        self,
        request: SecurityScanRequest,
    ) -> SecurityScanResult:
        """Run a security scan and detect vulnerabilities.
        
        Alerts are generated within 24 hours of detection (per requirement 25.4).
        
        Args:
            request: Scan configuration
            
        Returns:
            SecurityScanResult: Scan results with vulnerabilities
        """
        scan_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        vulnerabilities: list[Vulnerability] = []
        
        # Check dependencies (simulated)
        if request.include_dependencies:
            dep_vulns = self._scan_dependencies()
            vulnerabilities.extend(dep_vulns)
        
        # Check configuration
        if request.include_configuration:
            config_vulns = self._scan_configuration()
            vulnerabilities.extend(config_vulns)
        
        # Check code (simulated)
        if request.include_code:
            code_vulns = self._scan_code()
            vulnerabilities.extend(code_vulns)
        
        completed_at = datetime.utcnow()
        
        # Count by severity
        critical_count = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])
        high_count = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH])
        medium_count = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM])
        low_count = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.LOW])
        info_count = len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.INFO])
        
        report = VulnerabilityReport(
            id=scan_id,
            scan_started_at=started_at,
            scan_completed_at=completed_at,
            total_vulnerabilities=len(vulnerabilities),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            info_count=info_count,
            vulnerabilities=vulnerabilities,
            scan_type=request.scan_type,
        )
        
        # Generate alerts for critical/high vulnerabilities (within 24 hours per requirement)
        for vuln in vulnerabilities:
            if vuln.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                alert = SecurityAlert(
                    id=str(uuid.uuid4()),
                    severity=vuln.severity,
                    title=f"Security Vulnerability: {vuln.title}",
                    description=vuln.description,
                    source="scan",
                )
                SecurityAlertStore.add_alert(alert)
        
        return SecurityScanResult(
            scan_id=scan_id,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            report=report,
        )
    
    def _scan_dependencies(self) -> list[Vulnerability]:
        """Scan dependencies for known vulnerabilities.
        
        In production, this would integrate with vulnerability databases
        like NVD, Snyk, or GitHub Advisory Database.
        
        Returns:
            list: Found vulnerabilities
        """
        # Simulated dependency scan - in production would check actual dependencies
        return []
    
    def _scan_configuration(self) -> list[Vulnerability]:
        """Scan configuration for security issues.
        
        Returns:
            list: Found vulnerabilities
        """
        vulnerabilities = []
        
        # Check TLS configuration
        if self._tls_config.minimum_version != TLSVersion.TLS_1_3:
            vulnerabilities.append(Vulnerability(
                id=str(uuid.uuid4()),
                type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title="TLS 1.3 Not Enforced",
                description="TLS 1.3 is not enforced. Older TLS versions may have known vulnerabilities.",
                affected_component="TLS Configuration",
                recommendation="Update minimum TLS version to TLS 1.3",
            ))
        
        # Check key rotation
        key_status = get_key_rotation_status()
        if key_status["rotation_recommended"]:
            vulnerabilities.append(Vulnerability(
                id=str(uuid.uuid4()),
                type=VulnerabilityType.ENCRYPTION,
                severity=VulnerabilitySeverity.LOW,
                title="Encryption Key Rotation Recommended",
                description=f"Encryption key is {key_status['current_key_age_days']} days old. Regular rotation is recommended.",
                affected_component="KMS Encryption",
                recommendation="Rotate encryption keys according to security policy",
            ))
        
        return vulnerabilities
    
    def _scan_code(self) -> list[Vulnerability]:
        """Scan code for security issues.
        
        In production, this would integrate with SAST tools.
        
        Returns:
            list: Found vulnerabilities
        """
        # Simulated code scan - in production would use SAST tools
        return []
    
    def get_security_alerts(
        self,
        severity: Optional[VulnerabilitySeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> list[SecurityAlert]:
        """Get security alerts.
        
        Args:
            severity: Filter by severity
            acknowledged: Filter by acknowledgment status
            limit: Maximum alerts to return
            
        Returns:
            list: Security alerts
        """
        return SecurityAlertStore.get_alerts(severity, acknowledged, limit)
    
    def acknowledge_alert(self, alert_id: str, user_id: uuid.UUID) -> bool:
        """Acknowledge a security alert.
        
        Args:
            alert_id: Alert to acknowledge
            user_id: User acknowledging
            
        Returns:
            bool: True if acknowledged
        """
        return SecurityAlertStore.acknowledge_alert(alert_id, user_id)
    
    # ==================== Audit Export (Requirement 25.5) ====================
    
    async def export_audit_logs(
        self,
        request: AuditExportRequest,
    ) -> AuditExportResponse:
        """Export audit logs for specified time period.
        
        Provides complete action logs per requirement 25.5.
        
        Args:
            request: Export configuration
            
        Returns:
            AuditExportResponse: Exported audit data
        """
        # Get logs from AuditLogger
        all_logs = AuditLogger.get_logs(
            user_id=request.user_id,
            limit=10000,  # Get all logs, we'll filter by date
        )
        
        # Filter by date range
        filtered_logs = [
            log for log in all_logs
            if request.start_date <= log.timestamp <= request.end_date
        ]
        
        # Filter by actions if specified
        if request.actions:
            filtered_logs = [
                log for log in filtered_logs
                if log.action in request.actions
            ]
        
        export_id = str(uuid.uuid4())
        
        # Format based on requested format
        if request.format == AuditExportFormat.JSON:
            content = self._export_logs_json(filtered_logs, request.include_details)
        elif request.format == AuditExportFormat.CSV:
            content = self._export_logs_csv(filtered_logs, request.include_details)
        else:
            # PDF would require additional library
            content = self._export_logs_json(filtered_logs, request.include_details)
        
        return AuditExportResponse(
            export_id=export_id,
            format=request.format,
            record_count=len(filtered_logs),
            file_content=content,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    
    def _export_logs_json(self, logs: list[AuditLogEntry], include_details: bool) -> str:
        """Export logs as JSON.
        
        Args:
            logs: Audit log entries
            include_details: Whether to include full details
            
        Returns:
            str: JSON formatted logs
        """
        export_data = []
        for log in logs:
            entry = {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
            }
            if include_details:
                entry["details"] = log.details
                entry["user_agent"] = log.user_agent
            export_data.append(entry)
        
        return json.dumps(export_data, indent=2)
    
    def _export_logs_csv(self, logs: list[AuditLogEntry], include_details: bool) -> str:
        """Export logs as CSV.
        
        Args:
            logs: Audit log entries
            include_details: Whether to include full details
            
        Returns:
            str: CSV formatted logs
        """
        output = io.StringIO()
        
        fieldnames = ["id", "user_id", "action", "timestamp", "ip_address"]
        if include_details:
            fieldnames.extend(["details", "user_agent"])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in logs:
            row = {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else "",
                "action": log.action,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address or "",
            }
            if include_details:
                row["details"] = json.dumps(log.details) if log.details else ""
                row["user_agent"] = log.user_agent or ""
            writer.writerow(row)
        
        return output.getvalue()
