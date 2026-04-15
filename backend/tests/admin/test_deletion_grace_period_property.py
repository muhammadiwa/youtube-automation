"""Property-based tests for deletion grace period.

**Feature: admin-panel, Property 17: Deletion Grace Period**
**Validates: Requirements 15.2**

For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st, assume
import pytest


# Grace period in days (30 days as per requirements)
GRACE_PERIOD_DAYS = 30


@dataclass
class DeletionRequest:
    """Deletion request for testing."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: str  # pending, scheduled, processing, completed, cancelled
    requested_at: datetime
    scheduled_for: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[uuid.UUID] = None
    cancellation_reason: Optional[str] = None


def create_deletion_request(
    user_id: uuid.UUID,
    requested_at: Optional[datetime] = None,
) -> DeletionRequest:
    """
    Create a deletion request with proper grace period.
    
    Property 17: Deletion Grace Period
    - scheduled_for date SHALL be exactly 30 days from requested_at.
    
    Args:
        user_id: User requesting deletion
        requested_at: When the request was made (defaults to now)
        
    Returns:
        DeletionRequest: The created request
    """
    request_id = uuid.uuid4()
    req_at = requested_at or datetime.utcnow()
    
    # Property 17: scheduled_for is exactly 30 days from requested_at
    scheduled_for = req_at + timedelta(days=GRACE_PERIOD_DAYS)
    
    return DeletionRequest(
        id=request_id,
        user_id=user_id,
        status="scheduled",
        requested_at=req_at,
        scheduled_for=scheduled_for,
    )


def calculate_days_remaining(request: DeletionRequest, current_time: Optional[datetime] = None) -> int:
    """
    Calculate days remaining until scheduled deletion.
    
    Args:
        request: The deletion request
        current_time: Current time (defaults to now)
        
    Returns:
        int: Days remaining (0 if past scheduled date)
    """
    now = current_time or datetime.utcnow()
    remaining = request.scheduled_for - now
    return max(0, remaining.days)


def is_grace_period_valid(request: DeletionRequest) -> bool:
    """
    Check if the grace period is exactly 30 days.
    
    Property 17: Deletion Grace Period
    - scheduled_for date SHALL be exactly 30 days from requested_at.
    
    Args:
        request: The deletion request
        
    Returns:
        bool: True if grace period is exactly 30 days
    """
    expected_scheduled = request.requested_at + timedelta(days=GRACE_PERIOD_DAYS)
    
    # Allow for small time differences (within 1 second)
    diff = abs((request.scheduled_for - expected_scheduled).total_seconds())
    return diff < 1


