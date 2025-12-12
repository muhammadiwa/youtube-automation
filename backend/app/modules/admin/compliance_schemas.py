"""Pydantic schemas for Admin Compliance module.

Requirements: 8.1, 8.2, 8.3 - Audit Logs & Security
Requirements: 15.1, 15.2 - Compliance & Data Management
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Literal

from pydantic import BaseModel, Field


# ==================== Audit Log Schemas (Requirements 8.1, 8.2, 8.3) ====================


class AuditLogFilters(BaseModel):
    """Filters for audit log query.
    
    Requirements: 8.2 - Support filter by date range, actor, action type, and target resource
    
    Property 18: Audit Log Filtering
    - For any audit log filter query with date_range, actor, action_type, and resource_type,
    - returned logs SHALL match ALL specified filter criteria.
    """
    date_from: Optional[datetime] = Field(None, description="Filter logs from this date")
    date_to: Optional[datetime] = Field(None, description="Filter logs until this date")
    actor_id: Optional[uuid.UUID] = Field(None, description="Filter by actor (user) ID")
    action_type: Optional[str] = Field(None, description="Filter by action type")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    search: Optional[str] = Field(None, description="Search in details")


class AuditLogResponse(BaseModel):
    """Response for a single audit log entry.
    
    Requirements: 8.1 - Display all admin and system actions with timestamp, actor, action, and details
    """
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    action: str
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    # Extracted from details for convenience
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    event: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs.
    
    Requirements: 8.1 - Display all admin and system actions
    """
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogExportRequest(BaseModel):
    """Request to export audit logs.
    
    Requirements: 8.3 - Generate CSV with all log fields for compliance purposes
    """
    date_from: Optional[datetime] = Field(None, description="Export logs from this date")
    date_to: Optional[datetime] = Field(None, description="Export logs until this date")
    actor_id: Optional[uuid.UUID] = Field(None, description="Filter by actor ID")
    action_type: Optional[str] = Field(None, description="Filter by action type")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    format: Literal["csv", "json"] = Field(default="csv", description="Export format")


class AuditLogExportResponse(BaseModel):
    """Response for audit log export.
    
    Requirements: 8.3 - Generate CSV with all log fields for compliance purposes
    """
    export_id: uuid.UUID
    format: str
    record_count: int
    file_size_bytes: int
    download_url: str
    expires_at: datetime
    created_at: datetime


# ==================== Security Dashboard Schemas (Requirements 8.4, 8.5) ====================


class FailedLoginAttempt(BaseModel):
    """Failed login attempt record."""
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    reason: Optional[str] = None


class SuspiciousIP(BaseModel):
    """Suspicious IP address record."""
    ip_address: str
    failed_attempts: int
    last_attempt: datetime
    blocked: bool = False
    countries: list[str] = Field(default_factory=list)


class SecurityEvent(BaseModel):
    """Security event record."""
    id: uuid.UUID
    event_type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    user_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    timestamp: datetime
    resolved: bool = False


class SecurityDashboardResponse(BaseModel):
    """Security dashboard response.
    
    Requirements: 8.4, 8.5 - Show failed login attempts, suspicious IPs, and security events
    """
    failed_login_attempts_24h: int
    failed_login_attempts_7d: int
    suspicious_ips: list[SuspiciousIP]
    recent_security_events: list[SecurityEvent]
    blocked_ips_count: int
    active_sessions_count: int


# ==================== Data Export Request Schemas (Requirements 15.1) ====================


class DataExportRequestStatus(BaseModel):
    """Status of a data export request."""
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    status: Literal["pending", "processing", "completed", "failed"]
    requested_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DataExportRequestListResponse(BaseModel):
    """Paginated list of data export requests.
    
    Requirements: 15.1 - List data export requests
    """
    items: list[DataExportRequestStatus]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProcessDataExportResponse(BaseModel):
    """Response after processing a data export request.
    
    Requirements: 15.1 - Generate complete data package within 72 hours
    
    Property 16: Data Export Completion
    - For any data export request, the system SHALL generate complete data package
    - and update status to 'completed' with download_url within 72 hours.
    """
    request_id: uuid.UUID
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


# ==================== Deletion Request Schemas (Requirements 15.2) ====================


class DeletionRequestStatus(BaseModel):
    """Status of a deletion request.
    
    Property 17: Deletion Grace Period
    - For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    status: Literal["pending", "scheduled", "processing", "completed", "cancelled"]
    requested_at: datetime
    scheduled_for: datetime
    days_remaining: int
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[uuid.UUID] = None
    cancellation_reason: Optional[str] = None

    class Config:
        from_attributes = True


class DeletionRequestListResponse(BaseModel):
    """Paginated list of deletion requests.
    
    Requirements: 15.2 - Display pending deletions with countdown and cancel option
    """
    items: list[DeletionRequestStatus]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProcessDeletionResponse(BaseModel):
    """Response after processing a deletion request.
    
    Requirements: 15.2 - Schedule deletion with 30-day grace period
    """
    request_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    scheduled_for: Optional[datetime] = None
    message: str


class CancelDeletionRequest(BaseModel):
    """Request to cancel a deletion."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation")


class CancelDeletionResponse(BaseModel):
    """Response after cancelling a deletion request."""
    request_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    cancelled_at: datetime
    message: str
