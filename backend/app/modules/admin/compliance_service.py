"""Admin Compliance Service.

Requirements: 8.1, 8.2, 8.3 - Audit Logs & Security
Requirements: 15.1, 15.2 - Compliance & Data Management
"""

import csv
import io
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.audit import AuditLogger, AuditLog, AuditLogEntry
from app.modules.admin.audit import AdminAuditService, AdminAuditEvent
from app.modules.admin.compliance_schemas import (
    AuditLogFilters,
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogExportResponse,
    SecurityDashboardResponse,
    FailedLoginAttempt,
    SuspiciousIP,
    SecurityEvent,
    DataExportRequestStatus,
    DataExportRequestListResponse,
    ProcessDataExportResponse,
    DeletionRequestStatus,
    DeletionRequestListResponse,
    ProcessDeletionResponse,
    CancelDeletionResponse,
)


class AuditLogNotFoundError(Exception):
    """Raised when audit log is not found."""
    pass


class DataExportRequestNotFoundError(Exception):
    """Raised when data export request is not found."""
    pass


class DeletionRequestNotFoundError(Exception):
    """Raised when deletion request is not found."""
    pass


class DeletionRequestAlreadyProcessedError(Exception):
    """Raised when deletion request is already processed."""
    pass


class DeletionRequestAlreadyCancelledError(Exception):
    """Raised when deletion request is already cancelled."""
    pass


def filter_audit_logs(
    logs: list[AuditLogEntry],
    filters: AuditLogFilters,
) -> list[AuditLogEntry]:
    """
    Filter audit logs based on provided criteria.
    
    Property 18: Audit Log Filtering
    - For any audit log filter query with date_range, actor, action_type, and resource_type,
    - returned logs SHALL match ALL specified filter criteria.
    
    Args:
        logs: List of audit log entries to filter
        filters: Filter criteria
        
    Returns:
        list[AuditLogEntry]: Filtered audit log entries
    """
    result = logs
    
    # Filter by date range
    if filters.date_from:
        result = [log for log in result if log.timestamp >= filters.date_from]
    
    if filters.date_to:
        result = [log for log in result if log.timestamp <= filters.date_to]
    
    # Filter by actor (user_id)
    if filters.actor_id:
        result = [log for log in result if log.user_id == filters.actor_id]
    
    # Filter by action type
    if filters.action_type:
        result = [log for log in result if log.action == filters.action_type]
    
    # Filter by resource type (from details)
    if filters.resource_type:
        result = [
            log for log in result 
            if log.details and log.details.get("resource_type") == filters.resource_type
        ]
    
    # Filter by resource ID (from details)
    if filters.resource_id:
        result = [
            log for log in result 
            if log.details and log.details.get("resource_id") == filters.resource_id
        ]
    
    # Search in details
    if filters.search:
        search_lower = filters.search.lower()
        result = [
            log for log in result
            if (
                (log.action and search_lower in log.action.lower()) or
                (log.details and search_lower in json.dumps(log.details).lower())
            )
        ]
    
    return result


