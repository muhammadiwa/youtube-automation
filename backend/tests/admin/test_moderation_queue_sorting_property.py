"""Property-based tests for Moderation Queue Sorting.

**Feature: admin-panel, Property 9: Moderation Queue Sorting**
**Validates: Requirements 6.1**

Property 9: Moderation Queue Sorting
*For any* moderation queue query, results SHALL be sorted by severity 
(critical > high > medium > low) then by report_count descending.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Enums and Constants ====================

class ReportSeverity:
    """Severity levels for content reports."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus:
    """Status of content reports."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REMOVED = "removed"


# Severity order for sorting (higher = more severe)
SEVERITY_ORDER = {
    ReportSeverity.LOW: 1,
    ReportSeverity.MEDIUM: 2,
    ReportSeverity.HIGH: 3,
    ReportSeverity.CRITICAL: 4,
}


# ==================== Data Classes ====================

@dataclass
class ContentReport:
    """Content report for testing."""
    id: uuid.UUID
    content_type: str
    content_id: uuid.UUID
    severity: str
    report_count: int
    status: str
    created_at: datetime
    
    @property
    def severity_order(self) -> int:
        """Get numeric severity order for sorting."""
        return SEVERITY_ORDER.get(self.severity, 0)


# ==================== Sorting Logic ====================

def sort_moderation_queue(reports: list[ContentReport]) -> list[ContentReport]:
    """
    Sort moderation queue by severity (critical > high > medium > low),
    then by report_count descending.
    
    Property 9: Moderation Queue Sorting
    - Results SHALL be sorted by severity (critical > high > medium > low)
    - Then by report_count descending
    
    Args:
        reports: List of content reports to sort
        
    Returns:
        Sorted list of content reports
    """
    return sorted(
        reports,
        key=lambda r: (-r.severity_order, -r.report_count, r.created_at),
    )


def is_correctly_sorted(reports: list[ContentReport]) -> bool:
    """
    Check if reports are correctly sorted according to Property 9.
    
    Args:
        reports: List of content reports
        
    Returns:
        True if correctly sorted
    """
    for i in range(len(reports) - 1):
        current = reports[i]
        next_report = reports[i + 1]
        
        # Check severity order (higher severity should come first)
        if current.severity_order < next_report.severity_order:
            return False
        
        # If same severity, check report_count (higher count should come first)
        if current.severity_order == next_report.severity_order:
            if current.report_count < next_report.report_count:
                return False
    
    return True


# ==================== Strategies ====================

severity_strategy = st.sampled_from([
    ReportSeverity.LOW,
    ReportSeverity.MEDIUM,
    ReportSeverity.HIGH,
    ReportSeverity.CRITICAL,
])

content_type_strategy = st.sampled_from(["video", "comment", "stream", "thumbnail"])

status_strategy = st.sampled_from([
    ReportStatus.PENDING,
    ReportStatus.REVIEWED,
    ReportStatus.APPROVED,
    ReportStatus.REMOVED,
])


@st.composite
def report_strategy(draw):
    """Generate a random content report."""
    return ContentReport(
        id=uuid.uuid4(),
        content_type=draw(content_type_strategy),
        content_id=uuid.uuid4(),
        severity=draw(severity_strategy),
        report_count=draw(st.integers(min_value=1, max_value=100)),
        status=draw(status_strategy),
        created_at=datetime.utcnow(),
    )


@st.composite
def reports_list_strategy(draw, min_size=0, max_size=50):
    """Generate a list of random content reports."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(report_strategy()) for _ in range(size)]


# ==================== Property Tests ====================

