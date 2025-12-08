"""Property-based tests for analytics date range accuracy.

**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**
**Validates: Requirements 17.2**
"""

import uuid
from datetime import date, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st, assume


# Mock classes for testing without database
class MockAnalyticsSnapshot:
    """Mock analytics snapshot for testing."""

    def __init__(
        self,
        account_id: uuid.UUID,
        snapshot_date: date,
        subscriber_count: int = 0,
        total_views: int = 0,
        estimated_revenue: float = 0.0,
    ):
        self.id = uuid.uuid4()
        self.account_id = account_id
        self.snapshot_date = snapshot_date
        self.subscriber_count = subscriber_count
        self.subscriber_change = 0
        self.total_views = total_views
        self.views_change = 0
        self.total_videos = 0
        self.total_likes = 0
        self.total_comments = 0
        self.engagement_rate = 0.0
        self.watch_time_minutes = 0
        self.estimated_revenue = estimated_revenue


class MockAnalyticsRepository:
    """Mock repository for testing date range queries."""

    def __init__(self):
        self.snapshots: list[MockAnalyticsSnapshot] = []

    def add_snapshot(self, snapshot: MockAnalyticsSnapshot) -> None:
        """Add a snapshot to the repository."""
        self.snapshots.append(snapshot)


    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[MockAnalyticsSnapshot]:
        """Get snapshots within a date range.

        This is the core function being tested - it must return ONLY
        snapshots where snapshot_date is within [start_date, end_date].
        """
        result = []
        for snapshot in self.snapshots:
            # Check date range (inclusive)
            if snapshot.snapshot_date < start_date:
                continue
            if snapshot.snapshot_date > end_date:
                continue
            # Check account filter if provided
            if account_ids and snapshot.account_id not in account_ids:
                continue
            result.append(snapshot)
        return result

    def get_by_account_date_range(
        self,
        account_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[MockAnalyticsSnapshot]:
        """Get snapshots for a specific account within date range."""
        return self.get_by_date_range(start_date, end_date, [account_id])


# Strategies for generating test data
date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2025, 12, 31),
)

account_id_strategy = st.uuids()

snapshot_strategy = st.builds(
    MockAnalyticsSnapshot,
    account_id=account_id_strategy,
    snapshot_date=date_strategy,
    subscriber_count=st.integers(min_value=0, max_value=10_000_000),
    total_views=st.integers(min_value=0, max_value=1_000_000_000),
    estimated_revenue=st.floats(min_value=0.0, max_value=1_000_000.0),
)


