"""Property-based tests for User Activation Flow.

**Feature: admin-panel, Property 5: User Activation Flow**
**Validates: Requirements 3.4**

Property 5: User Activation Flow
*For any* user activation action on suspended user, the system SHALL set user status
to 'active' and mark paused jobs as ready for resume.
"""

import uuid
from datetime import datetime

import pytest
from hypothesis import given, strategies as st, settings

from app.modules.job.models import JobStatus


# ==================== Test Data Generators ====================

@st.composite
def suspended_user_strategy(draw):
    """Generate valid suspended user data for testing."""
    return {
        "id": uuid.uuid4(),
        "email": draw(st.emails()),
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')))),
        "is_active": False,  # User must be suspended to be activated
        "is_2fa_enabled": draw(st.booleans()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# ==================== Mock Classes for Testing ====================

class MockUser:
    """Mock user for testing activation flow."""
    
    def __init__(self, user_data: dict):
        self.id = user_data["id"]
        self.email = user_data["email"]
        self.name = user_data["name"]
        self.is_active = user_data["is_active"]
        self.is_2fa_enabled = user_data["is_2fa_enabled"]
        self.created_at = user_data["created_at"]
        self.updated_at = user_data["updated_at"]


class MockJob:
    """Mock job for testing activation flow."""
    
    def __init__(self, job_data: dict):
        self.id = job_data["id"]
        self.user_id = job_data["user_id"]
        self.job_type = job_data["job_type"]
        self.status = job_data["status"]
        self.payload = job_data["payload"]
        self.priority = job_data["priority"]
        self.created_at = job_data["created_at"]
        self.error = job_data.get("error")
        self.attempts = job_data.get("attempts", 0)


class ActivationResult:
    """Result of an activation operation."""
    
    def __init__(
        self,
        user_id: uuid.UUID,
        status: str,
        activated_at: datetime,
        jobs_resumed: int,
    ):
        self.user_id = user_id
        self.status = status
        self.activated_at = activated_at
        self.jobs_resumed = jobs_resumed


def activate_user_logic(
    user: MockUser,
    jobs: list[MockJob],
) -> ActivationResult:
    """
    Core activation logic extracted for property testing.
    
    This function implements the activation flow:
    1. Set user status to active (is_active = True)
    2. Resume all paused jobs (jobs that were paused due to suspension)
    
    Args:
        user: User to activate
        jobs: List of user's jobs
        
    Returns:
        ActivationResult with activation details
    """
    # 1. Set user status to active
    user.is_active = True
    
    # 2. Resume paused jobs (jobs that were failed due to suspension)
    jobs_resumed = 0
    for job in jobs:
        if job.status == JobStatus.FAILED.value and job.error == "User account suspended":
            job.status = JobStatus.QUEUED.value
            job.error = None
            job.attempts = 0
            jobs_resumed += 1
    
    return ActivationResult(
        user_id=user.id,
        status="active",
        activated_at=datetime.utcnow(),
        jobs_resumed=jobs_resumed,
    )


# ==================== Property Tests ====================

class TestUserActivationFlow:
    """Property tests for User Activation Flow.
    
    **Feature: admin-panel, Property 5: User Activation Flow**
    **Validates: Requirements 3.4**
    """

    @settings(max_examples=100)
    @given(user_data=suspended_user_strategy())
    def test_activation_sets_user_active(self, user_data: dict):
        """
        Property: Activating a suspended user SHALL set their status to active.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        assert user.is_active is False  # Pre-condition: user is suspended
        
        result = activate_user_logic(user, [])
        
        # User should now be active
        assert user.is_active is True
        assert result.status == "active"

    @settings(max_examples=100)
    @given(
        user_data=suspended_user_strategy(),
        num_paused_jobs=st.integers(min_value=0, max_value=10),
    )
    def test_activation_resumes_paused_jobs(
        self, user_data: dict, num_paused_jobs: int
    ):
        """
        Property: Activating a user SHALL resume all jobs paused due to suspension.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        
        # Create paused jobs (jobs that were failed due to suspension)
        jobs = []
        for _ in range(num_paused_jobs):
            job_data = {
                "id": uuid.uuid4(),
                "user_id": user.id,
                "job_type": "video_upload",
                "status": JobStatus.FAILED.value,
                "error": "User account suspended",
                "payload": {},
                "priority": 0,
                "created_at": datetime.utcnow(),
                "attempts": 1,
            }
            jobs.append(MockJob(job_data))
        
        result = activate_user_logic(user, jobs)
        
        # All paused jobs should be resumed (re-queued)
        assert result.jobs_resumed == num_paused_jobs
        for job in jobs:
            assert job.status == JobStatus.QUEUED.value
            assert job.error is None
            assert job.attempts == 0

    @settings(max_examples=100)
    @given(user_data=suspended_user_strategy())
    def test_activation_only_resumes_suspension_paused_jobs(self, user_data: dict):
        """
        Property: Activation SHALL only resume jobs paused due to suspension,
        not jobs that failed for other reasons.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        
        # Create jobs with different failure reasons
        suspension_paused_job = MockJob({
            "id": uuid.uuid4(),
            "user_id": user.id,
            "job_type": "video_upload",
            "status": JobStatus.FAILED.value,
            "error": "User account suspended",
            "payload": {},
            "priority": 0,
            "created_at": datetime.utcnow(),
            "attempts": 1,
        })
        
        other_failed_job = MockJob({
            "id": uuid.uuid4(),
            "user_id": user.id,
            "job_type": "video_upload",
            "status": JobStatus.FAILED.value,
            "error": "Network timeout",
            "payload": {},
            "priority": 0,
            "created_at": datetime.utcnow(),
            "attempts": 3,
        })
        
        completed_job = MockJob({
            "id": uuid.uuid4(),
            "user_id": user.id,
            "job_type": "video_upload",
            "status": JobStatus.COMPLETED.value,
            "error": None,
            "payload": {},
            "priority": 0,
            "created_at": datetime.utcnow(),
            "attempts": 1,
        })
        
        jobs = [suspension_paused_job, other_failed_job, completed_job]
        
        result = activate_user_logic(user, jobs)
        
        # Only the suspension-paused job should be resumed
        assert result.jobs_resumed == 1
        assert suspension_paused_job.status == JobStatus.QUEUED.value
        assert other_failed_job.status == JobStatus.FAILED.value
        assert other_failed_job.error == "Network timeout"
        assert completed_job.status == JobStatus.COMPLETED.value

    @settings(max_examples=100)
    @given(user_data=suspended_user_strategy())
    def test_activation_records_timestamp(self, user_data: dict):
        """
        Property: The activation SHALL record a timestamp.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        before = datetime.utcnow()
        
        result = activate_user_logic(user, [])
        
        after = datetime.utcnow()
        
        # Timestamp should be set and within bounds
        assert result.activated_at is not None
        assert before <= result.activated_at <= after

    @settings(max_examples=100)
    @given(user_data=suspended_user_strategy())
    def test_activation_resets_job_attempts(self, user_data: dict):
        """
        Property: Resumed jobs SHALL have their attempt counter reset to 0.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        
        # Create a paused job with some attempts
        job = MockJob({
            "id": uuid.uuid4(),
            "user_id": user.id,
            "job_type": "video_upload",
            "status": JobStatus.FAILED.value,
            "error": "User account suspended",
            "payload": {},
            "priority": 0,
            "created_at": datetime.utcnow(),
            "attempts": 5,  # Had some attempts before suspension
        })
        
        activate_user_logic(user, [job])
        
        # Attempts should be reset
        assert job.attempts == 0

    @settings(max_examples=100)
    @given(user_data=suspended_user_strategy())
    def test_activation_preserves_user_id(self, user_data: dict):
        """
        Property: The activation result SHALL contain the correct user ID.
        
        **Feature: admin-panel, Property 5: User Activation Flow**
        **Validates: Requirements 3.4**
        """
        user = MockUser(user_data)
        
        result = activate_user_logic(user, [])
        
        assert result.user_id == user.id
