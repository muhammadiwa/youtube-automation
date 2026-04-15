"""Property-based tests for audit log filtering.

**Feature: admin-panel, Property 18: Audit Log Filtering**
**Validates: Requirements 8.2**

For any audit log filter query with date_range, actor, action_type, and resource_type,
returned logs SHALL match ALL specified filter criteria.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional, List

from hypothesis import given, settings, strategies as st, assume
import pytest


@dataclass
class AuditLogEntry:
    """Audit log entry for testing."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogFilters:
    """Filters for audit log query."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    actor_id: Optional[uuid.UUID] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    search: Optional[str] = None


def filter_audit_logs(
    logs: List[AuditLogEntry],
    filters: AuditLogFilters,
) -> List[AuditLogEntry]:
    """
    Filter audit logs based on provided criteria.
    
    Property 18: Audit Log Filtering
    - For any audit log filter query with date_range, actor, action_type, and resource_type,
    - returned logs SHALL match ALL specified filter criteria.
    
    Args:
        logs: List of audit log entries to filter
        filters: Filter criteria
        
    Returns:
        List[AuditLogEntry]: Filtered audit log entries
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
    
    # Search in action and details
    if filters.search:
        search_lower = filters.search.lower()
        result = [
            log for log in result
            if (
                (log.action and search_lower in log.action.lower()) or
                (log.details and search_lower in str(log.details).lower())
            )
        ]
    
    return result


def log_matches_filters(log: AuditLogEntry, filters: AuditLogFilters) -> bool:
    """
    Check if a single log entry matches all filter criteria.
    
    This is the oracle function for Property 18.
    
    Args:
        log: Log entry to check
        filters: Filter criteria
        
    Returns:
        bool: True if log matches ALL filter criteria
    """
    # Check date_from
    if filters.date_from and log.timestamp < filters.date_from:
        return False
    
    # Check date_to
    if filters.date_to and log.timestamp > filters.date_to:
        return False
    
    # Check actor_id
    if filters.actor_id and log.user_id != filters.actor_id:
        return False
    
    # Check action_type
    if filters.action_type and log.action != filters.action_type:
        return False
    
    # Check resource_type
    if filters.resource_type:
        if not log.details or log.details.get("resource_type") != filters.resource_type:
            return False
    
    # Check resource_id
    if filters.resource_id:
        if not log.details or log.details.get("resource_id") != filters.resource_id:
            return False
    
    # Check search
    if filters.search:
        search_lower = filters.search.lower()
        action_match = log.action and search_lower in log.action.lower()
        details_match = log.details and search_lower in str(log.details).lower()
        if not (action_match or details_match):
            return False
    
    return True


# Strategies for generating test data
uuid_strategy = st.uuids()
action_strategy = st.sampled_from([
    "login", "login_failed", "logout", "admin_action",
    "user_created", "user_updated", "user_deleted",
    "subscription_created", "subscription_updated",
    "content_approved", "content_removed",
])
resource_type_strategy = st.sampled_from([
    "user", "admin", "subscription", "payment", "content", "config", "report"
])
timestamp_strategy = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2025, 12, 31),
)


@st.composite
def audit_log_entry_strategy(draw):
    """Generate a random audit log entry."""
    log_id = draw(uuid_strategy)
    user_id = draw(st.one_of(st.none(), uuid_strategy))
    action = draw(action_strategy)
    timestamp = draw(timestamp_strategy)
    
    # Generate details with optional resource info
    has_resource = draw(st.booleans())
    details = {}
    if has_resource:
        details["resource_type"] = draw(resource_type_strategy)
        details["resource_id"] = str(draw(uuid_strategy))
        details["event"] = action
    
    return AuditLogEntry(
        id=log_id,
        user_id=user_id,
        action=action,
        timestamp=timestamp,
        details=details,
    )


@st.composite
def audit_log_filters_strategy(draw):
    """Generate random filter criteria."""
    # Randomly decide which filters to apply
    use_date_from = draw(st.booleans())
    use_date_to = draw(st.booleans())
    use_actor_id = draw(st.booleans())
    use_action_type = draw(st.booleans())
    use_resource_type = draw(st.booleans())
    
    date_from = None
    date_to = None
    
    if use_date_from:
        date_from = draw(timestamp_strategy)
    
    if use_date_to:
        date_to = draw(timestamp_strategy)
        # Ensure date_to >= date_from if both are set
        if date_from and date_to < date_from:
            date_from, date_to = date_to, date_from
    
    return AuditLogFilters(
        date_from=date_from,
        date_to=date_to,
        actor_id=draw(uuid_strategy) if use_actor_id else None,
        action_type=draw(action_strategy) if use_action_type else None,
        resource_type=draw(resource_type_strategy) if use_resource_type else None,
    )