class AdminComplianceService:
    """
    Service for admin compliance operations.
    
    Requirements: 8.1, 8.2, 8.3 - Audit Logs & Security
    Requirements: 15.1, 15.2 - Compliance & Data Management
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the compliance service."""
        self.session = session
        # In-memory storage for data export and deletion requests (for demo)
        # In production, these would be database models
        self._data_export_requests: dict[uuid.UUID, dict] = {}
        self._deletion_requests: dict[uuid.UUID, dict] = {}
    
    async def get_audit_logs(
        self,
        filters: AuditLogFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:
        """
        Get audit logs with filtering and pagination.
        
        Requirements: 8.1 - Display all admin and system actions with timestamp, actor, action, and details
        Requirements: 8.2 - Support filter by date range, actor, action type, and target resource
        
        Property 18: Audit Log Filtering
        - For any audit log filter query with date_range, actor, action_type, and resource_type,
        - returned logs SHALL match ALL specified filter criteria.
        
        Args:
            filters: Filter criteria
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            AuditLogListResponse: Paginated audit logs
        """
        # Get all logs from the in-memory logger
        all_logs = AuditLogger.get_logs(limit=10000)
        
        # Apply filters
        filtered_logs = filter_audit_logs(all_logs, filters)
        
        # Sort by timestamp descending (most recent first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Calculate pagination
        total = len(filtered_logs)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        # Get page slice
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_logs = filtered_logs[start_idx:end_idx]
        
        # Convert to response format
        items = []
        for log in page_logs:
            # Extract resource info from details
            resource_type = None
            resource_id = None
            event = None
            if log.details:
                resource_type = log.details.get("resource_type")
                resource_id = log.details.get("resource_id")
                event = log.details.get("event")
            
            items.append(AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                actor_email=None,  # Would be populated from user lookup
                actor_name=None,
                action=log.action,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                timestamp=log.timestamp,
                resource_type=resource_type,
                resource_id=resource_id,
                event=event,
            ))
        
        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def export_audit_logs(
        self,
        filters: AuditLogFilters,
        format: str = "csv",
        admin_id: uuid.UUID = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLogExportResponse:
        """
        Export audit logs to CSV or JSON.
        
        Requirements: 8.3 - Generate CSV with all log fields for compliance purposes
        
        Args:
            filters: Filter criteria
            format: Export format (csv or json)
            admin_id: Admin performing the export
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AuditLogExportResponse: Export result with download URL
        """
        # Get all logs from the in-memory logger
        all_logs = AuditLogger.get_logs(limit=100000)
        
        # Apply filters
        filtered_logs = filter_audit_logs(all_logs, filters)
        
        # Sort by timestamp descending
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Generate export content
        export_id = uuid.uuid4()
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "id", "user_id", "action", "timestamp", "ip_address", 
                "user_agent", "resource_type", "resource_id", "event", "details"
            ])
            
            # Write data
            for log in filtered_logs:
                resource_type = log.details.get("resource_type") if log.details else None
                resource_id = log.details.get("resource_id") if log.details else None
                event = log.details.get("event") if log.details else None
                
                writer.writerow([
                    str(log.id),
                    str(log.user_id) if log.user_id else "",
                    log.action,
                    log.timestamp.isoformat(),
                    log.ip_address or "",
                    log.user_agent or "",
                    resource_type or "",
                    resource_id or "",
                    event or "",
                    json.dumps(log.details) if log.details else "",
                ])
            
            content = output.getvalue()
            file_size = len(content.encode('utf-8'))
        else:
            # JSON format
            data = [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "details": log.details,
                }
                for log in filtered_logs
            ]
            content = json.dumps(data, indent=2)
            file_size = len(content.encode('utf-8'))
        
        # Log the export action
        if admin_id:
            AdminAuditService.log(
                admin_id=admin_id,
                admin_user_id=admin_id,
                event=AdminAuditEvent.AUDIT_LOG_EXPORTED,
                details={
                    "export_id": str(export_id),
                    "format": format,
                    "record_count": len(filtered_logs),
                    "filters": filters.model_dump(exclude_none=True),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        # In production, this would upload to S3/storage and return a signed URL
        download_url = f"/admin/audit-logs/download/{export_id}.{format}"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return AuditLogExportResponse(
            export_id=export_id,
            format=format,
            record_count=len(filtered_logs),
            file_size_bytes=file_size,
            download_url=download_url,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
    
    async def get_security_dashboard(self) -> SecurityDashboardResponse:
        """
        Get security dashboard data.
        
        Requirements: 8.4, 8.5 - Show failed login attempts, suspicious IPs, and security events
        
        Returns:
            SecurityDashboardResponse: Security dashboard data
        """
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # Get all logs
        all_logs = AuditLogger.get_logs(limit=10000)
        
        # Count failed login attempts
        failed_logins_24h = len([
            log for log in all_logs
            if log.action == "login_failed" and log.timestamp >= day_ago
        ])
        
        failed_logins_7d = len([
            log for log in all_logs
            if log.action == "login_failed" and log.timestamp >= week_ago
        ])
        
        # Aggregate suspicious IPs (IPs with multiple failed logins)
        ip_failures: dict[str, list[datetime]] = {}
        for log in all_logs:
            if log.action == "login_failed" and log.ip_address:
                if log.ip_address not in ip_failures:
                    ip_failures[log.ip_address] = []
                ip_failures[log.ip_address].append(log.timestamp)
        
        suspicious_ips = [
            SuspiciousIP(
                ip_address=ip,
                failed_attempts=len(attempts),
                last_attempt=max(attempts),
                blocked=len(attempts) >= 10,  # Block after 10 failures
                countries=[],  # Would be populated from GeoIP lookup
            )
            for ip, attempts in ip_failures.items()
            if len(attempts) >= 3  # Consider suspicious after 3 failures
        ]
        
        # Sort by failed attempts descending
        suspicious_ips.sort(key=lambda x: x.failed_attempts, reverse=True)
        suspicious_ips = suspicious_ips[:20]  # Top 20
        
        # Generate security events from logs
        security_events = []
        for log in all_logs[:50]:  # Recent 50 logs
            if log.action in ["login_failed", "admin_access_denied", "2fa_disable"]:
                severity = "high" if log.action == "admin_access_denied" else "medium"
                security_events.append(SecurityEvent(
                    id=log.id,
                    event_type=log.action,
                    severity=severity,
                    description=f"{log.action.replace('_', ' ').title()}",
                    user_id=log.user_id,
                    ip_address=log.ip_address,
                    details=log.details,
                    timestamp=log.timestamp,
                    resolved=False,
                ))
        
        blocked_ips_count = len([ip for ip in suspicious_ips if ip.blocked])
        
        return SecurityDashboardResponse(
            failed_login_attempts_24h=failed_logins_24h,
            failed_login_attempts_7d=failed_logins_7d,
            suspicious_ips=suspicious_ips,
            recent_security_events=security_events[:20],
            blocked_ips_count=blocked_ips_count,
            active_sessions_count=0,  # Would be populated from session store
        )
    
    async def get_data_export_requests(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> DataExportRequestListResponse:
        """
        Get data export requests.
        
        Requirements: 15.1 - List data export requests
        
        Args:
            page: Page number
            page_size: Items per page
            status: Filter by status
            
        Returns:
            DataExportRequestListResponse: Paginated list of requests
        """
        # In production, this would query the database
        # For now, return from in-memory storage
        requests = list(self._data_export_requests.values())
        
        if status:
            requests = [r for r in requests if r["status"] == status]
        
        # Sort by requested_at descending
        requests.sort(key=lambda x: x["requested_at"], reverse=True)
        
        total = len(requests)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_requests = requests[start_idx:end_idx]
        
        items = [
            DataExportRequestStatus(
                id=r["id"],
                user_id=r["user_id"],
                user_email=r.get("user_email"),
                user_name=r.get("user_name"),
                status=r["status"],
                requested_at=r["requested_at"],
                processed_at=r.get("processed_at"),
                completed_at=r.get("completed_at"),
                download_url=r.get("download_url"),
                expires_at=r.get("expires_at"),
                error_message=r.get("error_message"),
            )
            for r in page_requests
        ]
        
        return DataExportRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def process_data_export(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ProcessDataExportResponse:
        """
        Process a data export request.
        
        Requirements: 15.1 - Generate complete data package within 72 hours and notify user
        
        Property 16: Data Export Completion
        - For any data export request, the system SHALL generate complete data package
        - and update status to 'completed' with download_url within 72 hours.
        
        Args:
            request_id: ID of the export request
            admin_id: Admin processing the request
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ProcessDataExportResponse: Processing result
        """
        if request_id not in self._data_export_requests:
            raise DataExportRequestNotFoundError(f"Data export request {request_id} not found")
        
        request = self._data_export_requests[request_id]
        
        # Update status to processing
        request["status"] = "processing"
        request["processed_at"] = datetime.utcnow()
        
        # In production, this would trigger an async job to generate the export
        # For now, simulate completion
        request["status"] = "completed"
        request["completed_at"] = datetime.utcnow()
        request["download_url"] = f"/compliance/exports/{request_id}/download"
        request["expires_at"] = datetime.utcnow() + timedelta(days=7)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.DATA_EXPORT_PROCESSED,
            resource_type="data_export_request",
            resource_id=str(request_id),
            details={
                "user_id": str(request["user_id"]),
                "status": "completed",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ProcessDataExportResponse(
            request_id=request_id,
            status="completed",
            download_url=request["download_url"],
            expires_at=request["expires_at"],
            message="Data export completed successfully",
        )
    
    async def get_deletion_requests(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> DeletionRequestListResponse:
        """
        Get deletion requests.
        
        Requirements: 15.2 - Display pending deletions with countdown and cancel option
        
        Args:
            page: Page number
            page_size: Items per page
            status: Filter by status
            
        Returns:
            DeletionRequestListResponse: Paginated list of requests
        """
        requests = list(self._deletion_requests.values())
        
        if status:
            requests = [r for r in requests if r["status"] == status]
        
        # Sort by scheduled_for ascending (soonest first)
        requests.sort(key=lambda x: x["scheduled_for"])
        
        total = len(requests)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_requests = requests[start_idx:end_idx]
        
        now = datetime.utcnow()
        items = [
            DeletionRequestStatus(
                id=r["id"],
                user_id=r["user_id"],
                user_email=r.get("user_email"),
                user_name=r.get("user_name"),
                status=r["status"],
                requested_at=r["requested_at"],
                scheduled_for=r["scheduled_for"],
                days_remaining=max(0, (r["scheduled_for"] - now).days),
                processed_at=r.get("processed_at"),
                completed_at=r.get("completed_at"),
                cancelled_at=r.get("cancelled_at"),
                cancelled_by=r.get("cancelled_by"),
                cancellation_reason=r.get("cancellation_reason"),
            )
            for r in page_requests
        ]
        
        return DeletionRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def process_deletion(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ProcessDeletionResponse:
        """
        Process a deletion request.
        
        Requirements: 15.2 - Schedule deletion with 30-day grace period
        
        Property 17: Deletion Grace Period
        - For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
        
        Args:
            request_id: ID of the deletion request
            admin_id: Admin processing the request
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ProcessDeletionResponse: Processing result
        """
        if request_id not in self._deletion_requests:
            raise DeletionRequestNotFoundError(f"Deletion request {request_id} not found")
        
        request = self._deletion_requests[request_id]
        
        if request["status"] == "completed":
            raise DeletionRequestAlreadyProcessedError("Deletion request already completed")
        
        if request["status"] == "cancelled":
            raise DeletionRequestAlreadyCancelledError("Deletion request was cancelled")
        
        # Update status to processing
        request["status"] = "processing"
        request["processed_at"] = datetime.utcnow()
        
        # In production, this would trigger the actual deletion process
        # For now, mark as completed
        request["status"] = "completed"
        request["completed_at"] = datetime.utcnow()
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.DELETION_REQUEST_PROCESSED,
            resource_type="deletion_request",
            resource_id=str(request_id),
            details={
                "user_id": str(request["user_id"]),
                "status": "completed",
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ProcessDeletionResponse(
            request_id=request_id,
            user_id=request["user_id"],
            status="completed",
            scheduled_for=request["scheduled_for"],
            message="Deletion request processed successfully",
        )
    
    async def cancel_deletion(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CancelDeletionResponse:
        """
        Cancel a deletion request.
        
        Requirements: 15.2 - Cancel option for pending deletions
        
        Args:
            request_id: ID of the deletion request
            admin_id: Admin cancelling the request
            reason: Reason for cancellation
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            CancelDeletionResponse: Cancellation result
        """
        if request_id not in self._deletion_requests:
            raise DeletionRequestNotFoundError(f"Deletion request {request_id} not found")
        
        request = self._deletion_requests[request_id]
        
        if request["status"] == "completed":
            raise DeletionRequestAlreadyProcessedError("Cannot cancel completed deletion")
        
        if request["status"] == "cancelled":
            raise DeletionRequestAlreadyCancelledError("Deletion request already cancelled")
        
        # Cancel the request
        request["status"] = "cancelled"
        request["cancelled_at"] = datetime.utcnow()
        request["cancelled_by"] = admin_id
        request["cancellation_reason"] = reason
        
        return CancelDeletionResponse(
            request_id=request_id,
            user_id=request["user_id"],
            status="cancelled",
            cancelled_at=request["cancelled_at"],
            message="Deletion request cancelled successfully",
        )
    
    # Helper methods for creating test data
    def create_data_export_request(
        self,
        user_id: uuid.UUID,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> uuid.UUID:
        """Create a data export request (for testing)."""
        request_id = uuid.uuid4()
        self._data_export_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "status": "pending",
            "requested_at": datetime.utcnow(),
        }
        return request_id
    
    def create_deletion_request(
        self,
        user_id: uuid.UUID,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        requested_at: Optional[datetime] = None,
    ) -> uuid.UUID:
        """
        Create a deletion request (for testing).
        
        Property 17: Deletion Grace Period
        - scheduled_for date SHALL be exactly 30 days from requested_at.
        """
        request_id = uuid.uuid4()
        req_at = requested_at or datetime.utcnow()
        
        # Property 17: scheduled_for is exactly 30 days from requested_at
        scheduled_for = req_at + timedelta(days=30)
        
        self._deletion_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "status": "scheduled",
            "requested_at": req_at,
            "scheduled_for": scheduled_for,
        }
        return request_id



# ==================== Terms of Service Service (Requirements 15.4) ====================


class TermsOfServiceNotFoundError(Exception):
    """Raised when terms of service is not found."""
    pass


class TermsOfServiceAlreadyActiveError(Exception):
    """Raised when trying to activate already active terms."""
    pass


class TermsOfServiceVersionExistsError(Exception):
    """Raised when version already exists."""
    pass


class AdminTermsOfServiceService:
    """
    Service for managing terms of service versions.
    
    Requirements: 15.4 - Terms of service versioning
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the terms of service service."""
        self.session = session
    
    async def create_terms_of_service(
        self,
        version: str,
        title: str,
        content: str,
        admin_id: uuid.UUID,
        content_html: Optional[str] = None,
        summary: Optional[str] = None,
        effective_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Create a new terms of service version.
        
        Requirements: 15.4 - Create new version
        
        Args:
            version: Version identifier
            title: Title of the terms
            content: Plain text content
            admin_id: Admin creating the terms
            content_html: HTML formatted content
            summary: Summary of changes
            effective_date: When terms become effective
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            TermsOfService: Created terms of service
        """
        from app.modules.admin.models import TermsOfService, TermsOfServiceStatus
        
        # Check if version already exists
        existing = await self.session.execute(
            select(TermsOfService).where(TermsOfService.version == version)
        )
        if existing.scalar_one_or_none():
            raise TermsOfServiceVersionExistsError(f"Version {version} already exists")
        
        # Create new terms
        terms = TermsOfService(
            version=version,
            title=title,
            content=content,
            content_html=content_html,
            summary=summary,
            status=TermsOfServiceStatus.DRAFT.value,
            effective_date=effective_date,
            created_by=admin_id,
        )
        
        self.session.add(terms)
        await self.session.commit()
        await self.session.refresh(terms)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.TERMS_CREATED,
            resource_type="terms_of_service",
            resource_id=str(terms.id),
            details={
                "version": version,
                "title": title,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return terms
    
    async def get_terms_of_service_list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ):
        """
        Get list of terms of service versions.
        
        Requirements: 15.4 - List versions
        
        Args:
            page: Page number
            page_size: Items per page
            status: Filter by status
            
        Returns:
            Paginated list of terms
        """
        from app.modules.admin.models import TermsOfService
        from app.modules.admin.compliance_schemas import (
            TermsOfServiceResponse,
            TermsOfServiceListResponse,
        )
        
        # Build query
        query = select(TermsOfService)
        
        if status:
            query = query.where(TermsOfService.status == status)
        
        # Order by created_at descending
        query = query.order_by(desc(TermsOfService.created_at))
        
        # Get total count
        count_query = select(func.count()).select_from(TermsOfService)
        if status:
            count_query = count_query.where(TermsOfService.status == status)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        terms_list = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        items = [
            TermsOfServiceResponse(
                id=t.id,
                version=t.version,
                title=t.title,
                content=t.content,
                content_html=t.content_html,
                summary=t.summary,
                status=t.status,
                effective_date=t.effective_date,
                created_by=t.created_by,
                activated_by=t.activated_by,
                activated_at=t.activated_at,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in terms_list
        ]
        
        return TermsOfServiceListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def activate_terms_of_service(
        self,
        terms_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Activate a terms of service version.
        
        Requirements: 15.4 - Activate version and require user acceptance on next login
        
        Args:
            terms_id: ID of the terms to activate
            admin_id: Admin activating the terms
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ActivateTermsOfServiceResponse: Activation result
        """
        from app.modules.admin.models import TermsOfService, TermsOfServiceStatus
        from app.modules.admin.compliance_schemas import ActivateTermsOfServiceResponse
        
        # Get the terms
        result = await self.session.execute(
            select(TermsOfService).where(TermsOfService.id == terms_id)
        )
        terms = result.scalar_one_or_none()
        
        if not terms:
            raise TermsOfServiceNotFoundError(f"Terms of service {terms_id} not found")
        
        if terms.status == TermsOfServiceStatus.ACTIVE.value:
            raise TermsOfServiceAlreadyActiveError("Terms of service is already active")
        
        # Archive any currently active terms
        await self.session.execute(
            select(TermsOfService)
            .where(TermsOfService.status == TermsOfServiceStatus.ACTIVE.value)
        )
        active_terms = await self.session.execute(
            select(TermsOfService).where(
                TermsOfService.status == TermsOfServiceStatus.ACTIVE.value
            )
        )
        for active in active_terms.scalars().all():
            active.status = TermsOfServiceStatus.ARCHIVED.value
        
        # Activate the new terms
        terms.status = TermsOfServiceStatus.ACTIVE.value
        terms.activated_by = admin_id
        terms.activated_at = datetime.utcnow()
        
        if not terms.effective_date:
            terms.effective_date = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(terms)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.TERMS_ACTIVATED,
            resource_type="terms_of_service",
            resource_id=str(terms.id),
            details={
                "version": terms.version,
                "title": terms.title,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ActivateTermsOfServiceResponse(
            id=terms.id,
            version=terms.version,
            status=terms.status,
            activated_at=terms.activated_at,
            message=f"Terms of service version {terms.version} activated successfully",
        )


# ==================== Compliance Report Service (Requirements 15.5) ====================


class ComplianceReportNotFoundError(Exception):
    """Raised when compliance report is not found."""
    pass


class AdminComplianceReportService:
    """
    Service for generating compliance reports.
    
    Requirements: 15.5 - Compliance report generation
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the compliance report service."""
        self.session = session
    
    async def create_compliance_report(
        self,
        report_type: str,
        title: str,
        admin_id: uuid.UUID,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        parameters: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Create and generate a compliance report.
        
        Requirements: 15.5 - Generate audit-ready report
        
        Args:
            report_type: Type of report
            title: Report title
            admin_id: Admin requesting the report
            description: Report description
            start_date: Report period start
            end_date: Report period end
            parameters: Additional parameters
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ComplianceReport: Created report
        """
        from app.modules.admin.models import ComplianceReport, ComplianceReportStatus
        from app.modules.admin.compliance_schemas import ComplianceReportResponse
        
        # Create the report
        report = ComplianceReport(
            report_type=report_type,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters,
            status=ComplianceReportStatus.PENDING.value,
            requested_by=admin_id,
        )
        
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        
        # In production, this would trigger an async job to generate the report
        # For now, simulate generation
        report.status = ComplianceReportStatus.GENERATING.value
        await self.session.commit()
        
        # Simulate completion
        report.status = ComplianceReportStatus.COMPLETED.value
        report.completed_at = datetime.utcnow()
        report.download_url = f"/admin/compliance/reports/{report.id}/download"
        report.expires_at = datetime.utcnow() + timedelta(days=30)
        report.file_size = 1024 * 100  # Simulated 100KB
        
        await self.session.commit()
        await self.session.refresh(report)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.COMPLIANCE_REPORT_GENERATED,
            resource_type="compliance_report",
            resource_id=str(report.id),
            details={
                "report_type": report_type,
                "title": title,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return ComplianceReportResponse(
            id=report.id,
            report_type=report.report_type,
            title=report.title,
            description=report.description,
            start_date=report.start_date,
            end_date=report.end_date,
            parameters=report.parameters,
            status=report.status,
            error_message=report.error_message,
            file_path=report.file_path,
            file_size=report.file_size,
            download_url=report.download_url,
            expires_at=report.expires_at,
            requested_by=report.requested_by,
            created_at=report.created_at,
            completed_at=report.completed_at,
        )
    
    async def get_compliance_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """
        Get list of compliance reports.
        
        Requirements: 15.5 - List reports
        
        Args:
            page: Page number
            page_size: Items per page
            report_type: Filter by report type
            status: Filter by status
            
        Returns:
            Paginated list of reports
        """
        from app.modules.admin.models import ComplianceReport
        from app.modules.admin.compliance_schemas import (
            ComplianceReportResponse,
            ComplianceReportListResponse,
        )
        
        # Build query
        query = select(ComplianceReport)
        
        if report_type:
            query = query.where(ComplianceReport.report_type == report_type)
        
        if status:
            query = query.where(ComplianceReport.status == status)
        
        # Order by created_at descending
        query = query.order_by(desc(ComplianceReport.created_at))
        
        # Get total count
        count_query = select(func.count()).select_from(ComplianceReport)
        if report_type:
            count_query = count_query.where(ComplianceReport.report_type == report_type)
        if status:
            count_query = count_query.where(ComplianceReport.status == status)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        reports = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        items = [
            ComplianceReportResponse(
                id=r.id,
                report_type=r.report_type,
                title=r.title,
                description=r.description,
                start_date=r.start_date,
                end_date=r.end_date,
                parameters=r.parameters,
                status=r.status,
                error_message=r.error_message,
                file_path=r.file_path,
                file_size=r.file_size,
                download_url=r.download_url,
                expires_at=r.expires_at,
                requested_by=r.requested_by,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in reports
        ]
        
        return ComplianceReportListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
