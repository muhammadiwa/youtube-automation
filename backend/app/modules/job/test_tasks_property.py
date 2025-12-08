"""Property-based tests for job retry logic.

**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**
**Validates: Requirements 22.2**
"""

import math

import pytest
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
        self,
        initial_delay: float,
        max_delay: float,
        backoff_multiplier: float,
        attempt: int,
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**

        For any retry configuration and attempt number, the calculated delay
        SHALL follow the exponential backoff formula: initial_delay * (multiplier ^ (attempt - 1)),
        capped at max_delay.
        """
        config = RetryConfig(
            max_attempts=20,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )

        delay = config.calculate_delay(attempt)

        # Calculate expected delay using exponential backoff formula
        expected_uncapped = initial_delay * math.pow(backoff_multiplier, attempt - 1)
        expected = min(expected_uncapped, max_delay)

        # Verify the delay matches the expected exponential backoff
        assert abs(delay - expected) < 0.0001, (
            f"Delay {delay} does not match expected {expected} "
            f"for attempt {attempt} with initial={initial_delay}, "
            f"multiplier={backoff_multiplier}, max={max_delay}"
        )

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=10.0),
        max_delay=st.floats(min_value=10.0, max_value=100.0),
        backoff_multiplier=st.floats(min_value=1.5, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_delay_never_exceeds_max(
        self,
        initial_delay: float,
        max_delay: float,
        backoff_multiplier: float,
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**

        For any retry configuration, the calculated delay SHALL never exceed max_delay,
        regardless of the attempt number.
        """
        config = RetryConfig(
            max_attempts=100,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )

        # Test many attempts to ensure delay is always capped
        for attempt in range(1, 51):
            delay = config.calculate_delay(attempt)
            assert delay <= max_delay, (
                f"Delay {delay} exceeds max_delay {max_delay} at attempt {attempt}"
            )

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=10.0),
        max_delay=st.floats(min_value=100.0, max_value=500.0),
        backoff_multiplier=st.floats(min_value=1.5, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_delay_increases_monotonically_until_cap(
        self,
        initial_delay: float,
        max_delay: float,
        backoff_multiplier: float,
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**

        For any retry configuration, delays SHALL increase monotonically
        (or stay the same once capped) as attempt number increases.
        """
        config = RetryConfig(
            max_attempts=20,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_multiplier=backoff_multiplier,
        )

        previous_delay = 0.0
        for attempt in range(1, 21):
            delay = config.calculate_delay(attempt)
            assert delay >= previous_delay, (
                f"Delay decreased from {previous_delay} to {delay} at attempt {attempt}"
            )
            previous_delay = delay

    @given(attempt=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100)
    def test_first_attempt_uses_initial_delay(self, attempt: int) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**

        For any retry configuration, the first attempt (attempt=1) SHALL use
        exactly the initial_delay value.
        """
        for config_name, config in RETRY_CONFIGS.items():
            delay = config.calculate_delay(1)
            assert delay == config.initial_delay, (
                f"First attempt delay {delay} != initial_delay {config.initial_delay} "
                f"for config '{config_name}'"
            )

    @given(
        initial_delay=st.floats(min_value=1.0, max_value=5.0),
        backoff_multiplier=st.floats(min_value=2.0, max_value=3.0),
    )
    @settings(max_examples=100)
    def test_second_attempt_equals_initial_times_multiplier(
        self,
        initial_delay: float,
        backoff_multiplier: float,
    ) -> None:
        """**Feature: youtube-automation, Property 29: Job Retry Exponential Backoff**

        For any retry configuration with high enough max_delay, the second attempt
        delay SHALL equal initial_delay * backoff_multiplier.
        """
        config = RetryConfig(
            max_attempts=10,
            initial_delay=initial_delay,
            max_delay=1000.0,  # High enough to not cap
            backoff_multiplier=backoff_multiplier,
        )

        delay = config.calculate_delay(2)
        expected = initial_delay * backoff_multiplier

        assert abs(delay - expected) < 0.0001, (
            f"Second attempt delay {delay} != expected {expected}"
        )


class TestPredefinedRetryConfigs:
    """Tests for predefined retry configurations."""

    def test_all_configs_have_valid_values(self) -> None:
        """All predefined configs SHALL have positive, valid values."""
        for name, config in RETRY_CONFIGS.items():
            assert config.max_attempts > 0, f"Config '{name}' has invalid max_attempts"
            assert config.initial_delay > 0, f"Config '{name}' has invalid initial_delay"
            assert config.max_delay > 0, f"Config '{name}' has invalid max_delay"
            assert config.backoff_multiplier >= 1.0, f"Config '{name}' has invalid multiplier"
            assert config.max_delay >= config.initial_delay, (
                f"Config '{name}' has max_delay < initial_delay"
            )

    def test_upload_config_has_three_max_attempts(self) -> None:
        """Upload config SHALL have exactly 3 max attempts per Requirements 3.3."""
        config = RETRY_CONFIGS["upload"]
        assert config.max_attempts == 3

    def test_webhook_config_has_five_max_attempts(self) -> None:
        """Webhook config SHALL have exactly 5 max attempts per Requirements 29.4."""
        config = RETRY_CONFIGS["webhook"]
        assert config.max_attempts == 5

    def test_stream_reconnect_has_five_max_attempts(self) -> None:
        """Stream reconnect config SHALL have exactly 5 max attempts per Requirements 8.3."""
        config = RETRY_CONFIGS["stream_reconnect"]
        assert config.max_attempts == 5
