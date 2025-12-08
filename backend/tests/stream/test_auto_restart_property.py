"""Property-based tests for stream auto-restart on disconnection.

**Feature: youtube-automation, Property: Auto-Restart Logic**
**Validates: Requirements 6.5**
"""

import sys
import math
from unittest.mock import MagicMock

# Mock celery_app before importing stream tasks
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st

from app.modules.stream.tasks import StreamAutoRestartManager
from app.modules.job.tasks import RetryConfig, RETRY_CONFIGS


class TestAutoRestartManager:
    """Property tests for auto-restart manager.

    Requirements 6.5: Auto-restart on unexpected disconnection.
    """

    @given(attempts=st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_restart_allowed_within_max_attempts(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any number of reconnection attempts, restart SHALL be allowed
        only if attempts < max_reconnection_attempts (5).
        """
        manager = StreamAutoRestartManager()

        should_restart = manager.should_attempt_restart(attempts)

        if attempts < manager.max_reconnection_attempts:
            assert should_restart is True, f"Should restart at attempt {attempts}"
        else:
            assert should_restart is False, f"Should not restart at attempt {attempts}"

    @given(attempts=st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_remaining_attempts_calculation(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any number of attempts, remaining attempts SHALL be
        max(0, max_reconnection_attempts - attempts).
        """
        manager = StreamAutoRestartManager()

        remaining = manager.get_remaining_attempts(attempts)
        expected = max(0, manager.max_reconnection_attempts - attempts)

        assert remaining == expected, f"Remaining should be {expected}, got {remaining}"

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_restart_delay_follows_exponential_backoff(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any attempt, restart delay SHALL follow exponential backoff pattern.
        """
        manager = StreamAutoRestartManager()
        config = manager.retry_config

        delay = manager.calculate_restart_delay(attempt)

        # Calculate expected delay
        expected_uncapped = config.initial_delay * math.pow(
            config.backoff_multiplier, attempt - 1
        )
        expected = min(expected_uncapped, config.max_delay)

        assert abs(delay - expected) < 0.0001, f"Delay mismatch at attempt {attempt}"

    @given(attempt=st.integers(min_value=1, max_value=20))
    @settings(max_examples=100)
    def test_restart_delay_never_exceeds_max(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any attempt, restart delay SHALL never exceed max_delay.
        """
        manager = StreamAutoRestartManager()

        delay = manager.calculate_restart_delay(attempt)

        assert delay <= manager.retry_config.max_delay, (
            f"Delay {delay} exceeds max {manager.retry_config.max_delay}"
        )

    @given(
        attempt1=st.integers(min_value=1, max_value=10),
        attempt2=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_restart_delay_increases_monotonically(
        self, attempt1: int, attempt2: int
    ) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any two attempts, later attempt SHALL have >= delay than earlier attempt.
        """
        manager = StreamAutoRestartManager()

        delay1 = manager.calculate_restart_delay(attempt1)
        delay2 = manager.calculate_restart_delay(attempt2)

        if attempt1 < attempt2:
            assert delay1 <= delay2, "Delay should increase with attempt number"
        elif attempt1 > attempt2:
            assert delay1 >= delay2, "Delay should increase with attempt number"
        else:
            assert delay1 == delay2, "Same attempt should have same delay"

    def test_max_reconnection_attempts_is_five(self) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        max_reconnection_attempts SHALL be 5 per design document.
        """
        manager = StreamAutoRestartManager()
        assert manager.max_reconnection_attempts == 5

    def test_uses_stream_reconnect_config(self) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        Auto-restart SHALL use stream_reconnect retry configuration.
        """
        manager = StreamAutoRestartManager()
        expected_config = RETRY_CONFIGS["stream_reconnect"]

        assert manager.retry_config.max_attempts == expected_config.max_attempts
        assert manager.retry_config.initial_delay == expected_config.initial_delay
        assert manager.retry_config.max_delay == expected_config.max_delay
        assert manager.retry_config.backoff_multiplier == expected_config.backoff_multiplier

    @given(attempts=st.integers(min_value=5, max_value=100))
    @settings(max_examples=100)
    def test_no_restart_after_max_attempts(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any attempts >= MAX_RECONNECTION_ATTEMPTS, restart SHALL NOT be allowed.
        """
        manager = StreamAutoRestartManager()

        should_restart = manager.should_attempt_restart(attempts)

        assert should_restart is False, f"Should not restart at attempt {attempts}"

    @given(attempts=st.integers(min_value=0, max_value=4))
    @settings(max_examples=100)
    def test_restart_allowed_before_max_attempts(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property: Auto-Restart Logic**

        For any attempts < MAX_RECONNECTION_ATTEMPTS (5), restart SHALL be allowed.
        """
        manager = StreamAutoRestartManager()

        should_restart = manager.should_attempt_restart(attempts)

        assert should_restart is True, f"Should restart at attempt {attempts}"


class TestAutoRestartConfig:
    """Tests for auto-restart configuration values."""

    def test_stream_reconnect_config_exists(self) -> None:
        """stream_reconnect config SHALL exist in RETRY_CONFIGS."""
        assert "stream_reconnect" in RETRY_CONFIGS

    def test_stream_reconnect_config_values(self) -> None:
        """stream_reconnect config SHALL have expected values per design."""
        config = RETRY_CONFIGS["stream_reconnect"]

        # Per design document: max_attempts=5, initial_delay=2.0, max_delay=30.0, backoff_multiplier=1.5
        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 30.0
        assert config.backoff_multiplier == 1.5

    def test_custom_retry_config_can_be_provided(self) -> None:
        """Custom retry config SHALL be accepted by manager."""
        custom_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
        )

        manager = StreamAutoRestartManager(retry_config=custom_config)

        assert manager.retry_config.max_attempts == 3
        assert manager.retry_config.initial_delay == 1.0


class TestAutoRestartDelaySequence:
    """Tests for the sequence of restart delays."""

    def test_delay_sequence_for_all_attempts(self) -> None:
        """Verify delay sequence for all 5 reconnection attempts."""
        manager = StreamAutoRestartManager()
        config = manager.retry_config

        expected_delays = []
        for attempt in range(1, 6):
            uncapped = config.initial_delay * math.pow(
                config.backoff_multiplier, attempt - 1
            )
            expected_delays.append(min(uncapped, config.max_delay))

        actual_delays = [
            manager.calculate_restart_delay(attempt) for attempt in range(1, 6)
        ]

        for i, (expected, actual) in enumerate(zip(expected_delays, actual_delays)):
            assert abs(expected - actual) < 0.0001, (
                f"Delay mismatch at attempt {i + 1}: expected {expected}, got {actual}"
            )

    def test_first_attempt_uses_initial_delay(self) -> None:
        """First reconnection attempt SHALL use initial_delay."""
        manager = StreamAutoRestartManager()

        delay = manager.calculate_restart_delay(1)

        assert delay == manager.retry_config.initial_delay
