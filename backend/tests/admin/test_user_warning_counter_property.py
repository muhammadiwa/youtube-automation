"""Property-based tests for User Warning Counter.

**Feature: admin-panel, Property 11: User Warning Counter**
**Validates: Requirements 6.5**

Property 11: User Warning Counter
*For any* user warning action, the user's warning_count SHALL increment by 1 
and a UserWarning record SHALL be created.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings


# ==================== Data Classes ====================

@dataclass
class User:
    """User for testing."""
    id: uuid.UUID
    email: str
    name: str
    is_active: bool = True


@dataclass
class UserWarning:
    """User warning record for testing."""
    id: uuid.UUID
    user_id: uuid.UUID
    admin_id: uuid.UUID
    reason: str
    warning_number: int
    related_report_id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserWarnResult:
    """Result of user warning operation."""
    warning_id: uuid.UUID
    user_id: uuid.UUID
    warning_number: int
    reason: str
    notification_sent: bool
    created_at: datetime


# ==================== Mock Storage ====================

class MockWarningStorage:
    """Mock storage for testing user warning flow."""
    
    def __init__(self):
        self.warnings: list[UserWarning] = []
        self.notifications_sent: list[tuple[uuid.UUID, str, int]] = []
    
    def get_warning_count(self, user_id: uuid.UUID) -> int:
        """Get the number of warnings for a user."""
        return len([w for w in self.warnings if w.user_id == user_id])
    
    def create_warning(
        self,
        user_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: str,
        warning_number: int,
        related_report_id: Optional[uuid.UUID] = None,
    ) -> UserWarning:
        """Create a new warning record."""
        warning = UserWarning(
            id=uuid.uuid4(),
            user_id=user_id,
            admin_id=admin_id,
            reason=reason,
            warning_number=warning_number,
            related_report_id=related_report_id,
        )
        self.warnings.append(warning)
        return warning
    
    def send_warning_notification(
        self,
        user_id: uuid.UUID,
        reason: str,
        warning_number: int,
    ) -> bool:
        """Send warning notification to user."""
        self.notifications_sent.append((user_id, reason, warning_number))
        return True


# ==================== Warning Logic ====================

def warn_user(
    user: User,
    admin_id: uuid.UUID,
    reason: str,
    storage: MockWarningStorage,
    related_report_id: Optional[uuid.UUID] = None,
) -> UserWarnResult:
    """
    Issue a warning to a user.
    
    Property 11: User Warning Counter
    - For any user warning action, the user's warning_count SHALL increment by 1
    - A UserWarning record SHALL be created
    
    Args:
        user: User to warn
        admin_id: Admin performing the action
        reason: Reason for warning
        storage: Mock storage for testing
        related_report_id: Optional related content report ID
        
    Returns:
        UserWarnResult with warning details
    """
    # Get current warning count
    current_count = storage.get_warning_count(user.id)
    new_warning_number = current_count + 1
    
    # Create warning record
    warning = storage.create_warning(
        user_id=user.id,
        admin_id=admin_id,
        reason=reason,
        warning_number=new_warning_number,
        related_report_id=related_report_id,
    )
    
    # Send notification
    notification_sent = storage.send_warning_notification(
        user_id=user.id,
        reason=reason,
        warning_number=new_warning_number,
    )
    
    return UserWarnResult(
        warning_id=warning.id,
        user_id=user.id,
        warning_number=new_warning_number,
        reason=reason,
        notification_sent=notification_sent,
        created_at=warning.created_at,
    )


# ==================== Strategies ====================

reason_strategy = st.text(
    min_size=1,
    max_size=500,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')),
)


@st.composite
def user_strategy(draw):
    """Generate a random user."""
    return User(
        id=uuid.uuid4(),
        email=draw(st.emails()),
        name=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Z')))),
        is_active=True,
    )


# ==================== Property Tests ====================

class TestUserWarningCounter:
    """Property tests for User Warning Counter.
    
    **Feature: admin-panel, Property 11: User Warning Counter**
    **Validates: Requirements 6.5**
    """

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_warning_count_increments_by_one(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: Warning count SHALL increment by 1 for each warning.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        initial_count = storage.get_warning_count(user.id)
        assert initial_count == 0
        
        result = warn_user(user, admin_id, reason, storage)
        
        new_count = storage.get_warning_count(user.id)
        assert new_count == initial_count + 1
        assert result.warning_number == 1

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        num_warnings=st.integers(min_value=1, max_value=10),
    )
    def test_multiple_warnings_increment_correctly(
        self,
        user: User,
        num_warnings: int,
    ):
        """
        Property: Multiple warnings SHALL increment count correctly.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        for i in range(num_warnings):
            result = warn_user(user, admin_id, f"Warning reason {i+1}", storage)
            assert result.warning_number == i + 1
        
        final_count = storage.get_warning_count(user.id)
        assert final_count == num_warnings

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_warning_record_created(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: A UserWarning record SHALL be created for each warning.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        result = warn_user(user, admin_id, reason, storage)
        
        # Warning record should be created
        assert len(storage.warnings) == 1
        
        warning = storage.warnings[0]
        assert warning.id == result.warning_id
        assert warning.user_id == user.id
        assert warning.admin_id == admin_id
        assert warning.reason == reason

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_warning_number_matches_count(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: Warning number in record SHALL match the user's warning count.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        result = warn_user(user, admin_id, reason, storage)
        
        warning = storage.warnings[0]
        assert warning.warning_number == result.warning_number
        assert warning.warning_number == storage.get_warning_count(user.id)

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_notification_sent(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: A notification SHALL be sent to the user.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        result = warn_user(user, admin_id, reason, storage)
        
        assert result.notification_sent is True
        assert len(storage.notifications_sent) == 1
        
        notification = storage.notifications_sent[0]
        assert notification[0] == user.id  # user_id
        assert notification[1] == reason  # reason
        assert notification[2] == result.warning_number  # warning_number

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_reason_preserved(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: The warning reason SHALL be preserved in the record.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        result = warn_user(user, admin_id, reason, storage)
        
        assert result.reason == reason
        assert storage.warnings[0].reason == reason

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_admin_id_recorded(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: The admin ID SHALL be recorded in the warning.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        warn_user(user, admin_id, reason, storage)
        
        warning = storage.warnings[0]
        assert warning.admin_id == admin_id

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_related_report_id_optional(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: Related report ID SHALL be optional.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        # Without related report
        warn_user(user, admin_id, reason, storage)
        assert storage.warnings[0].related_report_id is None
        
        # With related report
        storage2 = MockWarningStorage()
        related_report_id = uuid.uuid4()
        warn_user(user, admin_id, reason, storage2, related_report_id)
        assert storage2.warnings[0].related_report_id == related_report_id

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_timestamp_set(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: Warning timestamp SHALL be set.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        before = datetime.utcnow()
        
        result = warn_user(user, admin_id, reason, storage)
        
        after = datetime.utcnow()
        
        assert result.created_at is not None
        assert before <= result.created_at <= after

    @settings(max_examples=100)
    @given(
        num_users=st.integers(min_value=2, max_value=5),
    )
    def test_warnings_isolated_per_user(
        self,
        num_users: int,
    ):
        """
        Property: Warnings for different users SHALL be isolated.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        users = [
            User(id=uuid.uuid4(), email=f"user{i}@test.com", name=f"User {i}")
            for i in range(num_users)
        ]
        
        # Give each user a different number of warnings
        for i, user in enumerate(users):
            for j in range(i + 1):
                warn_user(user, admin_id, f"Warning {j+1}", storage)
        
        # Verify each user has the correct count
        for i, user in enumerate(users):
            count = storage.get_warning_count(user.id)
            assert count == i + 1, f"User {i} should have {i+1} warnings, got {count}"

    @settings(max_examples=100)
    @given(
        user=user_strategy(),
        reason=reason_strategy,
    )
    def test_warning_id_unique(
        self,
        user: User,
        reason: str,
    ):
        """
        Property: Each warning SHALL have a unique ID.
        
        **Feature: admin-panel, Property 11: User Warning Counter**
        **Validates: Requirements 6.5**
        """
        storage = MockWarningStorage()
        admin_id = uuid.uuid4()
        
        result1 = warn_user(user, admin_id, reason, storage)
        result2 = warn_user(user, admin_id, reason, storage)
        
        assert result1.warning_id != result2.warning_id
