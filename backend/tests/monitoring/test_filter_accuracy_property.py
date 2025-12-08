"""Property-based tests for channel filter accuracy.

**Feature: youtube-automation, Property 23: Channel Filter Accuracy**
**Validates: Requirements 16.2**
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st, assume

from app.modules.monitoring.schemas import (
    ChannelStatusFilter,
    ChannelStatus,
    IssueSeverity,
    ChannelIssue,
    ChannelGridItem,
)


# Mock service for testing filter logic without database
class MockMonitoringService:
    """Mock monitoring service for testing filter logic."""

    def __init__(self):
        self.channels: list[ChannelGridItem] = []

    def add_channel(self, channel: ChannelGridItem) -> None:
        """Add a channel to the mock service."""
        self.channels.append(channel)

    def apply_filters(
        self,
        status_filter: ChannelStatusFilter,
        search: Optional[str] = None,
    ) -> list[ChannelGridItem]:
        """Apply filters to channels.
        
        This is the core filtering logic being tested.
        Requirements: 16.2
        """
        filtered = self.channels
        
        # Filter by status
        if status_filter != ChannelStatusFilter.ALL:
            filtered = [
                item for item in filtered
                if self._matches_status_filter(item, status_filter)
            ]
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            filtered = [
                item for item in filtered
                if search_lower in item.channel_title.lower()
                or search_lower in item.channel_id.lower()
            ]
        
        return filtered

    def _matches_status_filter(
        self, item: ChannelGridItem, status_filter: ChannelStatusFilter
    ) -> bool:
        """Check if channel matches the status filter."""
        if status_filter == ChannelStatusFilter.ALL:
            return True
        elif status_filter == ChannelStatusFilter.LIVE:
            return item.status == ChannelStatus.LIVE
        elif status_filter == ChannelStatusFilter.SCHEDULED:
            return item.status == ChannelStatus.SCHEDULED
        elif status_filter == ChannelStatusFilter.OFFLINE:
            return item.status == ChannelStatus.OFFLINE
        elif status_filter == ChannelStatusFilter.ERROR:
            return item.status == ChannelStatus.ERROR
        elif status_filter == ChannelStatusFilter.TOKEN_EXPIRED:
            return item.status == ChannelStatus.TOKEN_EXPIRED
        return True


# Strategies for generating test data
channel_status_strategy = st.sampled_from([
    ChannelStatus.LIVE,
    ChannelStatus.SCHEDULED,
    ChannelStatus.OFFLINE,
    ChannelStatus.ERROR,
    ChannelStatus.TOKEN_EXPIRED,
])

status_filter_strategy = st.sampled_from([
    ChannelStatusFilter.ALL,
    ChannelStatusFilter.LIVE,
    ChannelStatusFilter.SCHEDULED,
    ChannelStatusFilter.OFFLINE,
    ChannelStatusFilter.ERROR,
    ChannelStatusFilter.TOKEN_EXPIRED,
])

channel_title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())

channel_id_strategy = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=10,
    max_size=24,
)


def create_channel_grid_item(
    status: ChannelStatus,
    channel_title: str = "Test Channel",
    channel_id: Optional[str] = None,
) -> ChannelGridItem:
    """Create a ChannelGridItem for testing."""
    return ChannelGridItem(
        account_id=uuid.uuid4(),
        channel_id=channel_id or f"UC{uuid.uuid4().hex[:22]}",
        channel_title=channel_title,
        status=status,
        subscriber_count=1000,
        video_count=50,
        view_count=100000,
    )


class TestChannelFilterAccuracy:
    """Property tests for channel filter accuracy.

    Requirements 16.2: For any channel filter applied in monitoring view,
    the returned channels SHALL match the filter criteria exactly.
    """

    @given(
        statuses=st.lists(channel_status_strategy, min_size=1, max_size=50),
        status_filter=status_filter_strategy,
    )
    @settings(max_examples=100)
    def test_all_returned_channels_match_filter(
        self,
        statuses: list[ChannelStatus],
        status_filter: ChannelStatusFilter,
    ) -> None:
        """**Feature: youtube-automation, Property 23: Channel Filter Accuracy**

        For any status filter, ALL returned channels SHALL have
        a status that matches the filter criteria.
        """
        service = MockMonitoringService()
        
        # Create channels with various statuses
        for i, status in enumerate(statuses):
            channel = create_channel_grid_item(
                status=status,
                channel_title=f"Channel {i}",
            )
            service.add_channel(channel)
        
        # Apply filter
        results = service.apply_filters(status_filter)
        
        # Verify ALL results match the filter
        for result in results:
            if status_filter == ChannelStatusFilter.ALL:
                # All channels should be returned
                pass
            elif status_filter == ChannelStatusFilter.LIVE:
                assert result.status == ChannelStatus.LIVE, (
                    f"Channel with status {result.status} returned for LIVE filter"
                )
            elif status_filter == ChannelStatusFilter.SCHEDULED:
                assert result.status == ChannelStatus.SCHEDULED, (
                    f"Channel with status {result.status} returned for SCHEDULED filter"
                )
            elif status_filter == ChannelStatusFilter.OFFLINE:
                assert result.status == ChannelStatus.OFFLINE, (
                    f"Channel with status {result.status} returned for OFFLINE filter"
                )
            elif status_filter == ChannelStatusFilter.ERROR:
                assert result.status == ChannelStatus.ERROR, (
                    f"Channel with status {result.status} returned for ERROR filter"
                )
            elif status_filter == ChannelStatusFilter.TOKEN_EXPIRED:
                assert result.status == ChannelStatus.TOKEN_EXPIRED, (
                    f"Channel with status {result.status} returned for TOKEN_EXPIRED filter"
                )

    @given(
        statuses=st.lists(channel_status_strategy, min_size=1, max_size=50),
        status_filter=status_filter_strategy,
    )
    @settings(max_examples=100)
    def test_no_non_matching_channels_returned(
        self,
        statuses: list[ChannelStatus],
        status_filter: ChannelStatusFilter,
    ) -> None:
        """**Feature: youtube-automation, Property 23: Channel Filter Accuracy**

        Channels that do NOT match the filter SHALL NOT be returned.
        """
        service = MockMonitoringService()
        
        for i, status in enumerate(statuses):
            channel = create_channel_grid_item(
                status=status,
                channel_title=f"Channel {i}",
            )
            service.add_channel(channel)
        
        results = service.apply_filters(status_filter)
        result_ids = {r.account_id for r in results}
        
        # Check that non-matching channels are NOT in results
        for channel in service.channels:
            matches_filter = self._channel_matches_filter(channel, status_filter)
            is_in_results = channel.account_id in result_ids
            
            if not matches_filter:
                assert not is_in_results, (
                    f"Channel with status {channel.status} incorrectly returned "
                    f"for filter {status_filter}"
                )

    def _channel_matches_filter(
        self, channel: ChannelGridItem, status_filter: ChannelStatusFilter
    ) -> bool:
        """Check if channel should match the filter."""
        if status_filter == ChannelStatusFilter.ALL:
            return True
        
        filter_to_status = {
            ChannelStatusFilter.LIVE: ChannelStatus.LIVE,
            ChannelStatusFilter.SCHEDULED: ChannelStatus.SCHEDULED,
            ChannelStatusFilter.OFFLINE: ChannelStatus.OFFLINE,
            ChannelStatusFilter.ERROR: ChannelStatus.ERROR,
            ChannelStatusFilter.TOKEN_EXPIRED: ChannelStatus.TOKEN_EXPIRED,
        }
        
        expected_status = filter_to_status.get(status_filter)
        return channel.status == expected_status

    @given(
        statuses=st.lists(channel_status_strategy, min_size=1, max_size=50),
        status_filter=status_filter_strategy,
    )
    @settings(max_examples=100)
    def test_all_matching_channels_returned(
        self,
        statuses: list[ChannelStatus],
        status_filter: ChannelStatusFilter,
    ) -> None:
        """**Feature: youtube-automation, Property 23: Channel Filter Accuracy**

        ALL channels that match the filter SHALL be returned.
        """
        service = MockMonitoringService()
        
        for i, status in enumerate(statuses):
            channel = create_channel_grid_item(
                status=status,
                channel_title=f"Channel {i}",
            )
            service.add_channel(channel)
        
        results = service.apply_filters(status_filter)
        result_ids = {r.account_id for r in results}
        
        # Check that ALL matching channels ARE in results
        for channel in service.channels:
            matches_filter = self._channel_matches_filter(channel, status_filter)
            is_in_results = channel.account_id in result_ids
            
            if matches_filter:
                assert is_in_results, (
                    f"Channel with status {channel.status} not returned "
                    f"for filter {status_filter}"
                )

    @given(
        titles=st.lists(channel_title_strategy, min_size=1, max_size=20),
        search_term=st.text(min_size=1, max_size=10).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_search_filter_matches_title(
        self,
        titles: list[str],
        search_term: str,
    ) -> None:
        """**Feature: youtube-automation, Property 23: Channel Filter Accuracy**

        Search filter SHALL return only channels whose title contains the search term.
        """
        service = MockMonitoringService()
        
        for title in titles:
            channel = create_channel_grid_item(
                status=ChannelStatus.OFFLINE,
                channel_title=title,
            )
            service.add_channel(channel)
        
        results = service.apply_filters(ChannelStatusFilter.ALL, search=search_term)
        
        search_lower = search_term.lower()
        
        # All results should contain the search term
        for result in results:
            assert (
                search_lower in result.channel_title.lower()
                or search_lower in result.channel_id.lower()
            ), (
                f"Channel '{result.channel_title}' returned but doesn't contain "
                f"search term '{search_term}'"
            )

    @given(
        statuses=st.lists(channel_status_strategy, min_size=1, max_size=30),
        status_filter=status_filter_strategy,
        search_term=st.text(min_size=1, max_size=5).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_combined_filters_both_apply(
        self,
        statuses: list[ChannelStatus],
        status_filter: ChannelStatusFilter,
        search_term: str,
    ) -> None:
        """**Feature: youtube-automation, Property 23: Channel Filter Accuracy**

        When multiple filters are applied, results SHALL satisfy ALL criteria.
        """
        service = MockMonitoringService()
        
        for i, status in enumerate(statuses):
            # Create channels with varied titles
            title = f"Channel {i} {search_term if i % 3 == 0 else 'Other'}"
            channel = create_channel_grid_item(
                status=status,
                channel_title=title,
            )
            service.add_channel(channel)
        
        results = service.apply_filters(status_filter, search=search_term)
        
        search_lower = search_term.lower()
        
        for result in results:
            # Must match status filter
            if status_filter != ChannelStatusFilter.ALL:
                assert self._channel_matches_filter(result, status_filter), (
                    f"Channel status {result.status} doesn't match filter {status_filter}"
                )
            
            # Must match search filter
            assert (
                search_lower in result.channel_title.lower()
                or search_lower in result.channel_id.lower()
            ), (
                f"Channel '{result.channel_title}' doesn't contain search term"
            )


class TestFilterInvariants:
    """Tests for filter invariants."""

    def test_all_filter_returns_all_channels(self) -> None:
        """ALL filter SHALL return all channels."""
        service = MockMonitoringService()
        
        for status in ChannelStatus:
            channel = create_channel_grid_item(status=status)
            service.add_channel(channel)
        
        results = service.apply_filters(ChannelStatusFilter.ALL)
        assert len(results) == len(service.channels)

    def test_empty_service_returns_empty_list(self) -> None:
        """Empty service SHALL return empty list for any filter."""
        service = MockMonitoringService()
        
        for filter_type in ChannelStatusFilter:
            results = service.apply_filters(filter_type)
            assert results == []

    def test_result_count_never_exceeds_total(self) -> None:
        """Result count SHALL never exceed total channels."""
        service = MockMonitoringService()
        
        for i in range(10):
            channel = create_channel_grid_item(
                status=ChannelStatus.OFFLINE,
                channel_title=f"Channel {i}",
            )
            service.add_channel(channel)
        
        for filter_type in ChannelStatusFilter:
            results = service.apply_filters(filter_type)
            assert len(results) <= len(service.channels)

    @given(status_filter=status_filter_strategy)
    @settings(max_examples=50)
    def test_filter_is_idempotent(
        self,
        status_filter: ChannelStatusFilter,
    ) -> None:
        """Applying the same filter twice SHALL return the same results."""
        service = MockMonitoringService()
        
        for status in ChannelStatus:
            for i in range(3):
                channel = create_channel_grid_item(
                    status=status,
                    channel_title=f"Channel {status.value} {i}",
                )
                service.add_channel(channel)
        
        results1 = service.apply_filters(status_filter)
        results2 = service.apply_filters(status_filter)
        
        ids1 = {r.account_id for r in results1}
        ids2 = {r.account_id for r in results2}
        
        assert ids1 == ids2

    def test_narrower_filter_returns_subset(self) -> None:
        """Specific status filter SHALL return subset of ALL filter."""
        service = MockMonitoringService()
        
        for status in ChannelStatus:
            for i in range(3):
                channel = create_channel_grid_item(
                    status=status,
                    channel_title=f"Channel {status.value} {i}",
                )
                service.add_channel(channel)
        
        all_results = service.apply_filters(ChannelStatusFilter.ALL)
        all_ids = {r.account_id for r in all_results}
        
        for filter_type in ChannelStatusFilter:
            if filter_type != ChannelStatusFilter.ALL:
                filtered_results = service.apply_filters(filter_type)
                filtered_ids = {r.account_id for r in filtered_results}
                
                assert filtered_ids.issubset(all_ids), (
                    f"Filter {filter_type} results not subset of ALL results"
                )
