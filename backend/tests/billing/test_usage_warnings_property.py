"""Property-based tests for usage warning thresholds.

**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
**Validates: Requirements 27.2**
"""

import uuid
from datetime import date, timedelta
from typing import Optional, List

from hypothesis import given, settings, strategies as st
import pytest

from app.modules.billing.metering import (
    WARNING_THRESHOLDS,
    UsageMeteringService,
    UsageWarning,
    calculate_usage_percent,
    get_warning_threshold,
    should_send_warning,
    get_all_pending_warnings,
)
from app.modules.billing.models import (
    PlanTier,
    UsageResourceType,
    PLAN_LIMITS,
)


# Strategies for generating test data
plan_tier_strategy = st.sampled_from([
    PlanTier.FREE.value,
    PlanTier.BASIC.value,
    PlanTier.PRO.value,
])

resource_type_strategy = st.sampled_from([
    UsageResourceType.API_CALLS.value,
    UsageResourceType.ENCODING_MINUTES.value,
    UsageResourceType.STORAGE_GB.value,
    UsageResourceType.BANDWIDTH_GB.value,
])

# Usage percentage strategies
below_50_percent = st.floats(min_value=0.0, max_value=49.9)
at_50_to_74_percent = st.floats(min_value=50.0, max_value=74.9)
at_75_to_89_percent = st.floats(min_value=75.0, max_value=89.9)
at_90_plus_percent = st.floats(min_value=90.0, max_value=100.0)
any_usage_percent = st.floats(min_value=0.0, max_value=150.0)


