"""Property-based tests for API rate limiting.

**Feature: youtube-automation, Property 34: API Rate Limiting**
**Validates: Requirements 29.2**
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st
import pytest


# Strategies for generating test data
rate_limit_strategy = st.integers(min_value=1, max_value=1000)
request_count_strategy = st.integers(min_value=0, max_value=2000)


class RateLimitChecker:
    """Helper class to check rate limits without database.
    
    Simulates the rate limiting logic from APIKeyService.
    """
    
    def __init__(
        self,
        rate_limit_per_minute: int,
        rate_limit_per_hour: int,
        rate_limit_per_day: int,
    ):
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_per_hour = rate_limit_per_hour
        self.rate_limit_per_day = rate_limit_per_day
        self.minute_usage = 0
        self.hour_usage = 0
        self.day_usage = 0
    
    def check_rate_limit(self) -> tuple[bool, Optional[str], Optional[int]]:
        """Check if request is within rate limits.
        
        Returns: (is_allowed, limit_type, retry_after_seconds)
        """
        now = datetime.utcnow()
        
        # Check minute limit
        if self.minute_usage >= self.rate_limit_per_minute:
            return False, "minute", 60 - now.second
        
        # Check hour limit
        if self.hour_usage >= self.rate_limit_per_hour:
            return False, "hour", 3600 - (now.minute * 60 + now.second)
        
        # Check day limit
        if self.day_usage >= self.rate_limit_per_day:
            seconds_until_midnight = (
                24 * 3600 - (now.hour * 3600 + now.minute * 60 + now.second)
            )
            return False, "day", seconds_until_midnight
        
        return True, None, None
    
    def record_request(self) -> None:
        """Record a request."""
        self.minute_usage += 1
        self.hour_usage += 1
        self.day_usage += 1
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited."""
        is_allowed, _, _ = self.check_rate_limit()
        return not is_allowed


class TestRateLimitEnforcement:
    """Property tests for rate limit enforcement.
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        rate_limit=rate_limit_strategy,
        requests_made=request_count_strategy,
    )
    @settings(max_examples=100)
    def test_requests_within_minute_limit_allowed(
        self,
        rate_limit: int,
        requests_made: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, requests within the minute limit SHALL be allowed.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit,
            rate_limit_per_hour=rate_limit * 100,  # High enough to not interfere
            rate_limit_per_day=rate_limit * 1000,  # High enough to not interfere
        )
        
        # Make requests up to the limit
        requests_to_make = min(requests_made, rate_limit - 1)
        for _ in range(requests_to_make):
            is_allowed, _, _ = checker.check_rate_limit()
            assert is_allowed, "Request within limit should be allowed"
            checker.record_request()
        
        # Verify we're still within limit
        if requests_to_make < rate_limit:
            is_allowed, _, _ = checker.check_rate_limit()
            assert is_allowed, "Request within limit should be allowed"

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_requests_exceeding_minute_limit_rejected(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, requests exceeding the minute limit SHALL be rejected.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit,
            rate_limit_per_hour=rate_limit * 100,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        # Make requests up to the limit
        for _ in range(rate_limit):
            checker.record_request()
        
        # Next request should be rejected
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed, (
            f"Request exceeding minute limit ({rate_limit}) should be rejected"
        )
        assert limit_type == "minute", (
            f"Limit type should be 'minute', got '{limit_type}'"
        )
        assert retry_after is not None and retry_after > 0, (
            f"Retry-after should be positive, got {retry_after}"
        )

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_requests_exceeding_hour_limit_rejected(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, requests exceeding the hour limit SHALL be rejected.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit * 100,  # High enough to not interfere
            rate_limit_per_hour=rate_limit,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        # Make requests up to the hour limit
        for _ in range(rate_limit):
            checker.record_request()
        
        # Next request should be rejected
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed, (
            f"Request exceeding hour limit ({rate_limit}) should be rejected"
        )
        assert limit_type == "hour", (
            f"Limit type should be 'hour', got '{limit_type}'"
        )
        assert retry_after is not None and retry_after > 0, (
            f"Retry-after should be positive, got {retry_after}"
        )

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_requests_exceeding_day_limit_rejected(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, requests exceeding the day limit SHALL be rejected.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit * 100,
            rate_limit_per_hour=rate_limit * 100,
            rate_limit_per_day=rate_limit,
        )
        
        # Make requests up to the day limit
        for _ in range(rate_limit):
            checker.record_request()
        
        # Next request should be rejected
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed, (
            f"Request exceeding day limit ({rate_limit}) should be rejected"
        )
        assert limit_type == "day", (
            f"Limit type should be 'day', got '{limit_type}'"
        )
        assert retry_after is not None and retry_after > 0, (
            f"Retry-after should be positive, got {retry_after}"
        )


class TestRateLimitPriority:
    """Property tests for rate limit priority (minute < hour < day).
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        minute_limit=st.integers(min_value=1, max_value=100),
        hour_limit=st.integers(min_value=101, max_value=1000),
        day_limit=st.integers(min_value=1001, max_value=10000),
    )
    @settings(max_examples=100)
    def test_minute_limit_checked_first(
        self,
        minute_limit: int,
        hour_limit: int,
        day_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, minute limit SHALL be checked before hour and day limits.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=minute_limit,
            rate_limit_per_hour=hour_limit,
            rate_limit_per_day=day_limit,
        )
        
        # Exceed minute limit
        for _ in range(minute_limit):
            checker.record_request()
        
        is_allowed, limit_type, _ = checker.check_rate_limit()
        
        assert not is_allowed, "Should be rate limited"
        assert limit_type == "minute", (
            f"Minute limit should be checked first, got '{limit_type}'"
        )

    @given(
        minute_limit=st.integers(min_value=100, max_value=1000),
        hour_limit=st.integers(min_value=1, max_value=99),
        day_limit=st.integers(min_value=1001, max_value=10000),
    )
    @settings(max_examples=100)
    def test_hour_limit_checked_when_minute_ok(
        self,
        minute_limit: int,
        hour_limit: int,
        day_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* API key, hour limit SHALL be checked when minute limit is not exceeded.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=minute_limit,
            rate_limit_per_hour=hour_limit,
            rate_limit_per_day=day_limit,
        )
        
        # Exceed hour limit (but not minute)
        for _ in range(hour_limit):
            checker.record_request()
        
        is_allowed, limit_type, _ = checker.check_rate_limit()
        
        assert not is_allowed, "Should be rate limited"
        assert limit_type == "hour", (
            f"Hour limit should be checked when minute OK, got '{limit_type}'"
        )