class TestAnalyticsDateRangeAccuracy:
    """Property tests for analytics date range accuracy.

    Requirements 17.2: For any analytics query with date range,
    all returned metrics SHALL fall within the specified date range.
    """

    @given(
        snapshots=st.lists(snapshot_strategy, min_size=1, max_size=100),
        start_date=date_strategy,
        end_date=date_strategy,
    )
    @settings(max_examples=100)
    def test_all_returned_snapshots_within_date_range(
        self,
        snapshots: list[MockAnalyticsSnapshot],
        start_date: date,
        end_date: date,
    ) -> None:
        """**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**

        For any date range query, ALL returned snapshots SHALL have
        snapshot_date within [start_date, end_date] inclusive.
        """
        # Ensure valid date range
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        repo = MockAnalyticsRepository()
        for snapshot in snapshots:
            repo.add_snapshot(snapshot)

        # Query with date range
        results = repo.get_by_date_range(start_date, end_date)

        # Verify ALL results are within the date range
        for result in results:
            assert result.snapshot_date >= start_date, (
                f"Snapshot date {result.snapshot_date} is before start_date {start_date}"
            )
            assert result.snapshot_date <= end_date, (
                f"Snapshot date {result.snapshot_date} is after end_date {end_date}"
            )

    @given(
        snapshots=st.lists(snapshot_strategy, min_size=1, max_size=100),
        start_date=date_strategy,
        end_date=date_strategy,
    )
    @settings(max_examples=100)
    def test_no_snapshots_outside_range_returned(
        self,
        snapshots: list[MockAnalyticsSnapshot],
        start_date: date,
        end_date: date,
    ) -> None:
        """**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**

        Snapshots outside the date range SHALL NOT be returned.
        """
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        repo = MockAnalyticsRepository()
        for snapshot in snapshots:
            repo.add_snapshot(snapshot)

        results = repo.get_by_date_range(start_date, end_date)
        result_ids = {r.id for r in results}

        # Check that snapshots outside range are NOT in results
        for snapshot in snapshots:
            is_in_range = start_date <= snapshot.snapshot_date <= end_date
            is_in_results = snapshot.id in result_ids

            if not is_in_range:
                assert not is_in_results, (
                    f"Snapshot with date {snapshot.snapshot_date} outside range "
                    f"[{start_date}, {end_date}] was incorrectly returned"
                )

    @given(
        snapshots=st.lists(snapshot_strategy, min_size=1, max_size=50),
        start_date=date_strategy,
        end_date=date_strategy,
        account_id=account_id_strategy,
    )
    @settings(max_examples=100)
    def test_account_filter_with_date_range(
        self,
        snapshots: list[MockAnalyticsSnapshot],
        start_date: date,
        end_date: date,
        account_id: uuid.UUID,
    ) -> None:
        """**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**

        When filtering by account AND date range, results SHALL satisfy both criteria.
        """
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        repo = MockAnalyticsRepository()
        for snapshot in snapshots:
            repo.add_snapshot(snapshot)

        results = repo.get_by_date_range(start_date, end_date, [account_id])

        for result in results:
            # Must be within date range
            assert result.snapshot_date >= start_date
            assert result.snapshot_date <= end_date
            # Must match account filter
            assert result.account_id == account_id

    @given(
        base_date=date_strategy,
        days_before=st.integers(min_value=0, max_value=365),
        days_after=st.integers(min_value=0, max_value=365),
    )
    @settings(max_examples=100)
    def test_boundary_dates_included(
        self,
        base_date: date,
        days_before: int,
        days_after: int,
    ) -> None:
        """**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**

        Snapshots on boundary dates (start_date and end_date) SHALL be included.
        """
        start_date = base_date - timedelta(days=days_before)
        end_date = base_date + timedelta(days=days_after)

        # Ensure dates are valid
        assume(start_date >= date(2020, 1, 1))
        assume(end_date <= date(2025, 12, 31))

        account_id = uuid.uuid4()
        repo = MockAnalyticsRepository()

        # Add snapshots on boundary dates
        start_snapshot = MockAnalyticsSnapshot(account_id, start_date)
        end_snapshot = MockAnalyticsSnapshot(account_id, end_date)
        repo.add_snapshot(start_snapshot)
        repo.add_snapshot(end_snapshot)

        results = repo.get_by_date_range(start_date, end_date)

        # Both boundary snapshots should be included
        result_ids = {r.id for r in results}
        assert start_snapshot.id in result_ids, "Start date snapshot not included"
        assert end_snapshot.id in result_ids, "End date snapshot not included"

    @given(
        single_date=date_strategy,
        num_snapshots=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_single_day_range(
        self,
        single_date: date,
        num_snapshots: int,
    ) -> None:
        """**Feature: youtube-automation, Property 24: Analytics Date Range Accuracy**

        When start_date equals end_date, only snapshots for that exact date SHALL be returned.
        """
        account_id = uuid.uuid4()
        repo = MockAnalyticsRepository()

        # Add snapshots for the target date
        for _ in range(num_snapshots):
            repo.add_snapshot(MockAnalyticsSnapshot(account_id, single_date))

        # Add snapshots for adjacent dates
        if single_date > date(2020, 1, 1):
            repo.add_snapshot(MockAnalyticsSnapshot(account_id, single_date - timedelta(days=1)))
        if single_date < date(2025, 12, 31):
            repo.add_snapshot(MockAnalyticsSnapshot(account_id, single_date + timedelta(days=1)))

        # Query for single day
        results = repo.get_by_date_range(single_date, single_date)

        # All results should be for the exact date
        assert len(results) == num_snapshots
        for result in results:
            assert result.snapshot_date == single_date


class TestDateRangeInvariants:
    """Tests for date range query invariants."""

    def test_empty_repository_returns_empty_list(self) -> None:
        """Empty repository SHALL return empty list for any date range."""
        repo = MockAnalyticsRepository()
        results = repo.get_by_date_range(date(2024, 1, 1), date(2024, 12, 31))
        assert results == []

    def test_result_count_never_exceeds_total_snapshots(self) -> None:
        """Result count SHALL never exceed total snapshots in repository."""
        repo = MockAnalyticsRepository()
        account_id = uuid.uuid4()

        # Add 10 snapshots
        for i in range(10):
            repo.add_snapshot(
                MockAnalyticsSnapshot(account_id, date(2024, 1, 1) + timedelta(days=i))
            )

        # Query for any range
        results = repo.get_by_date_range(date(2020, 1, 1), date(2030, 12, 31))
        assert len(results) <= 10

    def test_narrower_range_returns_subset(self) -> None:
        """Narrower date range SHALL return subset of wider range results."""
        repo = MockAnalyticsRepository()
        account_id = uuid.uuid4()

        # Add snapshots for a month
        for i in range(30):
            repo.add_snapshot(
                MockAnalyticsSnapshot(account_id, date(2024, 6, 1) + timedelta(days=i))
            )

        wide_results = repo.get_by_date_range(date(2024, 6, 1), date(2024, 6, 30))
        narrow_results = repo.get_by_date_range(date(2024, 6, 10), date(2024, 6, 20))

        wide_ids = {r.id for r in wide_results}
        narrow_ids = {r.id for r in narrow_results}

        # Narrow results should be subset of wide results
        assert narrow_ids.issubset(wide_ids)