class TestModerationQueueSorting:
    """Property tests for Moderation Queue Sorting.
    
    **Feature: admin-panel, Property 9: Moderation Queue Sorting**
    **Validates: Requirements 6.1**
    """

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=0, max_size=50))
    def test_sorted_queue_is_correctly_ordered(self, reports: list[ContentReport]):
        """
        Property: After sorting, the queue SHALL be ordered by severity 
        (critical > high > medium > low) then by report_count descending.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_reports = sort_moderation_queue(reports)
        
        assert is_correctly_sorted(sorted_reports), \
            "Queue is not correctly sorted by severity and report_count"

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=1, max_size=50))
    def test_critical_severity_comes_first(self, reports: list[ContentReport]):
        """
        Property: Critical severity reports SHALL appear before all other severities.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        # Add at least one critical report
        critical_report = ContentReport(
            id=uuid.uuid4(),
            content_type="video",
            content_id=uuid.uuid4(),
            severity=ReportSeverity.CRITICAL,
            report_count=1,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        reports_with_critical = reports + [critical_report]
        
        sorted_reports = sort_moderation_queue(reports_with_critical)
        
        # Find first non-critical report
        first_non_critical_idx = None
        for i, report in enumerate(sorted_reports):
            if report.severity != ReportSeverity.CRITICAL:
                first_non_critical_idx = i
                break
        
        # All critical reports should come before non-critical
        if first_non_critical_idx is not None:
            for i in range(first_non_critical_idx):
                assert sorted_reports[i].severity == ReportSeverity.CRITICAL, \
                    "Critical reports should come before non-critical reports"

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=2, max_size=50))
    def test_same_severity_sorted_by_report_count(self, reports: list[ContentReport]):
        """
        Property: Reports with the same severity SHALL be sorted by report_count descending.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_reports = sort_moderation_queue(reports)
        
        # Check that within each severity level, report_count is descending
        for i in range(len(sorted_reports) - 1):
            current = sorted_reports[i]
            next_report = sorted_reports[i + 1]
            
            if current.severity == next_report.severity:
                assert current.report_count >= next_report.report_count, \
                    f"Within same severity ({current.severity}), report_count should be descending"

    @settings(max_examples=100)
    @given(
        severity=severity_strategy,
        report_counts=st.lists(st.integers(min_value=1, max_value=100), min_size=2, max_size=20),
    )
    def test_report_count_ordering_within_severity(
        self, severity: str, report_counts: list[int]
    ):
        """
        Property: For reports with identical severity, higher report_count SHALL come first.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        # Create reports with same severity but different report counts
        reports = [
            ContentReport(
                id=uuid.uuid4(),
                content_type="video",
                content_id=uuid.uuid4(),
                severity=severity,
                report_count=count,
                status=ReportStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            for count in report_counts
        ]
        
        sorted_reports = sort_moderation_queue(reports)
        
        # Verify descending order by report_count
        for i in range(len(sorted_reports) - 1):
            assert sorted_reports[i].report_count >= sorted_reports[i + 1].report_count, \
                "Report count should be in descending order within same severity"

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=0, max_size=50))
    def test_sorting_preserves_all_reports(self, reports: list[ContentReport]):
        """
        Property: Sorting SHALL preserve all reports (no reports lost or duplicated).
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_reports = sort_moderation_queue(reports)
        
        assert len(sorted_reports) == len(reports), \
            "Sorting should not change the number of reports"
        
        # Check all original reports are present
        original_ids = {r.id for r in reports}
        sorted_ids = {r.id for r in sorted_reports}
        
        assert original_ids == sorted_ids, \
            "Sorting should preserve all report IDs"

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=0, max_size=50))
    def test_sorting_is_idempotent(self, reports: list[ContentReport]):
        """
        Property: Sorting the same list twice SHALL produce the same result.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_once = sort_moderation_queue(reports)
        sorted_twice = sort_moderation_queue(sorted_once)
        
        # Compare by IDs since objects may be different instances
        assert [r.id for r in sorted_once] == [r.id for r in sorted_twice], \
            "Sorting should be idempotent"

    @settings(max_examples=100)
    @given(
        low_count=st.integers(min_value=1, max_value=50),
        high_count=st.integers(min_value=51, max_value=100),
    )
    def test_severity_takes_precedence_over_report_count(
        self, low_count: int, high_count: int
    ):
        """
        Property: A higher severity report with lower report_count SHALL come 
        before a lower severity report with higher report_count.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        # Create a low severity report with high count
        low_severity_high_count = ContentReport(
            id=uuid.uuid4(),
            content_type="video",
            content_id=uuid.uuid4(),
            severity=ReportSeverity.LOW,
            report_count=high_count,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        # Create a critical severity report with low count
        critical_low_count = ContentReport(
            id=uuid.uuid4(),
            content_type="video",
            content_id=uuid.uuid4(),
            severity=ReportSeverity.CRITICAL,
            report_count=low_count,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        reports = [low_severity_high_count, critical_low_count]
        sorted_reports = sort_moderation_queue(reports)
        
        # Critical should come first regardless of report count
        assert sorted_reports[0].severity == ReportSeverity.CRITICAL, \
            "Higher severity should take precedence over higher report count"

    @settings(max_examples=100)
    @given(reports=reports_list_strategy(min_size=0, max_size=50))
    def test_severity_order_is_correct(self, reports: list[ContentReport]):
        """
        Property: Severity order SHALL be critical > high > medium > low.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_reports = sort_moderation_queue(reports)
        
        # Track the last seen severity order
        last_severity_order = float('inf')
        
        for report in sorted_reports:
            current_order = SEVERITY_ORDER.get(report.severity, 0)
            assert current_order <= last_severity_order, \
                f"Severity order violated: {report.severity} came after a lower severity"
            last_severity_order = current_order

    def test_empty_queue_returns_empty(self):
        """
        Property: An empty queue SHALL return an empty sorted list.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        sorted_reports = sort_moderation_queue([])
        assert sorted_reports == [], "Empty queue should return empty list"

    def test_single_report_returns_same(self):
        """
        Property: A queue with one report SHALL return that report.
        
        **Feature: admin-panel, Property 9: Moderation Queue Sorting**
        **Validates: Requirements 6.1**
        """
        report = ContentReport(
            id=uuid.uuid4(),
            content_type="video",
            content_id=uuid.uuid4(),
            severity=ReportSeverity.MEDIUM,
            report_count=5,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        sorted_reports = sort_moderation_queue([report])
        
        assert len(sorted_reports) == 1
        assert sorted_reports[0].id == report.id
