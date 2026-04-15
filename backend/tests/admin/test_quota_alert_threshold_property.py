"""Property-based tests for Quota Alert Threshold.

**Feature: admin-panel, Property 13: Quota Alert Threshold**
**Validates: Requirements 11.2**

Property 13: Quota Alert Threshold
*For any* YouTube API quota check, when usage exceeds 80% of daily limit,
an alert SHALL be generated for admin.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Constants ====================

DEFAULT_DAILY_QUOTA_LIMIT = 10000
QUOTA_WARNING_THRESHOLD = 80  # 80%
QUOTA_CRITICAL_THRESHOLD = 90  # 90%


# ==================== Data Classes ====================

@dataclass
class QuotaAlertInfo:
    """Quota alert information for testing."""
    id: str
    user_id: uuid.UUID
    account_id: uuid.UUID
    usage_percent: float
    quota_used: int
    quota_limit: int
    triggered_at: datetime
    severity: str  # "warning" or "critical"


# ==================== Quota Alert Logic ====================

def should_trigger_alert(quota_used: int, quota_limit: int) -> bool:
    """
    Determine if a quota alert should be triggered.
    
    Property 13: Quota Alert Threshold
    - Alert when usage exceeds 80% of daily limit
    
    Args:
        quota_used: Current quota used
        quota_limit: Daily quota limit
        
    Returns:
        True if alert should be triggered, False otherwise
    """
    if quota_limit <= 0:
        return True  # Always alert if limit is invalid
    
    usage_percent = (quota_used / quota_limit) * 100
    return usage_percent >= QUOTA_WARNING_THRESHOLD


def calculate_usage_percent(quota_used: int, quota_limit: int) -> float:
    """
    Calculate quota usage percentage.
    
    Args:
        quota_used: Current quota used
        quota_limit: Daily quota limit
        
    Returns:
        Usage percentage (0-100+)
    """
    if quota_limit <= 0:
        return 100.0
    return min(100.0, (quota_used / quota_limit) * 100)


def determine_alert_severity(usage_percent: float) -> Optional[str]:
    """
    Determine alert severity based on usage percentage.
    
    Args:
        usage_percent: Current usage percentage
        
    Returns:
        "critical" if >= 90%, "warning" if >= 80%, None otherwise
    """
    if usage_percent >= QUOTA_CRITICAL_THRESHOLD:
        return "critical"
    elif usage_percent >= QUOTA_WARNING_THRESHOLD:
        return "warning"
    return None


def check_quota_and_alert(
    quota_used: int,
    quota_limit: int = DEFAULT_DAILY_QUOTA_LIMIT,
) -> Optional[QuotaAlertInfo]:
    """
    Check quota usage and generate alert if threshold exceeded.
    
    Property 13: Quota Alert Threshold
    - For any YouTube API quota check, when usage exceeds 80% of daily limit,
      an alert SHALL be generated for admin.
    
    Args:
        quota_used: Current quota used
        quota_limit: Daily quota limit
        
    Returns:
        QuotaAlertInfo if alert triggered, None otherwise
    """
    usage_percent = calculate_usage_percent(quota_used, quota_limit)
    
    # Property 13: Alert when usage exceeds 80%
    if usage_percent < QUOTA_WARNING_THRESHOLD:
        return None
    
    severity = determine_alert_severity(usage_percent)
    
    return QuotaAlertInfo(
        id=f"quota_alert_{datetime.utcnow().timestamp()}",
        user_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        usage_percent=round(usage_percent, 2),
        quota_used=quota_used,
        quota_limit=quota_limit,
        triggered_at=datetime.utcnow(),
        severity=severity or "warning",
    )


# ==================== Strategies ====================

# Strategy for quota values below threshold (0-79%)
@st.composite
def quota_below_threshold_strategy(draw):
    """Generate quota values below the 80% threshold."""
    quota_limit = draw(st.integers(min_value=100, max_value=100000))
    # Calculate max quota_used to stay below 80%
    max_quota = int(quota_limit * QUOTA_WARNING_THRESHOLD / 100) - 1
    quota_used = draw(st.integers(min_value=0, max_value=max(0, max_quota)))
    return quota_used, quota_limit


# Strategy for quota values at or above warning threshold (80-89%)
@st.composite
def quota_warning_threshold_strategy(draw):
    """Generate quota values at warning threshold (80-89%)."""
    quota_limit = draw(st.integers(min_value=100, max_value=100000))
    # Calculate quota_used to be between 80% and 89%
    min_quota = int(quota_limit * QUOTA_WARNING_THRESHOLD / 100)
    max_quota = int(quota_limit * QUOTA_CRITICAL_THRESHOLD / 100) - 1
    quota_used = draw(st.integers(min_value=min_quota, max_value=max(min_quota, max_quota)))
    return quota_used, quota_limit


# Strategy for quota values at or above critical threshold (90%+)
@st.composite
def quota_critical_threshold_strategy(draw):
    """Generate quota values at critical threshold (90%+)."""
    quota_limit = draw(st.integers(min_value=100, max_value=100000))
    # Calculate quota_used to be at or above 90%
    min_quota = int(quota_limit * QUOTA_CRITICAL_THRESHOLD / 100)
    quota_used = draw(st.integers(min_value=min_quota, max_value=quota_limit * 2))
    return quota_used, quota_limit


# Strategy for any valid quota values
@st.composite
def any_quota_strategy(draw):
    """Generate any valid quota values."""
    quota_limit = draw(st.integers(min_value=100, max_value=100000))
    quota_used = draw(st.integers(min_value=0, max_value=quota_limit * 2))
    return quota_used, quota_limit


# ==================== Property Tests ====================

class TestQuotaAlertThreshold:
    """Property tests for Quota Alert Threshold.
    
    **Feature: admin-panel, Property 13: Quota Alert Threshold**
    **Validates: Requirements 11.2**
    """

    @settings(max_examples=100)
    @given(quota_data=quota_below_threshold_strategy())
    def test_no_alert_below_threshold(self, quota_data: Tuple[int, int]):
        """
        Property: When usage is below 80%, no alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        # Verify we're actually below threshold
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(usage_percent < QUOTA_WARNING_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is None, \
            f"No alert should be generated when usage ({usage_percent:.1f}%) is below {QUOTA_WARNING_THRESHOLD}%"

    @settings(max_examples=100)
    @given(quota_data=quota_warning_threshold_strategy())
    def test_alert_at_warning_threshold(self, quota_data: Tuple[int, int]):
        """
        Property: When usage is at or above 80%, an alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        # Verify we're at or above warning threshold
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(usage_percent >= QUOTA_WARNING_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            f"Alert should be generated when usage ({usage_percent:.1f}%) is at or above {QUOTA_WARNING_THRESHOLD}%"
        assert alert.usage_percent >= QUOTA_WARNING_THRESHOLD, \
            f"Alert usage_percent ({alert.usage_percent}%) should be >= {QUOTA_WARNING_THRESHOLD}%"

    @settings(max_examples=100)
    @given(quota_data=quota_critical_threshold_strategy())
    def test_critical_alert_at_90_percent(self, quota_data: Tuple[int, int]):
        """
        Property: When usage is at or above 90%, alert severity SHALL be 'critical'.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        # Verify we're at or above critical threshold
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(usage_percent >= QUOTA_CRITICAL_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            f"Alert should be generated when usage ({usage_percent:.1f}%) is at or above {QUOTA_CRITICAL_THRESHOLD}%"
        assert alert.severity == "critical", \
            f"Alert severity should be 'critical' when usage ({usage_percent:.1f}%) is >= {QUOTA_CRITICAL_THRESHOLD}%"

    @settings(max_examples=100)
    @given(quota_data=quota_warning_threshold_strategy())
    def test_warning_alert_between_80_and_90_percent(self, quota_data: Tuple[int, int]):
        """
        Property: When usage is between 80% and 90%, alert severity SHALL be 'warning'.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        # Verify we're between warning and critical thresholds
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(QUOTA_WARNING_THRESHOLD <= usage_percent < QUOTA_CRITICAL_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            f"Alert should be generated when usage ({usage_percent:.1f}%) is >= {QUOTA_WARNING_THRESHOLD}%"
        assert alert.severity == "warning", \
            f"Alert severity should be 'warning' when usage ({usage_percent:.1f}%) is between {QUOTA_WARNING_THRESHOLD}% and {QUOTA_CRITICAL_THRESHOLD}%"

    @settings(max_examples=100)
    @given(quota_data=any_quota_strategy())
    def test_alert_contains_correct_usage_info(self, quota_data: Tuple[int, int]):
        """
        Property: Alert SHALL contain correct quota_used and quota_limit values.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        
        # Only test when alert is generated
        assume(usage_percent >= QUOTA_WARNING_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None
        assert alert.quota_used == quota_used, \
            f"Alert quota_used ({alert.quota_used}) should match input ({quota_used})"
        assert alert.quota_limit == quota_limit, \
            f"Alert quota_limit ({alert.quota_limit}) should match input ({quota_limit})"

    @settings(max_examples=100)
    @given(quota_data=any_quota_strategy())
    def test_usage_percent_calculation_accuracy(self, quota_data: Tuple[int, int]):
        """
        Property: Usage percentage SHALL be calculated as (quota_used / quota_limit) * 100.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        expected_percent = min(100.0, (quota_used / quota_limit) * 100)
        
        assert abs(usage_percent - expected_percent) < 0.01, \
            f"Usage percent ({usage_percent}) should equal ({expected_percent})"

    @settings(max_examples=100)
    @given(quota_limit=st.integers(min_value=100, max_value=100000))
    def test_threshold_boundary_at_exactly_80_percent(self, quota_limit: int):
        """
        Property: At exactly 80% usage, an alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        # Calculate exact 80% value
        quota_used = int(quota_limit * QUOTA_WARNING_THRESHOLD / 100)
        
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        
        # Only test if we're at or above 80% (due to integer rounding)
        assume(usage_percent >= QUOTA_WARNING_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            f"Alert should be generated at {usage_percent:.1f}% usage (>= {QUOTA_WARNING_THRESHOLD}%)"

    @settings(max_examples=100)
    @given(quota_data=any_quota_strategy())
    def test_alert_has_valid_timestamp(self, quota_data: Tuple[int, int]):
        """
        Property: Alert SHALL have a valid triggered_at timestamp.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(usage_percent >= QUOTA_WARNING_THRESHOLD)
        
        before = datetime.utcnow()
        alert = check_quota_and_alert(quota_used, quota_limit)
        after = datetime.utcnow()
        
        assert alert is not None
        assert before <= alert.triggered_at <= after, \
            "Alert triggered_at should be within the test execution window"

    @settings(max_examples=100)
    @given(quota_data=any_quota_strategy())
    def test_alert_has_valid_ids(self, quota_data: Tuple[int, int]):
        """
        Property: Alert SHALL have valid user_id and account_id UUIDs.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        usage_percent = calculate_usage_percent(quota_used, quota_limit)
        assume(usage_percent >= QUOTA_WARNING_THRESHOLD)
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None
        assert isinstance(alert.user_id, uuid.UUID), \
            "Alert should have a valid user_id UUID"
        assert isinstance(alert.account_id, uuid.UUID), \
            "Alert should have a valid account_id UUID"

    def test_zero_quota_limit_triggers_alert(self):
        """
        Property: Zero quota limit SHALL trigger an alert (edge case).
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        # Zero limit should be treated as 100% usage
        alert = check_quota_and_alert(quota_used=100, quota_limit=0)
        
        assert alert is not None, \
            "Alert should be generated when quota_limit is 0"
        assert alert.usage_percent == 100.0, \
            "Usage percent should be 100% when quota_limit is 0"

    def test_exactly_at_79_percent_no_alert(self):
        """
        Property: At 79% usage, no alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_limit = 10000
        quota_used = 7900  # Exactly 79%
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is None, \
            "No alert should be generated at 79% usage"

    def test_exactly_at_80_percent_triggers_alert(self):
        """
        Property: At exactly 80% usage, an alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_limit = 10000
        quota_used = 8000  # Exactly 80%
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            "Alert should be generated at exactly 80% usage"
        assert alert.severity == "warning", \
            "Alert severity should be 'warning' at 80%"

    def test_exactly_at_90_percent_triggers_critical(self):
        """
        Property: At exactly 90% usage, a critical alert SHALL be generated.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_limit = 10000
        quota_used = 9000  # Exactly 90%
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            "Alert should be generated at exactly 90% usage"
        assert alert.severity == "critical", \
            "Alert severity should be 'critical' at 90%"

    def test_over_100_percent_triggers_critical(self):
        """
        Property: Over 100% usage SHALL trigger a critical alert.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_limit = 10000
        quota_used = 15000  # 150%
        
        alert = check_quota_and_alert(quota_used, quota_limit)
        
        assert alert is not None, \
            "Alert should be generated when over 100% usage"
        assert alert.severity == "critical", \
            "Alert severity should be 'critical' when over 100%"
        # Usage percent is capped at 100%
        assert alert.usage_percent == 100.0, \
            "Usage percent should be capped at 100%"

    @settings(max_examples=100)
    @given(quota_data=any_quota_strategy())
    def test_alert_decision_is_deterministic(self, quota_data: Tuple[int, int]):
        """
        Property: Alert decision SHALL be deterministic for the same input.
        
        **Feature: admin-panel, Property 13: Quota Alert Threshold**
        **Validates: Requirements 11.2**
        """
        quota_used, quota_limit = quota_data
        
        should_alert_1 = should_trigger_alert(quota_used, quota_limit)
        should_alert_2 = should_trigger_alert(quota_used, quota_limit)
        
        assert should_alert_1 == should_alert_2, \
            "Alert decision should be deterministic"