class TestUsageWarningThresholds:
    """Property tests for usage warning thresholds.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    @given(
        usage_percent=below_50_percent,
    )
    @settings(max_examples=100)
    def test_no_warning_below_50_percent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage below 50%, no warning threshold SHALL be reached.
        """
        threshold = get_warning_threshold(usage_percent)
        
        assert threshold is None, (
            f"Usage at {usage_percent}% should not trigger any warning, "
            f"but got threshold {threshold}"
        )

    @given(
        usage_percent=at_50_to_74_percent,
    )
    @settings(max_examples=100)
    def test_50_percent_warning_threshold(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage between 50% and 74.9%, the 50% warning threshold SHALL be reached.
        """
        threshold = get_warning_threshold(usage_percent)
        
        assert threshold == 50, (
            f"Usage at {usage_percent}% should trigger 50% warning, "
            f"but got threshold {threshold}"
        )

    @given(
        usage_percent=at_75_to_89_percent,
    )
    @settings(max_examples=100)
    def test_75_percent_warning_threshold(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage between 75% and 89.9%, the 75% warning threshold SHALL be reached.
        """
        threshold = get_warning_threshold(usage_percent)
        
        assert threshold == 75, (
            f"Usage at {usage_percent}% should trigger 75% warning, "
            f"but got threshold {threshold}"
        )

    @given(
        usage_percent=at_90_plus_percent,
    )
    @settings(max_examples=100)
    def test_90_percent_warning_threshold(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 90% or above, the 90% warning threshold SHALL be reached.
        """
        threshold = get_warning_threshold(usage_percent)
        
        assert threshold == 90, (
            f"Usage at {usage_percent}% should trigger 90% warning, "
            f"but got threshold {threshold}"
        )


class TestShouldSendWarning:
    """Property tests for should_send_warning function.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    @given(
        usage_percent=at_50_to_74_percent,
    )
    @settings(max_examples=100)
    def test_send_50_warning_when_not_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 50%+, if 50% warning not sent, it SHALL be sent.
        """
        result = should_send_warning(
            usage_percent,
            warning_50_sent=False,
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert result == 50, (
            f"Should send 50% warning for {usage_percent}% usage, got {result}"
        )

    @given(
        usage_percent=at_50_to_74_percent,
    )
    @settings(max_examples=100)
    def test_no_warning_when_50_already_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 50-74%, if 50% warning already sent, no warning SHALL be sent.
        """
        result = should_send_warning(
            usage_percent,
            warning_50_sent=True,
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert result is None, (
            f"Should not send warning for {usage_percent}% when 50% already sent, got {result}"
        )

    @given(
        usage_percent=at_75_to_89_percent,
    )
    @settings(max_examples=100)
    def test_send_75_warning_when_not_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 75%+, if 75% warning not sent, it SHALL be sent.
        """
        result = should_send_warning(
            usage_percent,
            warning_50_sent=True,  # 50% already sent
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert result == 75, (
            f"Should send 75% warning for {usage_percent}% usage, got {result}"
        )

    @given(
        usage_percent=at_90_plus_percent,
    )
    @settings(max_examples=100)
    def test_send_90_warning_when_not_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 90%+, if 90% warning not sent, it SHALL be sent.
        """
        result = should_send_warning(
            usage_percent,
            warning_50_sent=True,  # 50% already sent
            warning_75_sent=True,  # 75% already sent
            warning_90_sent=False,
        )
        
        assert result == 90, (
            f"Should send 90% warning for {usage_percent}% usage, got {result}"
        )

    @given(
        usage_percent=at_90_plus_percent,
    )
    @settings(max_examples=100)
    def test_no_warning_when_all_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage, if all warnings already sent, no warning SHALL be sent.
        """
        result = should_send_warning(
            usage_percent,
            warning_50_sent=True,
            warning_75_sent=True,
            warning_90_sent=True,
        )
        
        assert result is None, (
            f"Should not send warning when all already sent, got {result}"
        )


class TestGetAllPendingWarnings:
    """Property tests for get_all_pending_warnings function.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    @given(
        usage_percent=at_90_plus_percent,
    )
    @settings(max_examples=100)
    def test_all_warnings_pending_when_none_sent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 90%+, if no warnings sent, all three SHALL be pending.
        """
        pending = get_all_pending_warnings(
            usage_percent,
            warning_50_sent=False,
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert 50 in pending, f"50% warning should be pending for {usage_percent}%"
        assert 75 in pending, f"75% warning should be pending for {usage_percent}%"
        assert 90 in pending, f"90% warning should be pending for {usage_percent}%"
        assert len(pending) == 3, f"All 3 warnings should be pending, got {len(pending)}"

    @given(
        usage_percent=at_75_to_89_percent,
    )
    @settings(max_examples=100)
    def test_two_warnings_pending_at_75_percent(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage at 75-89%, if no warnings sent, 50% and 75% SHALL be pending.
        """
        pending = get_all_pending_warnings(
            usage_percent,
            warning_50_sent=False,
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert 50 in pending, f"50% warning should be pending for {usage_percent}%"
        assert 75 in pending, f"75% warning should be pending for {usage_percent}%"
        assert 90 not in pending, f"90% warning should NOT be pending for {usage_percent}%"

    @given(
        usage_percent=below_50_percent,
    )
    @settings(max_examples=100)
    def test_no_warnings_pending_below_50(
        self,
        usage_percent: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage below 50%, no warnings SHALL be pending.
        """
        pending = get_all_pending_warnings(
            usage_percent,
            warning_50_sent=False,
            warning_75_sent=False,
            warning_90_sent=False,
        )
        
        assert len(pending) == 0, (
            f"No warnings should be pending for {usage_percent}%, got {pending}"
        )


class TestCalculateUsagePercent:
    """Property tests for calculate_usage_percent function.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    @given(
        used=st.floats(min_value=0.0, max_value=1000.0),
        limit=st.floats(min_value=1.0, max_value=1000.0),
    )
    @settings(max_examples=100)
    def test_usage_percent_calculation(
        self,
        used: float,
        limit: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* usage and limit, percentage SHALL be accurately calculated.
        """
        result = calculate_usage_percent(used, limit)
        expected = (used / limit) * 100
        
        assert abs(result - expected) < 0.001, (
            f"Usage percent calculation incorrect: "
            f"used={used}, limit={limit}, expected={expected}, actual={result}"
        )

    @given(
        used=st.floats(min_value=0.0, max_value=1000.0),
    )
    @settings(max_examples=100)
    def test_unlimited_returns_zero_percent(
        self,
        used: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* unlimited resource (-1 limit), usage percent SHALL be 0%.
        """
        result = calculate_usage_percent(used, -1)
        
        assert result == 0.0, (
            f"Unlimited resource should return 0%, got {result}"
        )

    @given(
        used=st.floats(min_value=0.1, max_value=1000.0),
    )
    @settings(max_examples=100)
    def test_zero_limit_returns_100_percent(
        self,
        used: float,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* zero limit, usage percent SHALL be 100%.
        """
        result = calculate_usage_percent(used, 0)
        
        assert result == 100.0, (
            f"Zero limit should return 100%, got {result}"
        )


class TestUsageMeteringServiceWarnings:
    """Property tests for UsageMeteringService warning generation.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    def _create_metering_service(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> UsageMeteringService:
        """Create a metering service for testing."""
        user_id = uuid.uuid4()
        subscription_id = uuid.uuid4()
        today = date.today()
        
        return UsageMeteringService(
            user_id=user_id,
            subscription_id=subscription_id,
            plan_tier=plan_tier,
            billing_period_start=today,
            billing_period_end=today + timedelta(days=30),
        )

    @given(
        plan_tier=plan_tier_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_warning_at_50_percent(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* plan and resource, reaching 50% SHALL trigger a warning.
        """
        service = self._create_metering_service(plan_tier, resource_type)
        limit = service.get_limit(resource_type)
        
        # Skip unlimited resources
        if limit == -1:
            return
        
        # Set usage to exactly 50%
        usage_at_50 = limit * 0.5
        new_total, warning = service.record_usage(resource_type, usage_at_50)
        
        assert warning is not None, (
            f"Warning should be generated at 50% for {resource_type}"
        )
        assert warning.threshold_percent == 50, (
            f"Warning threshold should be 50, got {warning.threshold_percent}"
        )

    @given(
        plan_tier=plan_tier_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_warning_at_75_percent(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* plan and resource, reaching 75% SHALL trigger a warning.
        """
        service = self._create_metering_service(plan_tier, resource_type)
        limit = service.get_limit(resource_type)
        
        # Skip unlimited resources
        if limit == -1:
            return
        
        # First reach 50% to send that warning
        service.set_current_usage(resource_type, limit * 0.5)
        service.set_warnings_sent(resource_type, {50})
        
        # Now add more to reach 75%
        additional = limit * 0.25
        new_total, warning = service.record_usage(resource_type, additional)
        
        assert warning is not None, (
            f"Warning should be generated at 75% for {resource_type}"
        )
        assert warning.threshold_percent == 75, (
            f"Warning threshold should be 75, got {warning.threshold_percent}"
        )

    @given(
        plan_tier=plan_tier_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_warning_at_90_percent(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* plan and resource, reaching 90% SHALL trigger a warning.
        """
        service = self._create_metering_service(plan_tier, resource_type)
        limit = service.get_limit(resource_type)
        
        # Skip unlimited resources
        if limit == -1:
            return
        
        # First reach 75% and mark warnings as sent
        service.set_current_usage(resource_type, limit * 0.75)
        service.set_warnings_sent(resource_type, {50, 75})
        
        # Now add more to reach 90%
        additional = limit * 0.15
        new_total, warning = service.record_usage(resource_type, additional)
        
        assert warning is not None, (
            f"Warning should be generated at 90% for {resource_type}"
        )
        assert warning.threshold_percent == 90, (
            f"Warning threshold should be 90, got {warning.threshold_percent}"
        )

    @given(
        plan_tier=plan_tier_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_no_duplicate_warnings(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* plan and resource, the same warning SHALL NOT be sent twice.
        """
        service = self._create_metering_service(plan_tier, resource_type)
        limit = service.get_limit(resource_type)
        
        # Skip unlimited resources
        if limit == -1:
            return
        
        # Reach 50% - should get warning
        usage_at_50 = limit * 0.5
        _, warning1 = service.record_usage(resource_type, usage_at_50)
        
        assert warning1 is not None, "First 50% warning should be sent"
        assert warning1.threshold_percent == 50
        
        # Add small amount (still at 50%) - should NOT get warning
        _, warning2 = service.record_usage(resource_type, limit * 0.01)
        
        assert warning2 is None, (
            f"Duplicate 50% warning should not be sent, got {warning2}"
        )

    @given(
        plan_tier=plan_tier_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_progressive_warnings_order(
        self,
        plan_tier: str,
        resource_type: str,
    ) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        *For any* plan and resource, warnings SHALL be sent in order: 50%, 75%, 90%.
        """
        service = self._create_metering_service(plan_tier, resource_type)
        limit = service.get_limit(resource_type)
        
        # Skip unlimited resources
        if limit == -1:
            return
        
        warnings_received = []
        
        # Gradually increase usage
        increments = [0.5, 0.25, 0.15]  # 50%, 75%, 90%
        for increment in increments:
            _, warning = service.record_usage(resource_type, limit * increment)
            if warning:
                warnings_received.append(warning.threshold_percent)
        
        # Verify order
        assert warnings_received == [50, 75, 90], (
            f"Warnings should be in order [50, 75, 90], got {warnings_received}"
        )


class TestWarningThresholdsConstant:
    """Tests for WARNING_THRESHOLDS constant.
    
    **Feature: youtube-automation, Property 32: Usage Warning Thresholds**
    **Validates: Requirements 27.2**
    """

    def test_warning_thresholds_are_50_75_90(self) -> None:
        """**Feature: youtube-automation, Property 32: Usage Warning Thresholds**
        
        Warning thresholds SHALL be exactly 50%, 75%, and 90%.
        """
        assert WARNING_THRESHOLDS == [50, 75, 90], (
            f"Warning thresholds should be [50, 75, 90], got {WARNING_THRESHOLDS}"
        )

    def test_warning_thresholds_are_sorted(self) -> None:
        """Warning thresholds SHALL be in ascending order."""
        assert WARNING_THRESHOLDS == sorted(WARNING_THRESHOLDS), (
            f"Warning thresholds should be sorted, got {WARNING_THRESHOLDS}"
        )

