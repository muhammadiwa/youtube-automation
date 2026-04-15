"""Property-based tests for Resource Limit Warnings.

**Feature: admin-panel, Property 14: Resource Limit Warnings**
**Validates: Requirements 16.2**

Property 14: Resource Limit Warnings
*For any* user resource usage check, warnings SHALL be sent at 75% and 90% of plan limits.
"""

import uuid
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Constants ====================

WARNING_THRESHOLD_75 = 75  # 75%
WARNING_THRESHOLD_90 = 90  # 90%


# ==================== Data Classes ====================

@dataclass
class ResourceUsage:
    """Resource usage information for testing."""
    user_id: uuid.UUID
    resource_type: str
    current_usage: float
    limit: float
    percentage: float
    warning_level: Optional[str]  # "warning_75", "warning_90", or None


@dataclass
class ResourceLimitWarning:
    """Resource limit warning for testing."""
    user_id: uuid.UUID
    resource_type: str
    current_usage: float
    limit: float
    percentage: float
    threshold: int  # 75 or 90
    message: str


@dataclass
class ResourceLimitCheckResult:
    """Result of checking resource limits."""
    user_id: uuid.UUID
    warnings: List[ResourceLimitWarning]
    resources: List[ResourceUsage]


# ==================== Resource Limit Logic ====================

def check_resource_limits(
    user_id: uuid.UUID,
    resource_usages: List[dict]
) -> ResourceLimitCheckResult:
    """Check resource limits and generate warnings.
    
    Requirements: 16.2 - Send warning notification at 75% and 90% thresholds
    
    Property 14: Resource Limit Warnings
    - For any user resource usage check, warnings SHALL be sent at 75% and 90% of plan limits.
    
    Args:
        user_id: User identifier
        resource_usages: List of resource usage dicts with keys:
            - resource_type: Type of resource (storage, bandwidth, etc.)
            - current_usage: Current usage amount
            - limit: Plan limit for the resource
            
    Returns:
        ResourceLimitCheckResult with warnings and resource statuses
    """
    warnings = []
    resources = []
    
    for usage in resource_usages:
        resource_type = usage.get("resource_type", "unknown")
        current_usage = float(usage.get("current_usage", 0))
        limit = float(usage.get("limit", 1))
        
        # Avoid division by zero
        if limit <= 0:
            percentage = 0.0
        else:
            percentage = (current_usage / limit) * 100
        
        # Determine warning level
        warning_level = None
        if percentage >= WARNING_THRESHOLD_90:
            warning_level = "warning_90"
            warnings.append(ResourceLimitWarning(
                user_id=user_id,
                resource_type=resource_type,
                current_usage=current_usage,
                limit=limit,
                percentage=percentage,
                threshold=90,
                message=f"Critical: You've used {percentage:.1f}% of your {resource_type} limit. "
                        f"Consider upgrading your plan to avoid service interruption."
            ))
        elif percentage >= WARNING_THRESHOLD_75:
            warning_level = "warning_75"
            warnings.append(ResourceLimitWarning(
                user_id=user_id,
                resource_type=resource_type,
                current_usage=current_usage,
                limit=limit,
                percentage=percentage,
                threshold=75,
                message=f"Warning: You've used {percentage:.1f}% of your {resource_type} limit. "
                        f"Consider upgrading your plan."
            ))
        
        resources.append(ResourceUsage(
            user_id=user_id,
            resource_type=resource_type,
            current_usage=current_usage,
            limit=limit,
            percentage=percentage,
            warning_level=warning_level
        ))
    
    return ResourceLimitCheckResult(
        user_id=user_id,
        warnings=warnings,
        resources=resources
    )


def calculate_usage_percentage(current_usage: float, limit: float) -> float:
    """Calculate usage percentage.
    
    Args:
        current_usage: Current usage amount
        limit: Plan limit
        
    Returns:
        Usage percentage (0-100+)
    """
    if limit <= 0:
        return 0.0
    return (current_usage / limit) * 100


def should_warn_at_75(percentage: float) -> bool:
    """Check if 75% warning should be triggered.
    
    Property 14: Warnings at 75% threshold
    """
    return WARNING_THRESHOLD_75 <= percentage < WARNING_THRESHOLD_90


def should_warn_at_90(percentage: float) -> bool:
    """Check if 90% warning should be triggered.
    
    Property 14: Warnings at 90% threshold
    """
    return percentage >= WARNING_THRESHOLD_90


# ==================== Strategies ====================