class TestAuditLogFiltering:
    """
    Property tests for audit log filtering.
    
    **Feature: admin-panel, Property 18: Audit Log Filtering**
    **Validates: Requirements 8.2**
    """

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=0, max_size=50),
        filters=audit_log_filters_strategy(),
    )
    @settings(max_examples=100)
    def test_all_returned_logs_match_all_filters(
        self,
        logs: List[AuditLogEntry],
        filters: AuditLogFilters,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any audit log filter query, ALL returned logs SHALL match ALL specified filter criteria.
        """
        filtered = filter_audit_logs(logs, filters)
        
        # Every returned log must match all filter criteria
        for log in filtered:
            assert log_matches_filters(log, filters), (
                f"Log {log.id} does not match all filters. "
                f"Log: action={log.action}, timestamp={log.timestamp}, "
                f"user_id={log.user_id}, details={log.details}. "
                f"Filters: {filters}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=0, max_size=50),
        filters=audit_log_filters_strategy(),
    )
    @settings(max_examples=100)
    def test_no_matching_logs_excluded(
        self,
        logs: List[AuditLogEntry],
        filters: AuditLogFilters,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any audit log filter query, NO logs that match all criteria SHALL be excluded.
        """
        filtered = filter_audit_logs(logs, filters)
        filtered_ids = {log.id for log in filtered}
        
        # Every log that matches all filters must be in the result
        for log in logs:
            if log_matches_filters(log, filters):
                assert log.id in filtered_ids, (
                    f"Log {log.id} matches all filters but was excluded. "
                    f"Log: action={log.action}, timestamp={log.timestamp}, "
                    f"user_id={log.user_id}, details={log.details}. "
                    f"Filters: {filters}"
                )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=1, max_size=50),
        date_from=timestamp_strategy,
        date_to=timestamp_strategy,
    )
    @settings(max_examples=100)
    def test_date_range_filter(
        self,
        logs: List[AuditLogEntry],
        date_from: datetime,
        date_to: datetime,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any date range filter, all returned logs SHALL have timestamps within the range.
        """
        # Ensure date_from <= date_to
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        
        filters = AuditLogFilters(date_from=date_from, date_to=date_to)
        filtered = filter_audit_logs(logs, filters)
        
        for log in filtered:
            assert log.timestamp >= date_from, (
                f"Log timestamp {log.timestamp} is before date_from {date_from}"
            )
            assert log.timestamp <= date_to, (
                f"Log timestamp {log.timestamp} is after date_to {date_to}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=1, max_size=50),
        actor_id=uuid_strategy,
    )
    @settings(max_examples=100)
    def test_actor_id_filter(
        self,
        logs: List[AuditLogEntry],
        actor_id: uuid.UUID,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any actor_id filter, all returned logs SHALL have matching user_id.
        """
        filters = AuditLogFilters(actor_id=actor_id)
        filtered = filter_audit_logs(logs, filters)
        
        for log in filtered:
            assert log.user_id == actor_id, (
                f"Log user_id {log.user_id} does not match actor_id {actor_id}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=1, max_size=50),
        action_type=action_strategy,
    )
    @settings(max_examples=100)
    def test_action_type_filter(
        self,
        logs: List[AuditLogEntry],
        action_type: str,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any action_type filter, all returned logs SHALL have matching action.
        """
        filters = AuditLogFilters(action_type=action_type)
        filtered = filter_audit_logs(logs, filters)
        
        for log in filtered:
            assert log.action == action_type, (
                f"Log action {log.action} does not match action_type {action_type}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=1, max_size=50),
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_resource_type_filter(
        self,
        logs: List[AuditLogEntry],
        resource_type: str,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        For any resource_type filter, all returned logs SHALL have matching resource_type in details.
        """
        filters = AuditLogFilters(resource_type=resource_type)
        filtered = filter_audit_logs(logs, filters)
        
        for log in filtered:
            assert log.details is not None, "Log details should not be None"
            assert log.details.get("resource_type") == resource_type, (
                f"Log resource_type {log.details.get('resource_type')} "
                f"does not match filter {resource_type}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_empty_filters_returns_all(
        self,
        logs: List[AuditLogEntry],
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        With no filters applied, all logs SHALL be returned.
        """
        filters = AuditLogFilters()  # No filters
        filtered = filter_audit_logs(logs, filters)
        
        assert len(filtered) == len(logs), (
            f"Expected {len(logs)} logs, got {len(filtered)}"
        )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=1, max_size=50),
        actor_id=uuid_strategy,
        action_type=action_strategy,
    )
    @settings(max_examples=100)
    def test_multiple_filters_are_conjunctive(
        self,
        logs: List[AuditLogEntry],
        actor_id: uuid.UUID,
        action_type: str,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        Multiple filters SHALL be applied conjunctively (AND logic).
        All returned logs must match ALL specified criteria.
        """
        filters = AuditLogFilters(actor_id=actor_id, action_type=action_type)
        filtered = filter_audit_logs(logs, filters)
        
        for log in filtered:
            # Must match BOTH criteria
            assert log.user_id == actor_id, (
                f"Log user_id {log.user_id} does not match actor_id {actor_id}"
            )
            assert log.action == action_type, (
                f"Log action {log.action} does not match action_type {action_type}"
            )

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=0, max_size=50),
        filters=audit_log_filters_strategy(),
    )
    @settings(max_examples=100)
    def test_filter_is_idempotent(
        self,
        logs: List[AuditLogEntry],
        filters: AuditLogFilters,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        Applying the same filter twice SHALL produce the same result.
        """
        filtered_once = filter_audit_logs(logs, filters)
        filtered_twice = filter_audit_logs(filtered_once, filters)
        
        assert len(filtered_once) == len(filtered_twice), (
            f"Filter is not idempotent: {len(filtered_once)} vs {len(filtered_twice)}"
        )
        
        # Same logs in same order
        for log1, log2 in zip(filtered_once, filtered_twice):
            assert log1.id == log2.id

    @given(
        logs=st.lists(audit_log_entry_strategy(), min_size=0, max_size=50),
        filters=audit_log_filters_strategy(),
    )
    @settings(max_examples=100)
    def test_filtered_count_lte_original(
        self,
        logs: List[AuditLogEntry],
        filters: AuditLogFilters,
    ) -> None:
        """
        **Feature: admin-panel, Property 18: Audit Log Filtering**
        
        Filtered result count SHALL be less than or equal to original count.
        """
        filtered = filter_audit_logs(logs, filters)
        
        assert len(filtered) <= len(logs), (
            f"Filtered count {len(filtered)} exceeds original {len(logs)}"
        )
