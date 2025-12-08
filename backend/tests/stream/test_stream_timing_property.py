"""Property-based tests for stream start timing.

**Feature: youtube-automation, Property 11: Stream Start Timing**
**Validates: Requirements 6.1**
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Mock celery_app before importing stream tasks
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.tasks import StreamScheduler


# Strategy for generating valid datetime objects
datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)

# Strategy for generating seconds within the timing window
seconds_within_window = st.integers(min_value=0, max_value=30)

# Strategy for generating seconds outside the timing window
seconds_outside_window = st.integers(min_value=31, max_value=3600)


class TestStreamStartTiming:
    """Property tests for stream start timing.

    Requirements 6.1: Stream SHALL be initiated within 30 seconds of scheduled time.
    """

    @given(
        scheduled_time=datetime_strategy,
        delay_seconds=seconds_within_window,
    )
    @settings(max_examples=100)
    def test_start_within_window_is_valid(
        self, scheduled_time: datetime, delay_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any scheduled time and current time within 30 seconds after scheduled,
        the start SHALL be considered within the valid window.
        """
        current_time = scheduled_time + timedelta(seconds=delay_seconds)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=current_time,
        )

        assert is_within_window is True, (
            f"Start at {delay_seconds}s after scheduled should be within window"
        )

    @given(
        scheduled_time=datetime_strategy,
        delay_seconds=seconds_outside_window,
    )
    @settings(max_examples=100)
    def test_start_outside_window_is_invalid(
        self, scheduled_time: datetime, delay_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any scheduled time and current time more than 30 seconds after scheduled,
        the start SHALL NOT be considered within the valid window.
        """
        current_time = scheduled_time + timedelta(seconds=delay_seconds)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=current_time,
        )

        assert is_within_window is False, (
            f"Start at {delay_seconds}s after scheduled should be outside window"
        )

    @given(
        scheduled_time=datetime_strategy,
        early_seconds=st.integers(min_value=1, max_value=3600),
    )
    @settings(max_examples=100)
    def test_start_before_scheduled_is_invalid(
        self, scheduled_time: datetime, early_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any current time before the scheduled time,
        the start SHALL NOT be considered within the valid window.
        """
        current_time = scheduled_time - timedelta(seconds=early_seconds)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=current_time,
        )

        assert is_within_window is False, (
            f"Start {early_seconds}s before scheduled should not be within window"
        )

    @given(scheduled_time=datetime_strategy)
    @settings(max_examples=100)
    def test_exact_scheduled_time_is_valid(self, scheduled_time: datetime) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any scheduled time, starting exactly at that time SHALL be valid.
        """
        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=scheduled_time,
        )

        assert is_within_window is True, "Exact scheduled time should be valid"

    @given(scheduled_time=datetime_strategy)
    @settings(max_examples=100)
    def test_boundary_at_30_seconds_is_valid(self, scheduled_time: datetime) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any scheduled time, starting exactly 30 seconds after SHALL be valid.
        """
        current_time = scheduled_time + timedelta(seconds=30)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=current_time,
        )

        assert is_within_window is True, "30 seconds after scheduled should be valid"

    @given(scheduled_time=datetime_strategy)
    @settings(max_examples=100)
    def test_boundary_at_31_seconds_is_invalid(self, scheduled_time: datetime) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any scheduled time, starting 31 seconds after SHALL NOT be valid.
        """
        current_time = scheduled_time + timedelta(seconds=31)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled_time,
            current_time=current_time,
        )

        assert is_within_window is False, "31 seconds after scheduled should be invalid"


class TestStreamStartDeviation:
    """Property tests for stream start deviation calculation."""

    @given(
        scheduled_time=datetime_strategy,
        delay_seconds=st.integers(min_value=0, max_value=3600),
    )
    @settings(max_examples=100)
    def test_late_start_has_positive_deviation(
        self, scheduled_time: datetime, delay_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any late start, deviation SHALL be positive.
        """
        actual_time = scheduled_time + timedelta(seconds=delay_seconds)

        deviation = StreamScheduler.calculate_start_deviation(
            scheduled_time=scheduled_time,
            actual_time=actual_time,
        )

        assert deviation >= 0, "Late start should have non-negative deviation"
        assert abs(deviation - delay_seconds) < 0.001, "Deviation should match delay"

    @given(
        scheduled_time=datetime_strategy,
        early_seconds=st.integers(min_value=1, max_value=3600),
    )
    @settings(max_examples=100)
    def test_early_start_has_negative_deviation(
        self, scheduled_time: datetime, early_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any early start, deviation SHALL be negative.
        """
        actual_time = scheduled_time - timedelta(seconds=early_seconds)

        deviation = StreamScheduler.calculate_start_deviation(
            scheduled_time=scheduled_time,
            actual_time=actual_time,
        )

        assert deviation < 0, "Early start should have negative deviation"
        assert abs(deviation + early_seconds) < 0.001, "Deviation should match early time"

    @given(scheduled_time=datetime_strategy)
    @settings(max_examples=100)
    def test_exact_start_has_zero_deviation(self, scheduled_time: datetime) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any exact start, deviation SHALL be zero.
        """
        deviation = StreamScheduler.calculate_start_deviation(
            scheduled_time=scheduled_time,
            actual_time=scheduled_time,
        )

        assert deviation == 0, "Exact start should have zero deviation"

    @given(
        scheduled_time=datetime_strategy,
        delay_seconds=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_deviation_within_requirement(
        self, scheduled_time: datetime, delay_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 11: Stream Start Timing**

        For any start within 30 seconds, deviation SHALL be <= 30 seconds.
        """
        actual_time = scheduled_time + timedelta(seconds=delay_seconds)

        deviation = StreamScheduler.calculate_start_deviation(
            scheduled_time=scheduled_time,
            actual_time=actual_time,
        )

        assert abs(deviation) <= StreamScheduler.MAX_START_DEVIATION_SECONDS, (
            f"Deviation {deviation} should be within {StreamScheduler.MAX_START_DEVIATION_SECONDS}s"
        )


class TestStreamTimingEdgeCases:
    """Edge case tests for stream timing."""

    def test_max_deviation_constant_is_30_seconds(self) -> None:
        """MAX_START_DEVIATION_SECONDS SHALL be 30 per Requirements 6.1."""
        assert StreamScheduler.MAX_START_DEVIATION_SECONDS == 30

    def test_timezone_aware_scheduled_time(self) -> None:
        """Timezone-aware scheduled times SHALL be handled correctly."""
        from datetime import timezone

        scheduled = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current = datetime(2024, 1, 1, 10, 0, 15, tzinfo=timezone.utc)

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled,
            current_time=current,
        )

        assert is_within_window is True

    def test_mixed_timezone_handling(self) -> None:
        """Mixed timezone-aware and naive datetimes SHALL be handled."""
        from datetime import timezone

        scheduled = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        current = datetime(2024, 1, 1, 10, 0, 15)  # Naive

        is_within_window = StreamScheduler.is_within_start_window(
            scheduled_time=scheduled,
            current_time=current,
        )

        assert is_within_window is True

    def test_deviation_calculation_precision(self) -> None:
        """Deviation calculation SHALL have sub-second precision."""
        scheduled = datetime(2024, 1, 1, 10, 0, 0, 0)
        actual = datetime(2024, 1, 1, 10, 0, 15, 500000)  # 15.5 seconds

        deviation = StreamScheduler.calculate_start_deviation(
            scheduled_time=scheduled,
            actual_time=actual,
        )

        assert abs(deviation - 15.5) < 0.001
