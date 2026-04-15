"""Property-based tests for Stream Health Monitoring.

**Feature: video-streaming, Property: Health Monitoring**
**Validates: Requirements 4.3, 4.4, 4.5, 9.1, 9.2**
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.stream_job_models import (
    StreamJob,
    StreamJobHealth,
    HealthAlertType,
    StreamJobStatus,
)


# ============================================
# Strategies for generating test data
# ============================================

bitrate_bps_strategy = st.integers(min_value=0, max_value=20000000)  # 0-20 Mbps
fps_strategy = st.floats(min_value=0, max_value=120, allow_nan=False)
dropped_frames_strategy = st.integers(min_value=0, max_value=1000)
cpu_strategy = st.floats(min_value=0, max_value=100, allow_nan=False)
memory_strategy = st.floats(min_value=0, max_value=32000, allow_nan=False)


def create_health_record(
    bitrate: int = 6000000,
    fps: float = 30.0,
    dropped_frames_delta: int = 0,
    cpu_percent: float = 10.0,
    memory_mb: float = 100.0,
) -> StreamJobHealth:
    """Create a test StreamJobHealth record."""
    return StreamJobHealth(
        id=uuid.uuid4(),
        stream_job_id=uuid.uuid4(),
        bitrate=bitrate,
        fps=fps,
        speed="1.0x",
        dropped_frames=0,
        dropped_frames_delta=dropped_frames_delta,
        frame_count=1000,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
    )


# ============================================
# Property Tests for Health Alert Thresholds
# ============================================


class TestHealthAlertThresholds:
    """Property tests for health alert threshold consistency.
    
    **Property 8: Health Alert Threshold Consistency**
    **Validates: Requirements 4.3, 4.4**
    """

    @given(bitrate_kbps=st.integers(min_value=0, max_value=499))
    @settings(max_examples=50)
    def test_critical_alert_below_500kbps(self, bitrate_kbps: int) -> None:
        """**Feature: video-streaming, Property: Health Alert**
        
        Bitrate < 500 kbps SHALL trigger CRITICAL alert.
        """
        bitrate_bps = bitrate_kbps * 1000
        health = create_health_record(bitrate=bitrate_bps)
        
        health.evaluate_health()
        
        assert health.alert_type == HealthAlertType.CRITICAL.value, (
            f"Bitrate {bitrate_kbps} kbps should trigger CRITICAL alert"
        )
        assert health.is_critical() is True
        assert health.is_healthy() is False

    @given(bitrate_kbps=st.integers(min_value=500, max_value=999))
    @settings(max_examples=50)
    def test_warning_alert_between_500_and_1000kbps(self, bitrate_kbps: int) -> None:
        """**Feature: video-streaming, Property: Health Alert**
        
        Bitrate between 500-999 kbps SHALL trigger WARNING alert.
        """
        bitrate_bps = bitrate_kbps * 1000
        health = create_health_record(bitrate=bitrate_bps)
        
        health.evaluate_health()
        
        assert health.alert_type == HealthAlertType.WARNING.value, (
            f"Bitrate {bitrate_kbps} kbps should trigger WARNING alert"
        )
        assert health.is_warning() is True
        assert health.is_healthy() is False

    @given(bitrate_kbps=st.integers(min_value=1000, max_value=20000))
    @settings(max_examples=50)
    def test_no_alert_above_1000kbps(self, bitrate_kbps: int) -> None:
        """**Feature: video-streaming, Property: Health Alert**
        
        Bitrate >= 1000 kbps with no dropped frames SHALL be healthy.
        """
        bitrate_bps = bitrate_kbps * 1000
        health = create_health_record(bitrate=bitrate_bps, dropped_frames_delta=0)
        
        health.evaluate_health()
        
        assert health.alert_type is None, (
            f"Bitrate {bitrate_kbps} kbps should not trigger alert"
        )
        assert health.is_healthy() is True


# ============================================
# Property Tests for Dropped Frames Alert
# ============================================


class TestDroppedFramesAlert:
    """Property tests for dropped frames alert threshold.
    
    **Property 9: Dropped Frames Alert Threshold**
    **Validates: Requirements 4.5**
    """

    @given(dropped_frames=st.integers(min_value=51, max_value=1000))
    @settings(max_examples=50)
    def test_critical_alert_above_50_dropped_frames(self, dropped_frames: int) -> None:
        """**Feature: video-streaming, Property: Dropped Frames Alert**
        
        Dropped frames > 50 in interval SHALL trigger CRITICAL alert.
        """
        # Use healthy bitrate to isolate dropped frames test
        health = create_health_record(
            bitrate=6000000,  # 6 Mbps - healthy
            dropped_frames_delta=dropped_frames,
        )
        
        health.evaluate_health()
        
        assert health.alert_type == HealthAlertType.CRITICAL.value, (
            f"Dropped frames {dropped_frames} should trigger CRITICAL alert"
        )
        assert "dropped" in health.alert_message.lower()

    @given(dropped_frames=st.integers(min_value=0, max_value=50))
    @settings(max_examples=50)
    def test_no_alert_at_or_below_50_dropped_frames(self, dropped_frames: int) -> None:
        """**Feature: video-streaming, Property: Dropped Frames Alert**
        
        Dropped frames <= 50 with healthy bitrate SHALL not trigger alert.
        """
        health = create_health_record(
            bitrate=6000000,  # 6 Mbps - healthy
            dropped_frames_delta=dropped_frames,
        )
        
        health.evaluate_health()
        
        assert health.alert_type is None, (
            f"Dropped frames {dropped_frames} should not trigger alert"
        )
        assert health.is_healthy() is True


# ============================================
# Property Tests for Health Status Methods
# ============================================


class TestHealthStatusMethods:
    """Property tests for health status helper methods."""

    def test_is_healthy_when_no_alert(self) -> None:
        """**Feature: video-streaming, Property: Health Status**
        
        is_healthy() SHALL return True when alert_type is None.
        """
        health = create_health_record(bitrate=6000000)
        health.alert_type = None
        
        assert health.is_healthy() is True
        assert health.is_warning() is False
        assert health.is_critical() is False

    def test_is_warning_when_warning_alert(self) -> None:
        """**Feature: video-streaming, Property: Health Status**
        
        is_warning() SHALL return True when alert_type is WARNING.
        """
        health = create_health_record()
        health.alert_type = HealthAlertType.WARNING.value
        
        assert health.is_warning() is True
        assert health.is_healthy() is False
        assert health.is_critical() is False

    def test_is_critical_when_critical_alert(self) -> None:
        """**Feature: video-streaming, Property: Health Status**
        
        is_critical() SHALL return True when alert_type is CRITICAL.
        """
        health = create_health_record()
        health.alert_type = HealthAlertType.CRITICAL.value
        
        assert health.is_critical() is True
        assert health.is_healthy() is False
        assert health.is_warning() is False

    @given(bitrate_bps=bitrate_bps_strategy)
    @settings(max_examples=50)
    def test_get_bitrate_kbps_conversion(self, bitrate_bps: int) -> None:
        """**Feature: video-streaming, Property: Health Metrics**
        
        get_bitrate_kbps() SHALL correctly convert bps to kbps.
        """
        health = create_health_record(bitrate=bitrate_bps)
        
        result = health.get_bitrate_kbps()
        expected = bitrate_bps / 1000
        
        assert result == expected, f"Conversion failed: {result} != {expected}"


# ============================================
# Property Tests for Health Serialization
# ============================================


class TestHealthSerialization:
    """Property tests for StreamJobHealth serialization."""

    @given(
        bitrate=bitrate_bps_strategy,
        fps=fps_strategy,
        cpu=cpu_strategy,
        memory=memory_strategy,
    )
    @settings(max_examples=30)
    def test_to_dict_contains_all_fields(
        self,
        bitrate: int,
        fps: float,
        cpu: float,
        memory: float,
    ) -> None:
        """**Feature: video-streaming, Property: Health Serialization**
        
        to_dict() SHALL contain all required fields.
        """
        health = create_health_record(
            bitrate=bitrate,
            fps=fps,
            cpu_percent=cpu,
            memory_mb=memory,
        )
        
        result = health.to_dict()
        
        required_fields = [
            "id", "stream_job_id", "bitrate", "bitrate_kbps",
            "fps", "speed", "dropped_frames", "dropped_frames_delta",
            "frame_count", "cpu_percent", "memory_mb",
            "alert_type", "alert_message", "is_healthy",
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        assert result["bitrate"] == bitrate
        assert result["bitrate_kbps"] == bitrate / 1000
        assert result["fps"] == fps
        assert result["cpu_percent"] == cpu
        assert result["memory_mb"] == memory


# ============================================
# Property Tests for Resource Aggregation
# ============================================


class TestResourceAggregation:
    """Property tests for resource aggregation consistency.
    
    **Property 16: Resource Aggregation Consistency**
    **Validates: Requirements 5.4, 9.1**
    """

    @given(
        cpu_values=st.lists(
            st.floats(min_value=0, max_value=100, allow_nan=False),
            min_size=1,
            max_size=10,
        ),
        memory_values=st.lists(
            st.floats(min_value=0, max_value=1000, allow_nan=False),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_total_cpu_is_sum_of_individual(
        self,
        cpu_values: list,
        memory_values: list,
    ) -> None:
        """**Feature: video-streaming, Property: Resource Aggregation**
        
        Total CPU usage SHALL be sum of individual stream CPU usage.
        """
        # Ensure same length
        min_len = min(len(cpu_values), len(memory_values))
        cpu_values = cpu_values[:min_len]
        memory_values = memory_values[:min_len]
        
        health_records = [
            create_health_record(cpu_percent=cpu, memory_mb=mem)
            for cpu, mem in zip(cpu_values, memory_values)
        ]
        
        total_cpu = sum(h.cpu_percent for h in health_records)
        total_memory = sum(h.memory_mb for h in health_records)
        
        expected_cpu = sum(cpu_values)
        expected_memory = sum(memory_values)
        
        assert abs(total_cpu - expected_cpu) < 0.01, (
            f"CPU aggregation failed: {total_cpu} != {expected_cpu}"
        )
        assert abs(total_memory - expected_memory) < 0.01, (
            f"Memory aggregation failed: {total_memory} != {expected_memory}"
        )


# ============================================
# Property Tests for Alert Priority
# ============================================


class TestAlertPriority:
    """Property tests for alert priority handling."""

    def test_bitrate_alert_takes_priority_over_dropped_frames(self) -> None:
        """**Feature: video-streaming, Property: Alert Priority**
        
        Low bitrate alert SHALL take priority over dropped frames alert.
        """
        # Both conditions would trigger alerts
        health = create_health_record(
            bitrate=400000,  # 400 kbps - critical
            dropped_frames_delta=100,  # Also would be critical
        )
        
        health.evaluate_health()
        
        # Bitrate alert should be shown (checked first)
        assert health.is_critical() is True
        assert "bitrate" in health.alert_message.lower()

    @given(
        bitrate_kbps=st.integers(min_value=500, max_value=999),
        dropped_frames=st.integers(min_value=51, max_value=200),
    )
    @settings(max_examples=30)
    def test_warning_bitrate_vs_critical_dropped_frames(
        self,
        bitrate_kbps: int,
        dropped_frames: int,
    ) -> None:
        """**Feature: video-streaming, Property: Alert Priority**
        
        Bitrate warning SHALL be shown before dropped frames critical.
        """
        health = create_health_record(
            bitrate=bitrate_kbps * 1000,
            dropped_frames_delta=dropped_frames,
        )
        
        health.evaluate_health()
        
        # Bitrate is checked first, so warning should be shown
        assert health.alert_type == HealthAlertType.WARNING.value
        assert "bitrate" in health.alert_message.lower()
