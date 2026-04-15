"""Property-based tests for System Health Aggregation.

**Feature: admin-panel, Property 12: System Health Aggregation**
**Validates: Requirements 7.1, 7.2**

Property 12: System Health Aggregation
*For any* system health check, overall_status SHALL be 'critical' if any 
component is 'down', 'degraded' if any component is 'degraded', otherwise 'healthy'.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== Enums and Constants ====================

class AdminHealthStatus:
    """Health status values for admin system monitoring.
    
    Property 12: System Health Aggregation
    - 'critical' if any component is 'down'
    - 'degraded' if any component is 'degraded'
    - 'healthy' otherwise
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class ComponentStatus:
    """Individual component status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


# ==================== Data Classes ====================

@dataclass
class AdminComponentHealth:
    """Health status of a system component for testing."""
    name: str
    status: str
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    last_check: datetime = None
    
    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.utcnow()


# ==================== Health Aggregation Logic ====================

def aggregate_health_status(components: List[AdminComponentHealth]) -> str:
    """
    Aggregate component statuses into overall system status.
    
    Property 12: System Health Aggregation
    - 'critical' if any component is 'down'
    - 'degraded' if any component is 'degraded'
    - 'healthy' otherwise
    
    Args:
        components: List of component health statuses
        
    Returns:
        Aggregated health status string
    """
    has_down = any(c.status == ComponentStatus.DOWN for c in components)
    has_degraded = any(c.status == ComponentStatus.DEGRADED for c in components)
    
    if has_down:
        return AdminHealthStatus.CRITICAL
    elif has_degraded:
        return AdminHealthStatus.DEGRADED
    return AdminHealthStatus.HEALTHY


# ==================== Strategies ====================

component_status_strategy = st.sampled_from([
    ComponentStatus.HEALTHY,
    ComponentStatus.DEGRADED,
    ComponentStatus.DOWN,
])

component_name_strategy = st.sampled_from([
    "api", "database", "redis", "workers", "agents"
])


@st.composite
def component_health_strategy(draw):
    """Generate a random component health status."""
    status = draw(component_status_strategy)
    name = draw(component_name_strategy)
    
    message = None
    if status == ComponentStatus.DOWN:
        message = f"{name} connection failed"
    elif status == ComponentStatus.DEGRADED:
        message = f"{name} latency is high"
    else:
        message = f"{name} is healthy"
    
    return AdminComponentHealth(
        name=name,
        status=status,
        message=message,
        latency_ms=draw(st.floats(min_value=0.1, max_value=5000.0)),
        last_check=datetime.utcnow(),
    )


@st.composite
def components_list_strategy(draw, min_size=1, max_size=10):
    """Generate a list of random component health statuses."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(component_health_strategy()) for _ in range(size)]


@st.composite
def all_healthy_components_strategy(draw, min_size=1, max_size=10):
    """Generate a list of all healthy components."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [
        AdminComponentHealth(
            name=f"component_{i}",
            status=ComponentStatus.HEALTHY,
            message="Component is healthy",
            latency_ms=draw(st.floats(min_value=0.1, max_value=100.0)),
        )
        for i in range(size)
    ]


@st.composite
def components_with_at_least_one_down_strategy(draw, min_size=1, max_size=10):
    """Generate components with at least one DOWN component."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    components = [draw(component_health_strategy()) for _ in range(size)]
    
    # Ensure at least one is DOWN
    down_component = AdminComponentHealth(
        name="critical_component",
        status=ComponentStatus.DOWN,
        message="Component is down",
        latency_ms=None,
    )
    components.append(down_component)
    
    return components


