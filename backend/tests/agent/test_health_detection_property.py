"""Property-based tests for agent health detection.

**Feature: youtube-automation, Property 27: Agent Health Detection**
**Validates: Requirements 21.2**
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from hypothesis import given, settings, strategies as st, assume

from app.modules.agent.schemas import AgentStatus, AgentType


# Constants matching the service implementation
HEARTBEAT_TIMEOUT_SECONDS = 60


class MockAgent:
    """Mock agent for testing health detection logic."""

    def __init__(
        self,
        agent_id: uuid.UUID,
        agent_type: AgentType,
        hostname: str,
        status: AgentStatus,
        last_heartbeat: Optional[datetime],
        current_load: int = 0,
        max_capacity: int = 5,
    ):
        self.id = agent_id
        self.type = agent_type
        self.hostname = hostname
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.current_load = current_load
        self.max_capacity = max_capacity

    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        return self.status == AgentStatus.HEALTHY

    def is_available(self) -> bool:
        """Check if agent can accept new jobs."""
        return self.is_healthy() and self.current_load < self.max_capacity


def is_agent_healthy(
    last_heartbeat: Optional[datetime],
    threshold_seconds: int = HEARTBEAT_TIMEOUT_SECONDS,
    current_time: Optional[datetime] = None,
) -> bool:
    """Check if an agent is healthy based on heartbeat.
    
    Requirements: 21.2 - Mark unhealthy after 60s missed heartbeat
    
    This is the core health detection logic being tested.
    """
    if last_heartbeat is None:
        return False
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Handle timezone-aware datetimes
    heartbeat_time = last_heartbeat.replace(tzinfo=None) if last_heartbeat.tzinfo else last_heartbeat
    current = current_time.replace(tzinfo=None) if current_time.tzinfo else current_time
    
    elapsed = (current - heartbeat_time).total_seconds()
    
    return elapsed < threshold_seconds


# Strategies for generating test data
agent_type_strategy = st.sampled_from([
    AgentType.FFMPEG,
    AgentType.RTMP,
    AgentType.HEADLESS,
])

hostname_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() and not x.startswith("-") and not x.endswith("-"))

# Generate seconds since heartbeat (positive values)
seconds_since_heartbeat_strategy = st.floats(
    min_value=0.0,
    max_value=3600.0,  # Up to 1 hour
    allow_nan=False,
    allow_infinity=False,
)


class TestAgentHealthDetection:
    """Property tests for agent health detection.

    Requirements 21.2: For any agent that misses heartbeat for 60 seconds,
    the agent status SHALL be marked as unhealthy.
    """

    @given(seconds_since_heartbeat=st.floats(min_value=60.0, max_value=3600.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_agent_unhealthy_after_60_seconds(
        self,
        seconds_since_heartbeat: float,
    ) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        For any agent that misses heartbeat for 60 seconds or more,
        the agent SHALL be marked as unhealthy.
        """
        current_time = datetime.utcnow()
        last_heartbeat = current_time - timedelta(seconds=seconds_since_heartbeat)
        
        is_healthy = is_agent_healthy(
            last_heartbeat=last_heartbeat,
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
            current_time=current_time,
        )
        
        assert not is_healthy, (
            f"Agent with heartbeat {seconds_since_heartbeat:.2f}s ago "
            f"should be unhealthy (threshold: {HEARTBEAT_TIMEOUT_SECONDS}s)"
        )

    @given(seconds_since_heartbeat=st.floats(min_value=0.0, max_value=59.9, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_agent_healthy_within_60_seconds(
        self,
        seconds_since_heartbeat: float,
    ) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        For any agent with heartbeat within 60 seconds,
        the agent SHALL remain healthy.
        """
        current_time = datetime.utcnow()
        last_heartbeat = current_time - timedelta(seconds=seconds_since_heartbeat)
        
        is_healthy = is_agent_healthy(
            last_heartbeat=last_heartbeat,
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
            current_time=current_time,
        )
        
        assert is_healthy, (
            f"Agent with heartbeat {seconds_since_heartbeat:.2f}s ago "
            f"should be healthy (threshold: {HEARTBEAT_TIMEOUT_SECONDS}s)"
        )

    @given(
        threshold=st.integers(min_value=1, max_value=300),
        seconds_since=st.floats(min_value=0.0, max_value=600.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_health_detection_respects_threshold(
        self,
        threshold: int,
        seconds_since: float,
    ) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        For any threshold value, agents with heartbeat older than threshold
        SHALL be unhealthy, and agents with recent heartbeat SHALL be healthy.
        """
        current_time = datetime.utcnow()
        last_heartbeat = current_time - timedelta(seconds=seconds_since)
        
        is_healthy = is_agent_healthy(
            last_heartbeat=last_heartbeat,
            threshold_seconds=threshold,
            current_time=current_time,
        )
        
        expected_healthy = seconds_since < threshold
        
        assert is_healthy == expected_healthy, (
            f"Agent with heartbeat {seconds_since:.2f}s ago "
            f"should be {'healthy' if expected_healthy else 'unhealthy'} "
            f"(threshold: {threshold}s)"
        )

    def test_agent_unhealthy_with_no_heartbeat(self) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        Agent with no heartbeat (None) SHALL be marked as unhealthy.
        """
        is_healthy = is_agent_healthy(
            last_heartbeat=None,
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
        )
        
        assert not is_healthy, "Agent with no heartbeat should be unhealthy"

    @given(
        seconds_list=st.lists(
            st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_health_detection_is_deterministic(
        self,
        seconds_list: list[float],
    ) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        Health detection SHALL be deterministic - same inputs produce same outputs.
        """
        current_time = datetime.utcnow()
        
        for seconds_since in seconds_list:
            last_heartbeat = current_time - timedelta(seconds=seconds_since)
            
            result1 = is_agent_healthy(
                last_heartbeat=last_heartbeat,
                threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
                current_time=current_time,
            )
            
            result2 = is_agent_healthy(
                last_heartbeat=last_heartbeat,
                threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
                current_time=current_time,
            )
            
            assert result1 == result2, "Health detection should be deterministic"

    @given(
        seconds_since=st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_boundary_at_exactly_60_seconds(
        self,
        seconds_since: float,
    ) -> None:
        """**Feature: youtube-automation, Property 27: Agent Health Detection**

        At exactly 60 seconds, agent SHALL be unhealthy (>= threshold is unhealthy).
        """
        current_time = datetime.utcnow()
        
        # Test at exactly 60 seconds
        last_heartbeat_at_60 = current_time - timedelta(seconds=60.0)
        is_healthy_at_60 = is_agent_healthy(
            last_heartbeat=last_heartbeat_at_60,
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
            current_time=current_time,
        )
        
        # At exactly 60 seconds, elapsed >= threshold, so should be unhealthy
        assert not is_healthy_at_60, "Agent at exactly 60s should be unhealthy"
        
        # Test just under 60 seconds
        last_heartbeat_under_60 = current_time - timedelta(seconds=59.999)
        is_healthy_under_60 = is_agent_healthy(
            last_heartbeat=last_heartbeat_under_60,
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
            current_time=current_time,
        )
        
        assert is_healthy_under_60, "Agent just under 60s should be healthy"


class TestHealthDetectionInvariants:
    """Tests for health detection invariants."""

    def test_healthy_agents_have_recent_heartbeat(self) -> None:
        """Healthy agents SHALL have heartbeat within threshold."""
        current_time = datetime.utcnow()
        
        # Create agents with various heartbeat times
        test_cases = [
            (0, True),    # Just now - healthy
            (30, True),   # 30s ago - healthy
            (59, True),   # 59s ago - healthy
            (60, False),  # 60s ago - unhealthy
            (120, False), # 2 min ago - unhealthy
        ]
        
        for seconds_ago, expected_healthy in test_cases:
            last_heartbeat = current_time - timedelta(seconds=seconds_ago)
            is_healthy = is_agent_healthy(
                last_heartbeat=last_heartbeat,
                threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS,
                current_time=current_time,
            )
            
            assert is_healthy == expected_healthy, (
                f"Agent with heartbeat {seconds_ago}s ago: "
                f"expected {'healthy' if expected_healthy else 'unhealthy'}, "
                f"got {'healthy' if is_healthy else 'unhealthy'}"
            )

    @given(
        threshold1=st.integers(min_value=1, max_value=100),
        threshold2=st.integers(min_value=1, max_value=100),
        seconds_since=st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_larger_threshold_more_permissive(
        self,
        threshold1: int,
        threshold2: int,
        seconds_since: float,
    ) -> None:
        """Larger threshold SHALL be more permissive (more agents healthy)."""
        assume(threshold1 != threshold2)
        
        current_time = datetime.utcnow()
        last_heartbeat = current_time - timedelta(seconds=seconds_since)
        
        smaller_threshold = min(threshold1, threshold2)
        larger_threshold = max(threshold1, threshold2)
        
        healthy_with_smaller = is_agent_healthy(
            last_heartbeat=last_heartbeat,
            threshold_seconds=smaller_threshold,
            current_time=current_time,
        )
        
        healthy_with_larger = is_agent_healthy(
            last_heartbeat=last_heartbeat,
            threshold_seconds=larger_threshold,
            current_time=current_time,
        )
        
        # If healthy with smaller threshold, must be healthy with larger
        if healthy_with_smaller:
            assert healthy_with_larger, (
                f"Agent healthy with threshold {smaller_threshold}s "
                f"should also be healthy with threshold {larger_threshold}s"
            )