# Strategy for resource usage below 75% threshold
@st.composite
def usage_below_75_strategy(draw):
    """Generate resource usage below 75% threshold."""
    limit = draw(st.floats(min_value=10.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    # Calculate max usage to stay below 75%
    max_usage = limit * WARNING_THRESHOLD_75 / 100 - 0.01
    current_usage = draw(st.floats(min_value=0.0, max_value=max(0.0, max_usage), allow_nan=False, allow_infinity=False))
    resource_type = draw(st.sampled_from(["storage", "bandwidth", "videos", "streams", "ai_generations"]))
    return {
        "resource_type": resource_type,
        "current_usage": current_usage,
        "limit": limit
    }


# Strategy for resource usage between 75% and 90%
@st.composite
def usage_between_75_and_90_strategy(draw):
    """Generate resource usage between 75% and 90% threshold."""
    limit = draw(st.floats(min_value=10.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    # Calculate usage to be between 75% and 90%
    min_usage = limit * WARNING_THRESHOLD_75 / 100
    max_usage = limit * WARNING_THRESHOLD_90 / 100 - 0.01
    current_usage = draw(st.floats(min_value=min_usage, max_value=max(min_usage, max_usage), allow_nan=False, allow_infinity=False))
    resource_type = draw(st.sampled_from(["storage", "bandwidth", "videos", "streams", "ai_generations"]))
    return {
        "resource_type": resource_type,
        "current_usage": current_usage,
        "limit": limit
    }


# Strategy for resource usage at or above 90%
@st.composite
def usage_at_or_above_90_strategy(draw):
    """Generate resource usage at or above 90% threshold."""
    limit = draw(st.floats(min_value=10.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    # Calculate usage to be at or above 90%
    min_usage = limit * WARNING_THRESHOLD_90 / 100
    max_usage = limit * 1.5  # Allow up to 150%
    current_usage = draw(st.floats(min_value=min_usage, max_value=max_usage, allow_nan=False, allow_infinity=False))
    resource_type = draw(st.sampled_from(["storage", "bandwidth", "videos", "streams", "ai_generations"]))
    return {
        "resource_type": resource_type,
        "current_usage": current_usage,
        "limit": limit
    }


# Strategy for any valid resource usage
@st.composite
def any_resource_usage_strategy(draw):
    """Generate any valid resource usage."""
    limit = draw(st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
    current_usage = draw(st.floats(min_value=0.0, max_value=limit * 2, allow_nan=False, allow_infinity=False))
    resource_type = draw(st.sampled_from(["storage", "bandwidth", "videos", "streams", "ai_generations"]))
    return {
        "resource_type": resource_type,
        "current_usage": current_usage,
        "limit": limit
    }


# Strategy for multiple resource usages
@st.composite
def multiple_resources_strategy(draw):
    """Generate multiple resource usages."""
    num_resources = draw(st.integers(min_value=1, max_value=5))
    resources = []
    resource_types = ["storage", "bandwidth", "videos", "streams", "ai_generations"]
    
    for i in range(num_resources):
        limit = draw(st.floats(min_value=10.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
        current_usage = draw(st.floats(min_value=0.0, max_value=limit * 1.5, allow_nan=False, allow_infinity=False))
        resources.append({
            "resource_type": resource_types[i % len(resource_types)],
            "current_usage": current_usage,
            "limit": limit
        })
    
    return resources


# ==================== Property Tests ====================

class TestResourceLimitWarnings:
    """Property tests for Resource Limit Warnings.
    
    **Feature: admin-panel, Property 14: Resource Limit Warnings**
    **Validates: Requirements 16.2**
    """

    @settings(max_examples=100)
    @given(resource=usage_below_75_strategy())
    def test_no_warning_below_75_percent(self, resource: dict):
        """
        Property: When usage is below 75%, no warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(percentage < WARNING_THRESHOLD_75)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 0, \
            f"No warning should be generated when usage ({percentage:.1f}%) is below {WARNING_THRESHOLD_75}%"
        assert result.resources[0].warning_level is None, \
            "Warning level should be None when below 75%"

    @settings(max_examples=100)
    @given(resource=usage_between_75_and_90_strategy())
    def test_warning_at_75_percent_threshold(self, resource: dict):
        """
        Property: When usage is between 75% and 90%, a 75% warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(WARNING_THRESHOLD_75 <= percentage < WARNING_THRESHOLD_90)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            f"One warning should be generated when usage ({percentage:.1f}%) is between 75% and 90%"
        assert result.warnings[0].threshold == 75, \
            "Warning threshold should be 75"
        assert result.resources[0].warning_level == "warning_75", \
            "Warning level should be 'warning_75'"

    @settings(max_examples=100)
    @given(resource=usage_at_or_above_90_strategy())
    def test_warning_at_90_percent_threshold(self, resource: dict):
        """
        Property: When usage is at or above 90%, a 90% warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(percentage >= WARNING_THRESHOLD_90)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            f"One warning should be generated when usage ({percentage:.1f}%) is at or above 90%"
        assert result.warnings[0].threshold == 90, \
            "Warning threshold should be 90"
        assert result.resources[0].warning_level == "warning_90", \
            "Warning level should be 'warning_90'"

    @settings(max_examples=100)
    @given(resources=multiple_resources_strategy())
    def test_multiple_resources_generate_correct_warnings(self, resources: List[dict]):
        """
        Property: Each resource SHALL be checked independently for warnings.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        
        result = check_resource_limits(user_id, resources)
        
        # Count expected warnings
        expected_warnings = 0
        for resource in resources:
            percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
            if percentage >= WARNING_THRESHOLD_75:
                expected_warnings += 1
        
        assert len(result.warnings) == expected_warnings, \
            f"Expected {expected_warnings} warnings, got {len(result.warnings)}"
        assert len(result.resources) == len(resources), \
            f"Expected {len(resources)} resources, got {len(result.resources)}"

    @settings(max_examples=100)
    @given(resource=any_resource_usage_strategy())
    def test_warning_contains_correct_user_id(self, resource: dict):
        """
        Property: Warning SHALL contain the correct user_id.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(percentage >= WARNING_THRESHOLD_75)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) > 0
        assert result.warnings[0].user_id == user_id, \
            "Warning should contain the correct user_id"
        assert result.user_id == user_id, \
            "Result should contain the correct user_id"

    @settings(max_examples=100)
    @given(resource=any_resource_usage_strategy())
    def test_warning_contains_correct_resource_info(self, resource: dict):
        """
        Property: Warning SHALL contain correct resource_type, current_usage, and limit.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(percentage >= WARNING_THRESHOLD_75)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) > 0
        warning = result.warnings[0]
        assert warning.resource_type == resource["resource_type"], \
            "Warning should contain correct resource_type"
        assert warning.current_usage == resource["current_usage"], \
            "Warning should contain correct current_usage"
        assert warning.limit == resource["limit"], \
            "Warning should contain correct limit"

    @settings(max_examples=100)
    @given(resource=any_resource_usage_strategy())
    def test_percentage_calculation_accuracy(self, resource: dict):
        """
        Property: Percentage SHALL be calculated as (current_usage / limit) * 100.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        
        result = check_resource_limits(user_id, [resource])
        
        expected_percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        actual_percentage = result.resources[0].percentage
        
        assert abs(actual_percentage - expected_percentage) < 0.01, \
            f"Percentage ({actual_percentage}) should equal ({expected_percentage})"

    @settings(max_examples=100)
    @given(resource=any_resource_usage_strategy())
    def test_warning_message_contains_percentage(self, resource: dict):
        """
        Property: Warning message SHALL contain the usage percentage.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        percentage = calculate_usage_percentage(resource["current_usage"], resource["limit"])
        assume(percentage >= WARNING_THRESHOLD_75)
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) > 0
        warning = result.warnings[0]
        # Check that message contains percentage value
        assert f"{percentage:.1f}%" in warning.message, \
            f"Warning message should contain percentage ({percentage:.1f}%)"

    def test_exactly_at_75_percent_triggers_warning(self):
        """
        Property: At exactly 75% usage, a warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 75.0,
            "limit": 100.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            "Warning should be generated at exactly 75%"
        assert result.warnings[0].threshold == 75, \
            "Warning threshold should be 75"

    def test_exactly_at_90_percent_triggers_90_warning(self):
        """
        Property: At exactly 90% usage, a 90% warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 90.0,
            "limit": 100.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            "Warning should be generated at exactly 90%"
        assert result.warnings[0].threshold == 90, \
            "Warning threshold should be 90"

    def test_at_74_percent_no_warning(self):
        """
        Property: At 74% usage, no warning SHALL be generated.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 74.0,
            "limit": 100.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 0, \
            "No warning should be generated at 74%"

    def test_at_89_percent_triggers_75_warning(self):
        """
        Property: At 89% usage, a 75% warning SHALL be generated (not 90%).
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 89.0,
            "limit": 100.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            "Warning should be generated at 89%"
        assert result.warnings[0].threshold == 75, \
            "Warning threshold should be 75 (not 90)"

    def test_over_100_percent_triggers_90_warning(self):
        """
        Property: Over 100% usage SHALL trigger a 90% warning.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 150.0,
            "limit": 100.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 1, \
            "Warning should be generated when over 100%"
        assert result.warnings[0].threshold == 90, \
            "Warning threshold should be 90"

    def test_zero_limit_no_warning(self):
        """
        Property: Zero limit SHALL result in 0% usage (no warning).
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        resource = {
            "resource_type": "storage",
            "current_usage": 50.0,
            "limit": 0.0
        }
        
        result = check_resource_limits(user_id, [resource])
        
        assert len(result.warnings) == 0, \
            "No warning should be generated when limit is 0"
        assert result.resources[0].percentage == 0.0, \
            "Percentage should be 0 when limit is 0"

    @settings(max_examples=100)
    @given(resource=any_resource_usage_strategy())
    def test_warning_decision_is_deterministic(self, resource: dict):
        """
        Property: Warning decision SHALL be deterministic for the same input.
        
        **Feature: admin-panel, Property 14: Resource Limit Warnings**
        **Validates: Requirements 16.2**
        """
        user_id = uuid.uuid4()
        
        result1 = check_resource_limits(user_id, [resource])
        result2 = check_resource_limits(user_id, [resource])
        
        assert len(result1.warnings) == len(result2.warnings), \
            "Warning count should be deterministic"
        assert result1.resources[0].warning_level == result2.resources[0].warning_level, \
            "Warning level should be deterministic"
