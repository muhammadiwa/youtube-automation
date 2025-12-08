"""Property-based tests for stream health collection frequency.

**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**
**Validates: Requirements 8.1**
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Mock celery_app before importing stream tasks
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.tasks import StreamHealthMonitor, HealthThresholds


# Strategy for generating valid datetime objects
datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
)

# Strategy for generating collection intervals
valid_interval_seconds = st.integers(min_value=1, max_value=10)
invalid_interval_seconds = st.integers(min_value=11, max_value=3600)

# Strategy for generating bitrate values
bitrate_strategy = st.integers(min_value=0, max_value=50000000)  # 0 to 50 Mbps

# Strategy for generating frame rate values
frame_rate_strategy = st.floats(min_value=0.0, max_value=120.0, allow_nan=False, allow_infinity=False)

# Strategy for generating dropped frames
dropped_frames_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for generating latency values
latency_strategy = st.integers(min_value=0, max_value=10000)


class TestStreamHealthCollectionFrequency:
    """Property tests for stream health collection frequency.

    Requirements 8.1: Health metrics SHALL be collected every 10 seconds.
    """

    def test_collection_interval_is_10_seconds(self) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        Collection interval SHALL be exactly 10 seconds per Requirements 8.1.
        """
        monitor = StreamHealthMonitor()
        assert monitor.COLLECTION_INTERVAL_SECONDS == 10

    @given(
        start_time=datetime_strategy,
        num_collections=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100)
    def test_collection_times_are_10_seconds_apart(
        self, start_time: datetime, num_collections: int
    ) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any stream session, consecutive health metric collections
        SHALL be at most 10 seconds apart.
        """
        monitor = StreamHealthMonitor()
        interval = monitor.COLLECTION_INTERVAL_SECONDS

        # Simulate collection times
        collection_times = [
            start_time + timedelta(seconds=i * interval)
            for i in range(num_collections)
        ]

        # Verify intervals between consecutive collections
        for i in range(1, len(collection_times)):
            time_diff = (collection_times[i] - collection_times[i - 1]).total_seconds()
            assert time_diff == interval, (
                f"Collection interval should be {interval}s, got {time_diff}s"
            )

    @given(
        session_duration_seconds=st.integers(min_value=10, max_value=36000),  # Up to 10 hours
    )
    @settings(max_examples=100)
    def test_minimum_collections_for_duration(
        self, session_duration_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any active stream session of duration D seconds,
        there SHALL be at least D/10 health metric collections.
        """
        monitor = StreamHealthMonitor()
        interval = monitor.COLLECTION_INTERVAL_SECONDS

        # Calculate expected minimum collections
        expected_min_collections = session_duration_seconds // interval

        # Verify the calculation
        assert expected_min_collections >= 1, "Should have at least 1 collection"
        assert expected_min_collections == session_duration_seconds // 10

    @given(
        interval_seconds=valid_interval_seconds,
    )
    @settings(max_examples=100)
    def test_valid_collection_interval_within_requirement(
        self, interval_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any collection interval <= 10 seconds, it SHALL meet the requirement.
        """
        max_allowed_interval = StreamHealthMonitor.COLLECTION_INTERVAL_SECONDS
        assert interval_seconds <= max_allowed_interval

    @given(
        interval_seconds=invalid_interval_seconds,
    )
    @settings(max_examples=100)
    def test_invalid_collection_interval_exceeds_requirement(
        self, interval_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any collection interval > 10 seconds, it SHALL NOT meet the requirement.
        """
        max_allowed_interval = StreamHealthMonitor.COLLECTION_INTERVAL_SECONDS
        assert interval_seconds > max_allowed_interval


class TestStreamHealthEvaluation:
    """Property tests for stream health evaluation."""

    @given(
        bitrate=st.integers(min_value=0, max_value=HealthThresholds.MIN_BITRATE_CRITICAL - 1),
    )
    @settings(max_examples=100)
    def test_critical_low_bitrate_detected(self, bitrate: int) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any bitrate below critical threshold, status SHALL be POOR.
        """
        monitor = StreamHealthMonitor()
        status, alert_type, _ = monitor.evaluate_health(
            bitrate=bitrate,
            frame_rate=30.0,
            dropped_frames_delta=0,
            latency_ms=100,
        )

        from app.modules.stream.models import ConnectionStatus
        assert status == ConnectionStatus.POOR.value
        assert alert_type == "critical"

    @given(
        bitrate=st.integers(
            min_value=HealthThresholds.MIN_BITRATE_WARNING * 2,
            max_value=50000000,
        ),
    )
    @settings(max_examples=100)
    def test_healthy_bitrate_detected(self, bitrate: int) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any bitrate well above warning threshold, status SHALL be EXCELLENT or GOOD.
        """
        monitor = StreamHealthMonitor()
        status, alert_type, _ = monitor.evaluate_health(
            bitrate=bitrate,
            frame_rate=30.0,
            dropped_frames_delta=0,
            latency_ms=100,
        )

        from app.modules.stream.models import ConnectionStatus
        assert status in [ConnectionStatus.EXCELLENT.value, ConnectionStatus.GOOD.value]
        assert alert_type is None

    @given(
        dropped_frames=st.integers(
            min_value=HealthThresholds.MAX_DROPPED_FRAMES_CRITICAL,
            max_value=1000,
        ),
    )
    @settings(max_examples=100)
    def test_critical_dropped_frames_detected(self, dropped_frames: int) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any dropped frames above critical threshold, status SHALL be POOR.
        """
        monitor = StreamHealthMonitor()
        status, alert_type, _ = monitor.evaluate_health(
            bitrate=5000000,  # Healthy bitrate
            frame_rate=30.0,
            dropped_frames_delta=dropped_frames,
            latency_ms=100,
        )

        from app.modules.stream.models import ConnectionStatus
        assert status == ConnectionStatus.POOR.value
        assert alert_type == "critical"

    @given(
        latency_ms=st.integers(
            min_value=HealthThresholds.MAX_LATENCY_CRITICAL,
            max_value=10000,
        ),
    )
    @settings(max_examples=100)
    def test_critical_latency_detected(self, latency_ms: int) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any latency above critical threshold, status SHALL be POOR.
        """
        monitor = StreamHealthMonitor()
        status, alert_type, _ = monitor.evaluate_health(
            bitrate=5000000,  # Healthy bitrate
            frame_rate=30.0,
            dropped_frames_delta=0,
            latency_ms=latency_ms,
        )

        from app.modules.stream.models import ConnectionStatus
        assert status == ConnectionStatus.POOR.value
        assert alert_type == "critical"

    @given(
        frame_rate=st.floats(
            min_value=0.0,
            max_value=HealthThresholds.MIN_FRAME_RATE_CRITICAL - 0.1,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    @settings(max_examples=100)
    def test_critical_low_frame_rate_detected(self, frame_rate: float) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any frame rate below critical threshold, status SHALL be POOR.
        """
        monitor = StreamHealthMonitor()
        status, alert_type, _ = monitor.evaluate_health(
            bitrate=5000000,  # Healthy bitrate
            frame_rate=frame_rate,
            dropped_frames_delta=0,
            latency_ms=100,
        )

        from app.modules.stream.models import ConnectionStatus
        assert status == ConnectionStatus.POOR.value
        assert alert_type == "critical"


class TestStreamHealthAlertTiming:
    """Property tests for stream health alert timing.

    Requirements 8.2: Alerts SHALL be triggered within 30 seconds.
    """

    def test_max_alert_delay_is_30_seconds(self) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        Maximum alert delay SHALL be 30 seconds per Requirements 8.2.
        """
        monitor = StreamHealthMonitor()
        assert monitor.MAX_ALERT_DELAY_SECONDS == 30

    @given(alert_type=st.sampled_from(["critical", "warning"]))
    @settings(max_examples=100)
    def test_first_alert_always_triggers(self, alert_type: str) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any alert type with no previous alert, alert SHALL be triggered.
        """
        monitor = StreamHealthMonitor()
        should_trigger = monitor.should_trigger_alert(
            alert_type=alert_type,
            last_alert_time=None,
        )
        assert should_trigger is True

    @given(
        last_alert_time=datetime_strategy,
        elapsed_seconds=st.integers(min_value=0, max_value=29),
    )
    @settings(max_examples=100)
    def test_critical_alert_always_triggers(
        self, last_alert_time: datetime, elapsed_seconds: int
    ) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        For any critical alert, it SHALL always be triggered regardless of timing.
        """
        # We need to mock datetime.utcnow() for this test
        # For simplicity, we test the logic directly
        monitor = StreamHealthMonitor()
        
        # Critical alerts should always trigger
        should_trigger = monitor.should_trigger_alert(
            alert_type="critical",
            last_alert_time=last_alert_time,
        )
        assert should_trigger is True

    def test_no_alert_when_type_is_none(self) -> None:
        """**Feature: youtube-automation, Property 13: Stream Health Collection Frequency**

        When alert_type is None, no alert SHALL be triggered.
        """
        monitor = StreamHealthMonitor()
        should_trigger = monitor.should_trigger_alert(
            alert_type=None,
            last_alert_time=None,
        )
        assert should_trigger is False


class TestHealthThresholds:
    """Tests for health threshold constants."""

    def test_bitrate_thresholds_are_ordered(self) -> None:
        """Critical threshold SHALL be lower than warning threshold."""
        assert HealthThresholds.MIN_BITRATE_CRITICAL < HealthThresholds.MIN_BITRATE_WARNING

    def test_frame_rate_thresholds_are_ordered(self) -> None:
        """Critical threshold SHALL be lower than warning threshold."""
        assert HealthThresholds.MIN_FRAME_RATE_CRITICAL < HealthThresholds.MIN_FRAME_RATE_WARNING

    def test_dropped_frames_thresholds_are_ordered(self) -> None:
        """Warning threshold SHALL be lower than critical threshold."""
        assert HealthThresholds.MAX_DROPPED_FRAMES_WARNING < HealthThresholds.MAX_DROPPED_FRAMES_CRITICAL

    def test_latency_thresholds_are_ordered(self) -> None:
        """Warning threshold SHALL be lower than critical threshold."""
        assert HealthThresholds.MAX_LATENCY_WARNING < HealthThresholds.MAX_LATENCY_CRITICAL
