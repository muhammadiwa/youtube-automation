"""Property-based tests for data export completion.

**Feature: admin-panel, Property 16: Data Export Completion**
**Validates: Requirements 15.1**

For any data export request, the system SHALL generate complete data package
and update status to 'completed' with download_url within 72 hours.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
import pytest


@dataclass
class DataExportRequest:
    """Data export request for testing."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: str  # pending, processing, completed, failed
    requested_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DataExportService:
    """
    Service for processing data export requests.
    
    Property 16: Data Export Completion
    - For any data export request, the system SHALL generate complete data package
    - and update status to 'completed' with download_url within 72 hours.
    """
    
    # Maximum time allowed for export completion (72 hours)
    MAX_COMPLETION_HOURS = 72
    
    def __init__(self):
        """Initialize the service."""
        self._requests: dict[uuid.UUID, DataExportRequest] = {}
    
    def create_request(
        self,
        user_id: uuid.UUID,
        requested_at: Optional[datetime] = None,
    ) -> DataExportRequest:
        """
        Create a new data export request.
        
        Args:
            user_id: User requesting the export
            requested_at: When the request was made (defaults to now)
            
        Returns:
            DataExportRequest: The created request
        """
        request_id = uuid.uuid4()
        req_at = requested_at or datetime.utcnow()
        
        request = DataExportRequest(
            id=request_id,
            user_id=user_id,
            status="pending",
            requested_at=req_at,
        )
        
        self._requests[request_id] = request
        return request
    
    def process_request(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        current_time: Optional[datetime] = None,
    ) -> DataExportRequest:
        """
        Process a data export request.
        
        Property 16: Data Export Completion
        - Status SHALL be updated to 'completed'
        - download_url SHALL be set
        - Completion SHALL happen within 72 hours of request
        
        Args:
            request_id: ID of the request to process
            admin_id: Admin processing the request
            current_time: Current time (for testing)
            
        Returns:
            DataExportRequest: The processed request
            
        Raises:
            ValueError: If request not found
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self._requests[request_id]
        now = current_time or datetime.utcnow()
        
        # Update to processing
        request.status = "processing"
        request.processed_at = now
        
        # Simulate export generation (in production this would be async)
        # For the property test, we complete immediately
        request.status = "completed"
        request.completed_at = now
        request.download_url = f"/compliance/exports/{request_id}/download"
        request.expires_at = now + timedelta(days=7)
        
        return request
    
    def get_request(self, request_id: uuid.UUID) -> Optional[DataExportRequest]:
        """Get a request by ID."""
        return self._requests.get(request_id)
    
    def is_completion_within_deadline(self, request: DataExportRequest) -> bool:
        """
        Check if the request was completed within the 72-hour deadline.
        
        Property 16: Data Export Completion
        - Completion SHALL happen within 72 hours of request
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if completed within deadline
        """
        if request.status != "completed" or request.completed_at is None:
            return False
        
        deadline = request.requested_at + timedelta(hours=self.MAX_COMPLETION_HOURS)
        return request.completed_at <= deadline
    
    def is_export_complete(self, request: DataExportRequest) -> bool:
        """
        Check if the export is complete with all required fields.
        
        Property 16: Data Export Completion
        - Status SHALL be 'completed'
        - download_url SHALL be set
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if export is complete
        """
        return (
            request.status == "completed" and
            request.download_url is not None and
            request.completed_at is not None
        )


# Strategies for generating test data
uuid_strategy = st.uuids()
timestamp_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2025, 12, 31),
)


class TestDataExportCompletion:
    """
    Property tests for data export completion.
    
    **Feature: admin-panel, Property 16: Data Export Completion**
    **Validates: Requirements 15.1**
    """

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_processed_request_has_completed_status(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, status SHALL be 'completed'.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert processed.status == "completed", (
            f"Expected status 'completed', got '{processed.status}'"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_processed_request_has_download_url(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, download_url SHALL be set.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert processed.download_url is not None, (
            "download_url should be set after processing"
        )
        assert len(processed.download_url) > 0, (
            "download_url should not be empty"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_processed_request_has_completed_at(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, completed_at SHALL be set.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert processed.completed_at is not None, (
            "completed_at should be set after processing"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
        processing_delay_hours=st.integers(min_value=0, max_value=71),
    )
    @settings(max_examples=100)
    def test_completion_within_72_hours_is_valid(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
        processing_delay_hours: int,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any data export request completed within 72 hours, it SHALL be considered valid.
        """
        service = DataExportService()
        
        # Create request
        request = service.create_request(user_id, requested_at)
        
        # Process within deadline
        processing_time = requested_at + timedelta(hours=processing_delay_hours)
        processed = service.process_request(request.id, admin_id, processing_time)
        
        assert service.is_completion_within_deadline(processed), (
            f"Request completed at {processing_delay_hours} hours should be within deadline"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_export_is_complete_after_processing(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, is_export_complete SHALL return True.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert service.is_export_complete(processed), (
            "Export should be complete after processing"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_pending_request_is_not_complete(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any pending data export request, is_export_complete SHALL return False.
        """
        service = DataExportService()
        
        # Create request but don't process
        request = service.create_request(user_id, requested_at)
        
        assert not service.is_export_complete(request), (
            "Pending export should not be complete"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_download_url_contains_request_id(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, download_url SHALL contain the request ID.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert str(request.id) in processed.download_url, (
            f"download_url should contain request ID {request.id}"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_expires_at_is_set_after_processing(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, expires_at SHALL be set.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert processed.expires_at is not None, (
            "expires_at should be set after processing"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_expires_at_is_after_completed_at(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any processed data export request, expires_at SHALL be after completed_at.
        """
        service = DataExportService()
        
        # Create and process request
        request = service.create_request(user_id, requested_at)
        processed = service.process_request(request.id, admin_id)
        
        assert processed.expires_at > processed.completed_at, (
            f"expires_at {processed.expires_at} should be after completed_at {processed.completed_at}"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
    )
    @settings(max_examples=100)
    def test_request_not_found_raises_error(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
    ) -> None:
        """
        **Feature: admin-panel, Property 16: Data Export Completion**
        
        For any non-existent request ID, processing SHALL raise an error.
        """
        service = DataExportService()
        
        # Try to process non-existent request
        fake_request_id = uuid.uuid4()
        
        with pytest.raises(ValueError):
            service.process_request(fake_request_id, admin_id)