@st.composite
def components_with_degraded_no_down_strategy(draw, min_size=1, max_size=10):
    """Generate components with at least one DEGRADED but no DOWN."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Generate only HEALTHY or DEGRADED components
    components = []
    for i in range(size):
        status = draw(st.sampled_from([ComponentStatus.HEALTHY, ComponentStatus.DEGRADED]))
        components.append(AdminComponentHealth(
            name=f"component_{i}",
            status=status,
            message=f"Component is {status}",
            latency_ms=draw(st.floats(min_value=0.1, max_value=1000.0)),
        ))
    
    # Ensure at least one is DEGRADED
    degraded_component = AdminComponentHealth(
        name="degraded_component",
        status=ComponentStatus.DEGRADED,
        message="Component is degraded",
        latency_ms=500.0,
    )
    components.append(degraded_component)
    
    return components


# ==================== Property Tests ====================

class TestSystemHealthAggregation:
    """Property tests for System Health Aggregation.
    
    **Feature: admin-panel, Property 12: System Health Aggregation**
    **Validates: Requirements 7.1, 7.2**
    """

    @settings(max_examples=100)
    @given(components=all_healthy_components_strategy(min_size=1, max_size=10))
    def test_all_healthy_returns_healthy(self, components: List[AdminComponentHealth]):
        """
        Property: When all components are healthy, overall_status SHALL be 'healthy'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.HEALTHY, \
            f"Expected 'healthy' when all components are healthy, got '{overall_status}'"

    @settings(max_examples=100)
    @given(components=components_with_at_least_one_down_strategy(min_size=1, max_size=10))
    def test_any_down_returns_critical(self, components: List[AdminComponentHealth]):
        """
        Property: When any component is 'down', overall_status SHALL be 'critical'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.CRITICAL, \
            f"Expected 'critical' when any component is down, got '{overall_status}'"

    @settings(max_examples=100)
    @given(components=components_with_degraded_no_down_strategy(min_size=1, max_size=10))
    def test_degraded_without_down_returns_degraded(self, components: List[AdminComponentHealth]):
        """
        Property: When any component is 'degraded' but none are 'down', 
        overall_status SHALL be 'degraded'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        # Verify no DOWN components
        assume(not any(c.status == ComponentStatus.DOWN for c in components))
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.DEGRADED, \
            f"Expected 'degraded' when components are degraded but not down, got '{overall_status}'"

    @settings(max_examples=100)
    @given(components=components_list_strategy(min_size=1, max_size=10))
    def test_down_takes_precedence_over_degraded(self, components: List[AdminComponentHealth]):
        """
        Property: 'down' status SHALL take precedence over 'degraded' status.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        # Add both a DOWN and DEGRADED component
        components_with_both = components + [
            AdminComponentHealth(
                name="down_component",
                status=ComponentStatus.DOWN,
                message="Component is down",
            ),
            AdminComponentHealth(
                name="degraded_component",
                status=ComponentStatus.DEGRADED,
                message="Component is degraded",
            ),
        ]
        
        overall_status = aggregate_health_status(components_with_both)
        
        assert overall_status == AdminHealthStatus.CRITICAL, \
            f"Expected 'critical' when both down and degraded exist, got '{overall_status}'"

    @settings(max_examples=100)
    @given(
        healthy_count=st.integers(min_value=0, max_value=5),
        degraded_count=st.integers(min_value=0, max_value=5),
        down_count=st.integers(min_value=0, max_value=5),
    )
    def test_aggregation_logic_comprehensive(
        self, healthy_count: int, degraded_count: int, down_count: int
    ):
        """
        Property: Aggregation logic SHALL follow the priority: down > degraded > healthy.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        # Skip if no components
        assume(healthy_count + degraded_count + down_count > 0)
        
        components = []
        
        for i in range(healthy_count):
            components.append(AdminComponentHealth(
                name=f"healthy_{i}",
                status=ComponentStatus.HEALTHY,
            ))
        
        for i in range(degraded_count):
            components.append(AdminComponentHealth(
                name=f"degraded_{i}",
                status=ComponentStatus.DEGRADED,
            ))
        
        for i in range(down_count):
            components.append(AdminComponentHealth(
                name=f"down_{i}",
                status=ComponentStatus.DOWN,
            ))
        
        overall_status = aggregate_health_status(components)
        
        # Verify the expected status based on component counts
        if down_count > 0:
            expected = AdminHealthStatus.CRITICAL
        elif degraded_count > 0:
            expected = AdminHealthStatus.DEGRADED
        else:
            expected = AdminHealthStatus.HEALTHY
        
        assert overall_status == expected, \
            f"Expected '{expected}' with {down_count} down, {degraded_count} degraded, {healthy_count} healthy, got '{overall_status}'"

    @settings(max_examples=100)
    @given(components=components_list_strategy(min_size=1, max_size=10))
    def test_aggregation_is_deterministic(self, components: List[AdminComponentHealth]):
        """
        Property: Aggregation SHALL produce the same result for the same input.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        result1 = aggregate_health_status(components)
        result2 = aggregate_health_status(components)
        
        assert result1 == result2, \
            "Aggregation should be deterministic"

    @settings(max_examples=100)
    @given(components=components_list_strategy(min_size=1, max_size=10))
    def test_aggregation_result_is_valid_status(self, components: List[AdminComponentHealth]):
        """
        Property: Aggregation result SHALL be one of: 'healthy', 'degraded', 'critical'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        overall_status = aggregate_health_status(components)
        
        valid_statuses = {
            AdminHealthStatus.HEALTHY,
            AdminHealthStatus.DEGRADED,
            AdminHealthStatus.CRITICAL,
        }
        
        assert overall_status in valid_statuses, \
            f"Aggregation result '{overall_status}' is not a valid status"

    def test_empty_components_returns_healthy(self):
        """
        Property: An empty component list SHALL return 'healthy'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        overall_status = aggregate_health_status([])
        
        assert overall_status == AdminHealthStatus.HEALTHY, \
            f"Expected 'healthy' for empty components, got '{overall_status}'"

    def test_single_healthy_component(self):
        """
        Property: A single healthy component SHALL return 'healthy'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        components = [AdminComponentHealth(
            name="api",
            status=ComponentStatus.HEALTHY,
        )]
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.HEALTHY

    def test_single_degraded_component(self):
        """
        Property: A single degraded component SHALL return 'degraded'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        components = [AdminComponentHealth(
            name="database",
            status=ComponentStatus.DEGRADED,
        )]
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.DEGRADED

    def test_single_down_component(self):
        """
        Property: A single down component SHALL return 'critical'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        components = [AdminComponentHealth(
            name="redis",
            status=ComponentStatus.DOWN,
        )]
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.CRITICAL

    @settings(max_examples=100)
    @given(
        num_healthy=st.integers(min_value=1, max_value=10),
    )
    def test_multiple_healthy_components(self, num_healthy: int):
        """
        Property: Multiple healthy components SHALL return 'healthy'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        components = [
            AdminComponentHealth(
                name=f"component_{i}",
                status=ComponentStatus.HEALTHY,
            )
            for i in range(num_healthy)
        ]
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.HEALTHY

    @settings(max_examples=100)
    @given(
        num_down=st.integers(min_value=1, max_value=5),
    )
    def test_multiple_down_components(self, num_down: int):
        """
        Property: Multiple down components SHALL return 'critical'.
        
        **Feature: admin-panel, Property 12: System Health Aggregation**
        **Validates: Requirements 7.1, 7.2**
        """
        components = [
            AdminComponentHealth(
                name=f"component_{i}",
                status=ComponentStatus.DOWN,
            )
            for i in range(num_down)
        ]
        
        overall_status = aggregate_health_status(components)
        
        assert overall_status == AdminHealthStatus.CRITICAL