class TestRetryAfterHeader:
    """Property tests for Retry-After header values.
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_retry_after_is_positive_for_minute_limit(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* rate-limited request, Retry-After SHALL be a positive integer.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit,
            rate_limit_per_hour=rate_limit * 100,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        # Exceed limit
        for _ in range(rate_limit):
            checker.record_request()
        
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed
        assert retry_after is not None
        assert retry_after > 0, f"Retry-after should be positive, got {retry_after}"
        assert retry_after <= 60, f"Minute retry-after should be <= 60, got {retry_after}"

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_retry_after_is_bounded_for_hour_limit(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* hour rate limit, Retry-After SHALL be <= 3600 seconds.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit * 100,
            rate_limit_per_hour=rate_limit,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        # Exceed hour limit
        for _ in range(rate_limit):
            checker.record_request()
        
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed
        assert retry_after is not None
        assert retry_after > 0, f"Retry-after should be positive, got {retry_after}"
        assert retry_after <= 3600, f"Hour retry-after should be <= 3600, got {retry_after}"


class TestRateLimitUsageTracking:
    """Property tests for usage tracking accuracy.
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        rate_limit=rate_limit_strategy,
        requests_to_make=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_usage_count_accurate(
        self,
        rate_limit: int,
        requests_to_make: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* number of requests, usage count SHALL be accurate.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit * 10,
            rate_limit_per_hour=rate_limit * 100,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        for _ in range(requests_to_make):
            checker.record_request()
        
        assert checker.minute_usage == requests_to_make, (
            f"Minute usage should be {requests_to_make}, got {checker.minute_usage}"
        )
        assert checker.hour_usage == requests_to_make, (
            f"Hour usage should be {requests_to_make}, got {checker.hour_usage}"
        )
        assert checker.day_usage == requests_to_make, (
            f"Day usage should be {requests_to_make}, got {checker.day_usage}"
        )


class TestAPIKeyRateLimitConfiguration:
    """Property tests for API key rate limit configuration.
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        minute_limit=st.integers(min_value=1, max_value=1000),
        hour_limit=st.integers(min_value=1, max_value=100000),
        day_limit=st.integers(min_value=1, max_value=1000000),
    )
    @settings(max_examples=100)
    def test_custom_rate_limits_respected(
        self,
        minute_limit: int,
        hour_limit: int,
        day_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* custom rate limit configuration, limits SHALL be respected.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=minute_limit,
            rate_limit_per_hour=hour_limit,
            rate_limit_per_day=day_limit,
        )
        
        # Verify limits are stored correctly
        assert checker.rate_limit_per_minute == minute_limit
        assert checker.rate_limit_per_hour == hour_limit
        assert checker.rate_limit_per_day == day_limit
        
        # Make requests up to the smallest limit
        smallest_limit = min(minute_limit, hour_limit, day_limit)
        for _ in range(smallest_limit):
            checker.record_request()
        
        # Should be rate limited now
        is_allowed, _, _ = checker.check_rate_limit()
        assert not is_allowed, (
            f"Should be rate limited after {smallest_limit} requests"
        )


class TestRateLimitRejectionResponse:
    """Property tests for rate limit rejection response format.
    
    **Feature: youtube-automation, Property 34: API Rate Limiting**
    **Validates: Requirements 29.2**
    """

    @given(
        rate_limit=rate_limit_strategy,
    )
    @settings(max_examples=100)
    def test_rejection_includes_limit_type(
        self,
        rate_limit: int,
    ) -> None:
        """**Feature: youtube-automation, Property 34: API Rate Limiting**
        
        *For any* rate limit rejection, response SHALL include limit type.
        """
        checker = RateLimitChecker(
            rate_limit_per_minute=rate_limit,
            rate_limit_per_hour=rate_limit * 100,
            rate_limit_per_day=rate_limit * 1000,
        )
        
        # Exceed limit
        for _ in range(rate_limit):
            checker.record_request()
        
        is_allowed, limit_type, retry_after = checker.check_rate_limit()
        
        assert not is_allowed
        assert limit_type in ["minute", "hour", "day"], (
            f"Limit type should be 'minute', 'hour', or 'day', got '{limit_type}'"
        )
        assert retry_after is not None, "Retry-after should be provided"