class DeletionService:
    """
    Service for managing deletion requests.
    
    Property 17: Deletion Grace Period
    - For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
    """
    
    def __init__(self):
        """Initialize the service."""
        self._requests: dict[uuid.UUID, DeletionRequest] = {}
    
    def create_request(
        self,
        user_id: uuid.UUID,
        requested_at: Optional[datetime] = None,
    ) -> DeletionRequest:
        """
        Create a deletion request.
        
        Property 17: scheduled_for SHALL be exactly 30 days from requested_at.
        
        Args:
            user_id: User requesting deletion
            requested_at: When the request was made
            
        Returns:
            DeletionRequest: The created request
        """
        request = create_deletion_request(user_id, requested_at)
        self._requests[request.id] = request
        return request
    
    def process_request(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        current_time: Optional[datetime] = None,
    ) -> DeletionRequest:
        """
        Process a deletion request.
        
        Args:
            request_id: ID of the request to process
            admin_id: Admin processing the request
            current_time: Current time (for testing)
            
        Returns:
            DeletionRequest: The processed request
            
        Raises:
            ValueError: If request not found or already processed/cancelled
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self._requests[request_id]
        now = current_time or datetime.utcnow()
        
        if request.status == "completed":
            raise ValueError("Request already completed")
        
        if request.status == "cancelled":
            raise ValueError("Request was cancelled")
        
        request.status = "processing"
        request.processed_at = now
        
        # Complete the deletion
        request.status = "completed"
        request.completed_at = now
        
        return request
    
    def cancel_request(
        self,
        request_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> DeletionRequest:
        """
        Cancel a deletion request.
        
        Args:
            request_id: ID of the request to cancel
            admin_id: Admin cancelling the request
            reason: Reason for cancellation
            current_time: Current time (for testing)
            
        Returns:
            DeletionRequest: The cancelled request
            
        Raises:
            ValueError: If request not found or already processed/cancelled
        """
        if request_id not in self._requests:
            raise ValueError(f"Request {request_id} not found")
        
        request = self._requests[request_id]
        now = current_time or datetime.utcnow()
        
        if request.status == "completed":
            raise ValueError("Cannot cancel completed request")
        
        if request.status == "cancelled":
            raise ValueError("Request already cancelled")
        
        request.status = "cancelled"
        request.cancelled_at = now
        request.cancelled_by = admin_id
        request.cancellation_reason = reason
        
        return request
    
    def get_request(self, request_id: uuid.UUID) -> Optional[DeletionRequest]:
        """Get a request by ID."""
        return self._requests.get(request_id)


# Strategies for generating test data
uuid_strategy = st.uuids()
timestamp_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2025, 12, 31),
)


class TestDeletionGracePeriod:
    """
    Property tests for deletion grace period.
    
    **Feature: admin-panel, Property 17: Deletion Grace Period**
    **Validates: Requirements 15.2**
    """

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_scheduled_for_is_exactly_30_days_from_requested_at(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
        """
        request = create_deletion_request(user_id, requested_at)
        
        expected_scheduled = requested_at + timedelta(days=GRACE_PERIOD_DAYS)
        
        # Allow for small time differences (within 1 second)
        diff = abs((request.scheduled_for - expected_scheduled).total_seconds())
        
        assert diff < 1, (
            f"scheduled_for {request.scheduled_for} should be exactly 30 days from "
            f"requested_at {requested_at}. Expected {expected_scheduled}"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_grace_period_is_valid(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        For any deletion request, is_grace_period_valid SHALL return True.
        """
        request = create_deletion_request(user_id, requested_at)
        
        assert is_grace_period_valid(request), (
            f"Grace period should be valid. requested_at={requested_at}, "
            f"scheduled_for={request.scheduled_for}"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_days_remaining_at_creation_is_30(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        At creation time, days_remaining SHALL be 30.
        """
        request = create_deletion_request(user_id, requested_at)
        
        # Calculate days remaining at the time of request
        days = calculate_days_remaining(request, requested_at)
        
        assert days == GRACE_PERIOD_DAYS, (
            f"Days remaining at creation should be {GRACE_PERIOD_DAYS}, got {days}"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
        days_elapsed=st.integers(min_value=0, max_value=29),
    )
    @settings(max_examples=100)
    def test_days_remaining_decreases_correctly(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
        days_elapsed: int,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        As time passes, days_remaining SHALL decrease correctly.
        """
        request = create_deletion_request(user_id, requested_at)
        
        # Calculate days remaining after some time has passed
        current_time = requested_at + timedelta(days=days_elapsed)
        days = calculate_days_remaining(request, current_time)
        
        expected_days = GRACE_PERIOD_DAYS - days_elapsed
        
        assert days == expected_days, (
            f"After {days_elapsed} days, remaining should be {expected_days}, got {days}"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
        days_past_scheduled=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_days_remaining_is_zero_after_scheduled(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
        days_past_scheduled: int,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        After scheduled_for date, days_remaining SHALL be 0.
        """
        request = create_deletion_request(user_id, requested_at)
        
        # Calculate days remaining after scheduled date
        current_time = request.scheduled_for + timedelta(days=days_past_scheduled)
        days = calculate_days_remaining(request, current_time)
        
        assert days == 0, (
            f"Days remaining after scheduled date should be 0, got {days}"
        )

    @given(
        user_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_service_creates_request_with_valid_grace_period(
        self,
        user_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        Service SHALL create requests with valid 30-day grace period.
        """
        service = DeletionService()
        request = service.create_request(user_id, requested_at)
        
        assert is_grace_period_valid(request), (
            "Service should create requests with valid grace period"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_cancelled_request_preserves_scheduled_for(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        Cancelling a request SHALL preserve the original scheduled_for date.
        """
        service = DeletionService()
        request = service.create_request(user_id, requested_at)
        original_scheduled = request.scheduled_for
        
        cancelled = service.cancel_request(request.id, admin_id)
        
        assert cancelled.scheduled_for == original_scheduled, (
            "Cancellation should preserve scheduled_for date"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_cancelled_request_has_cancelled_status(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        Cancelled request SHALL have status 'cancelled'.
        """
        service = DeletionService()
        request = service.create_request(user_id, requested_at)
        
        cancelled = service.cancel_request(request.id, admin_id)
        
        assert cancelled.status == "cancelled", (
            f"Expected status 'cancelled', got '{cancelled.status}'"
        )

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_cannot_cancel_completed_request(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        Completed requests SHALL NOT be cancellable.
        """
        service = DeletionService()
        request = service.create_request(user_id, requested_at)
        
        # Process the request
        service.process_request(request.id, admin_id)
        
        # Try to cancel
        with pytest.raises(ValueError, match="Cannot cancel completed"):
            service.cancel_request(request.id, admin_id)

    @given(
        user_id=uuid_strategy,
        admin_id=uuid_strategy,
        requested_at=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_cannot_cancel_already_cancelled_request(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        requested_at: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 17: Deletion Grace Period**
        
        Already cancelled requests SHALL NOT be cancellable again.
        """
        service = DeletionService()
        request = service.create_request(user_id, requested_at)
        
        # Cancel the request
        service.cancel_request(request.id, admin_id)
        
        # Try to cancel again
        with pytest.raises(ValueError, match="already cancelled"):
            service.cancel_request(request.id, admin_id)
