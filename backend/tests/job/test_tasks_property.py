"""Property-based tests for job retry logic.

**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**
**Validates: Requirements 22.2**
"""

import math

from hypothesis import given, settings, strategies as st

from app.modules.job.tasks import RETRY_CONFIGS, RetryConfig


class TestRetryExponentialBackoff:
    """Property tests for exponential backoff retry logic."""

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=10.0),
        max_delay=st.floats(min_value=10.0, max_value=1000.0),
        backoff_multiplier=st.floats(min_value=1.1, max_value=5.0),
        attempt=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_delay_follows_exponential_pattern(
        self, initial_delay: float, max_delay: float, backoff_multiplier: float, attempt: int
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**"""
        config = RetryConfig(
            max_attempts=20,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )
        delay = config.calculate_delay(attempt)
        expected_uncapped = initial_delay * math.pow(backoff_multiplier, attempt - 1)
        expected = min(expected_uncapped, max_delay)
        assert abs(delay - expected) < 0.0001

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=10.0),
        max_delay=st.floats(min_value=10.0, max_value=100.0),
        backoff_multiplier=st.floats(min_value=1.5, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_delay_never_exceeds_max(
        self, initial_delay: float, max_delay: float, backoff_multiplier: float
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**"""
        config = RetryConfig(
            max_attempts=100,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )
        for attempt in range(1, 51):
            delay = config.calculate_delay(attempt)
            assert delay <= max_delay


    @given(
        initial_delay=st.floats(min_value=0.1, max_value=10.0),
        max_delay=st.floats(min_value=100.0, max_value=500.0),
        backoff_multiplier=st.floats(min_value=1.5, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_delay_increases_monotonically_until_cap(
        self, initial_delay: float, max_delay: float, backoff_multiplier: float
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**"""
        config = RetryConfig(
            max_attempts=20,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )
        previous_delay = 0.0
        for attempt in range(1, 21):
            delay = config.calculate_delay(attempt)
            assert delay >= previous_delay
            previous_delay = delay

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_first_attempt_uses_initial_delay(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**"""
        for config_name, config in RETRY_CONFIGS.items():
            delay = config.calculate_delay(1)
            assert delay == config.initial_delay

    @given(
        initial_delay=st.floats(min_value=1.0, max_value=5.0),
        backoff_multiplier=st.floats(min_value=2.0, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_second_attempt_equals_initial_times_multiplier(
        self, initial_delay: float, backoff_multiplier: float
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**"""
        config = RetryConfig(
            max_attempts=10,
            initial_delay=initial_delay,
            max_delay=1000.0,
            backoff_multiplier=backoff_multiplier,
        )
        delay = config.calculate_delay(2)
        expected = initial_delay * backoff_multiplier
        assert abs(delay - expected) < 0.0001


class TestPredefinedRetryConfigs:
    """Tests for predefined retry configurations."""

    def test_all_configs_have_valid_values(self) -> None:
        """All predefined configs SHALL have positive, valid values."""
        for name, config in RETRY_CONFIGS.items():
            assert config.max_attempts > 0
            assert config.initial_delay > 0
            assert config.max_delay > 0
            assert config.backoff_multiplier >= 1.0
            assert config.max_delay >= config.initial_delay

    def test_upload_config_has_three_max_attempts(self) -> None:
        """Upload config SHALL have exactly 3 max attempts per Requirements 3.3."""
        assert RETRY_CONFIGS["upload"].max_attempts == 3

    def test_webhook_config_has_five_max_attempts(self) -> None:
        """Webhook config SHALL have exactly 5 max attempts per Requirements 29.4."""
        assert RETRY_CONFIGS["webhook"].max_attempts == 5

    def test_stream_reconnect_has_five_max_attempts(self) -> None:
        """Stream reconnect config SHALL have exactly 5 max attempts per Requirements 8.3."""
        assert RETRY_CONFIGS["stream_reconnect"].max_attempts == 5
