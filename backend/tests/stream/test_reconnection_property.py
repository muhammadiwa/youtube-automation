"""Property-based tests for stream reconnection attempt limit.

**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**
**Validates: Requirements 8.3, 8.4**
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Mock celery_app before importing stream tasks
sys.modules["app.core.celery_app"] = MagicMock()

from hypothesis import given, settings, strategies as st, assume

from app.modules.stream.tasks import (
    StreamReconnectionManager,
    StreamAutoRestartManager,
    STREAM_RECONNECT_CONFIG,
)


# Strategy for generating valid attempt counts
valid_attempts = st.integers(min_value=0, max_value=4)
exceeded_attempts = st.integers(min_value=5, max_value=100)
all_attempts = st.integers(min_value=0, max_value=100)


class TestReconnectionAttemptLimit:
    """Property tests for reconnection attempt limit.

    Requirements 8.3: System SHALL attempt reconnection with exponential backoff up to 5 times.
    Requirements 8.4: When reconnection fails, system SHALL execute failover.
    """

    def test_max_reconnection_attempts_is_5(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        Maximum reconnection attempts SHALL be exactly 5 per Requirements 8.3.
        """
        manager = StreamReconnectionManager()
        assert manager.max_reconnection_attempts == 5

    @given(attempts=valid_attempts)
    @settings(max_examples=100)
    def test_reconnection_allowed_within_limit(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt count less than 5, reconnection SHALL be allowed.
        """
        manager = StreamReconnectionManager()
        should_reconnect = manager.should_attempt_reconnection(attempts)
        
        assert should_reconnect is True, (
            f"Reconnection should be allowed at attempt {attempts}"
        )

    @given(attempts=exceeded_attempts)
    @settings(max_examples=100)
    def test_reconnection_denied_after_limit(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt count >= 5, reconnection SHALL NOT be allowed.
        """
        manager = StreamReconnectionManager()
        should_reconnect = manager.should_attempt_reconnection(attempts)
        
        assert should_reconnect is False, (
            f"Reconnection should be denied at attempt {attempts}"
        )

    def test_boundary_at_4_attempts_allows_reconnection(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        At exactly 4 attempts (5th attempt pending), reconnection SHALL be allowed.
        """
        manager = StreamReconnectionManager()
        should_reconnect = manager.should_attempt_reconnection(4)
        
        assert should_reconnect is True

    def test_boundary_at_5_attempts_denies_reconnection(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        At exactly 5 attempts, reconnection SHALL NOT be allowed (failover triggered).
        """
        manager = StreamReconnectionManager()
        should_reconnect = manager.should_attempt_reconnection(5)
        
        assert should_reconnect is False


class TestExponentialBackoff:
    """Property tests for exponential backoff delay calculation."""

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_delay_increases_with_attempts(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt, delay SHALL increase with each subsequent attempt.
        """
        manager = StreamReconnectionManager()
        
        if attempt > 1:
            current_delay = manager.calculate_reconnection_delay(attempt)
            previous_delay = manager.calculate_reconnection_delay(attempt - 1)
            
            assert current_delay >= previous_delay, (
                f"Delay at attempt {attempt} ({current_delay}s) should be >= "
                f"delay at attempt {attempt - 1} ({previous_delay}s)"
            )

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_delay_is_positive(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt, delay SHALL be positive.
        """
        manager = StreamReconnectionManager()
        delay = manager.calculate_reconnection_delay(attempt)
        
        assert delay > 0, f"Delay at attempt {attempt} should be positive"

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_delay_has_upper_bound(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt, delay SHALL not exceed the configured maximum.
        """
        manager = StreamReconnectionManager()
        delay = manager.calculate_reconnection_delay(attempt)
        max_delay = manager.retry_config.max_delay
        
        assert delay <= max_delay, (
            f"Delay {delay}s at attempt {attempt} should not exceed max {max_delay}s"
        )

    def test_first_attempt_uses_initial_delay(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        First attempt SHALL use the initial delay from config.
        """
        manager = StreamReconnectionManager()
        delay = manager.calculate_reconnection_delay(1)
        initial_delay = manager.retry_config.initial_delay
        
        assert delay == initial_delay, (
            f"First attempt delay {delay}s should equal initial delay {initial_delay}s"
        )


class TestAutoRestartManager:
    """Property tests for StreamAutoRestartManager (used in stream tasks)."""

    def test_max_attempts_is_5(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        StreamAutoRestartManager max attempts SHALL be 5.
        """
        manager = StreamAutoRestartManager()
        assert manager.max_reconnection_attempts == 5

    @given(attempts=valid_attempts)
    @settings(max_examples=100)
    def test_restart_allowed_within_limit(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt count less than 5, restart SHALL be allowed.
        """
        manager = StreamAutoRestartManager()
        should_restart = manager.should_attempt_restart(attempts)
        
        assert should_restart is True

    @given(attempts=exceeded_attempts)
    @settings(max_examples=100)
    def test_restart_denied_after_limit(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt count >= 5, restart SHALL NOT be allowed.
        """
        manager = StreamAutoRestartManager()
        should_restart = manager.should_attempt_restart(attempts)
        
        assert should_restart is False

    @given(attempts=all_attempts)
    @settings(max_examples=100)
    def test_remaining_attempts_calculation(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        Remaining attempts SHALL be correctly calculated.
        """
        manager = StreamAutoRestartManager()
        remaining = manager.get_remaining_attempts(attempts)
        
        expected = max(0, manager.max_reconnection_attempts - attempts)
        assert remaining == expected, (
            f"Remaining attempts should be {expected}, got {remaining}"
        )


class TestReconnectionConsistency:
    """Tests for consistency between reconnection managers."""

    def test_managers_have_same_max_attempts(self) -> None:
        """Both managers SHALL have the same max attempts limit."""
        reconnection_manager = StreamReconnectionManager()
        auto_restart_manager = StreamAutoRestartManager()
        
        assert reconnection_manager.max_reconnection_attempts == auto_restart_manager.max_reconnection_attempts

    @given(attempts=all_attempts)
    @settings(max_examples=100)
    def test_managers_agree_on_should_attempt(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        Both managers SHALL agree on whether to attempt reconnection.
        """
        reconnection_manager = StreamReconnectionManager()
        auto_restart_manager = StreamAutoRestartManager()
        
        reconnection_result = reconnection_manager.should_attempt_reconnection(attempts)
        restart_result = auto_restart_manager.should_attempt_restart(attempts)
        
        assert reconnection_result == restart_result, (
            f"Managers disagree at {attempts} attempts: "
            f"reconnection={reconnection_result}, restart={restart_result}"
        )


class TestFailoverTrigger:
    """Property tests for failover trigger conditions."""

    @given(attempts=exceeded_attempts)
    @settings(max_examples=100)
    def test_failover_triggered_after_max_attempts(self, attempts: int) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        For any attempt count >= 5, failover SHALL be triggered.
        """
        manager = StreamReconnectionManager()
        should_reconnect = manager.should_attempt_reconnection(attempts)
        
        # If reconnection is not allowed, failover should be triggered
        failover_should_trigger = not should_reconnect
        
        assert failover_should_trigger is True, (
            f"Failover should be triggered at {attempts} attempts"
        )

    def test_failover_not_triggered_within_limit(self) -> None:
        """**Feature: youtube-automation, Property 14: Reconnection Attempt Limit**

        Within the attempt limit, failover SHALL NOT be triggered.
        """
        manager = StreamReconnectionManager()
        
        for attempts in range(5):
            should_reconnect = manager.should_attempt_reconnection(attempts)
            failover_should_trigger = not should_reconnect
            
            assert failover_should_trigger is False, (
                f"Failover should not be triggered at {attempts} attempts"
            )


class TestRetryConfigIntegration:
    """Tests for retry configuration integration."""

    def test_uses_stream_reconnect_config(self) -> None:
        """Manager SHALL use the stream_reconnect retry configuration."""
        manager = StreamReconnectionManager()
        
        # Verify config is loaded
        assert manager.retry_config is not None
        assert manager.retry_config.max_attempts >= 1
        assert manager.retry_config.initial_delay > 0
        assert manager.retry_config.max_delay > 0
        assert manager.retry_config.backoff_multiplier >= 1

    def test_default_config_values(self) -> None:
        """Default configuration SHALL have reasonable values."""
        config = STREAM_RECONNECT_CONFIG
        
        assert config.max_attempts >= 3, "Should have at least 3 retry attempts"
        assert config.initial_delay >= 1.0, "Initial delay should be at least 1 second"
        assert config.max_delay <= 60.0, "Max delay should not exceed 60 seconds"
        assert config.backoff_multiplier >= 1.0, "Backoff multiplier should be >= 1"
