"""Property-based tests for audit logging.

**Feature: youtube-automation, Property 3: Audit Trail Completeness**
**Validates: Requirements 1.3**
"""

import uuid

import pytest
from hypothesis import given, settings, strategies as st

from app.modules.auth.audit import (
    AuditAction,
    AuditLogger,
    audit_login,
    audit_logout,
    audit_password_change,
)

uuid_strategy = st.uuids()
action_strategy = st.sampled_from(list(AuditAction))
ip_strategy = st.one_of(
    st.just(None),
    st.from_regex(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", fullmatch=True),
)
details_strategy = st.one_of(
    st.just(None),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
        values=st.one_of(st.text(max_size=100), st.integers(), st.booleans()),
        max_size=5,
    ),
)


class TestAuditTrailCompleteness:
    """Property tests for audit trail completeness."""

    @pytest.fixture(autouse=True)
    def clear_logs(self):
        """Clear audit logs before each test."""
        AuditLogger.clear()
        yield
        AuditLogger.clear()

    @given(user_id=uuid_strategy, action=action_strategy, details=details_strategy, ip_address=ip_strategy)
    @settings(max_examples=100)
    def test_audit_log_contains_user_id(self, user_id, action, details, ip_address) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = AuditLogger.log(action=action, user_id=user_id, details=details, ip_address=ip_address)
        assert entry.user_id == user_id


    @given(user_id=uuid_strategy, action=action_strategy)
    @settings(max_examples=100)
    def test_audit_log_contains_action_type(self, user_id, action) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = AuditLogger.log(action=action, user_id=user_id)
        assert entry.action == action.value

    @given(user_id=uuid_strategy, action=action_strategy)
    @settings(max_examples=100)
    def test_audit_log_contains_timestamp(self, user_id, action) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = AuditLogger.log(action=action, user_id=user_id)
        assert entry.timestamp is not None

    @given(user_id=uuid_strategy, action=action_strategy, details=details_strategy)
    @settings(max_examples=100)
    def test_audit_log_contains_details(self, user_id, action, details) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = AuditLogger.log(action=action, user_id=user_id, details=details)
        assert entry.details == details

    @given(user_id=uuid_strategy, count=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_all_actions_are_logged(self, user_id, count) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        for i in range(count):
            AuditLogger.log(action=AuditAction.LOGIN, user_id=user_id, details={"attempt": i})
        assert AuditLogger.count() == count

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_login_audit_contains_required_fields(self, user_id) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = audit_login(user_id=user_id, success=True)
        assert entry.user_id == user_id
        assert entry.action == AuditAction.LOGIN.value
        assert entry.timestamp is not None

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_failed_login_audit_records_failure(self, user_id) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = audit_login(user_id=user_id, success=False)
        assert entry.action == AuditAction.LOGIN_FAILED.value

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_logout_audit_contains_required_fields(self, user_id) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = audit_logout(user_id=user_id)
        assert entry.user_id == user_id
        assert entry.action == AuditAction.LOGOUT.value

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_password_change_audit_contains_required_fields(self, user_id) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        entry = audit_password_change(user_id=user_id)
        assert entry.user_id == user_id
        assert entry.action == AuditAction.PASSWORD_CHANGE.value

    @given(user_id=uuid_strategy)
    @settings(max_examples=100)
    def test_logs_can_be_filtered_by_user(self, user_id) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        other_user = uuid.uuid4()
        AuditLogger.log(action=AuditAction.LOGIN, user_id=user_id)
        AuditLogger.log(action=AuditAction.LOGIN, user_id=other_user)
        AuditLogger.log(action=AuditAction.LOGOUT, user_id=user_id)
        user_logs = AuditLogger.get_logs_for_user(user_id)
        assert len(user_logs) == 2
        for log in user_logs:
            assert log.user_id == user_id

    @given(action=action_strategy)
    @settings(max_examples=100)
    def test_logs_can_be_filtered_by_action(self, action) -> None:
        """**Feature: youtube-automation, Property 3: Audit Trail Completeness**"""
        AuditLogger.clear()
        user_id = uuid.uuid4()
        AuditLogger.log(action=action, user_id=user_id)
        AuditLogger.log(action=AuditAction.ADMIN_ACTION, user_id=user_id)
        AuditLogger.log(action=action, user_id=user_id)
        action_logs = AuditLogger.get_logs_by_action(action.value)
        for log in action_logs:
            assert log.action == action.value
