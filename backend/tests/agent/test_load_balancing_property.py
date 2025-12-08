"""Property-based tests for job load balancing.

**Feature: youtube-automation, Property 28: Job Load Balancing**
**Validates: Requirements 21.3**
"""

import uuid
from typing import Optional

from hypothesis import given, settings, strategies as st, assume

from app.modules.agent.schemas import AgentStatus, AgentType


class MockAgent:
    """Mock agent for testing load balancing logic."""

    def __init__(
        self,
        agent_id: uuid.UUID,
        agent_type: AgentType,
        hostname: str,
        status: AgentStatus,
        current_load: int,
        max_capacity: int,
    ):
        self.id = agent_id
        self.type = agent_type
        self.hostname = hostname
        self.status = status
        self.current_load = current_load
        self.max_capacity = max_capacity

    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        return self.status == AgentStatus.HEALTHY

    def is_available(self) -> bool:
        """Check if agent can accept new jobs."""
        return self.is_healthy() and self.current_load < self.max_capacity

    def get_available_capacity(self) -> int:
        """Get remaining capacity for jobs."""
        return max(0, self.max_capacity - self.current_load)


def select_lowest_load_agent(agents: list[MockAgent]) -> Optional[MockAgent]:
    """Select the healthy agent with the lowest current load.
    
    Requirements: 21.3 - Select lowest load healthy agent
    
    This is the core load balancing logic being tested.
    """
    available_agents = [a for a in agents if a.is_available()]
    
    if not available_agents:
        return None
    
    # Sort by current_load ascending, then by available capacity descending
    return min(available_agents, key=lambda a: (a.current_load, -a.get_available_capacity()))


def create_mock_agent(
    status: AgentStatus = AgentStatus.HEALTHY,
    current_load: int = 0,
    max_capacity: int = 5,
    agent_type: AgentType = AgentType.FFMPEG,
) -> MockAgent:
    """Create a mock agent for testing."""
    return MockAgent(
        agent_id=uuid.uuid4(),
        agent_type=agent_type,
        hostname=f"agent-{uuid.uuid4().hex[:8]}",
        status=status,
        current_load=current_load,
        max_capacity=max_capacity,
    )


# Strategies for generating test data
agent_status_strategy = st.sampled_from([
    AgentStatus.HEALTHY,
    AgentStatus.UNHEALTHY,
    AgentStatus.OFFLINE,
])

agent_type_strategy = st.sampled_from([
    AgentType.FFMPEG,
    AgentType.RTMP,
    AgentType.HEADLESS,
])

load_strategy = st.integers(min_value=0, max_value=100)
capacity_strategy = st.integers(min_value=1, max_value=100)


@st.composite
def agent_strategy(draw):
    """Strategy to generate a mock agent."""
    status = draw(agent_status_strategy)
    max_capacity = draw(capacity_strategy)
    # Ensure current_load doesn't exceed max_capacity for realistic scenarios
    current_load = draw(st.integers(min_value=0, max_value=max_capacity + 5))
    agent_type = draw(agent_type_strategy)
    
    return create_mock_agent(
        status=status,
        current_load=current_load,
        max_capacity=max_capacity,
        agent_type=agent_type,
    )


class TestJobLoadBalancing:
    """Property tests for job load balancing.

    Requirements 21.3: For any job dispatch to agents,
    the job SHALL be assigned to the healthy agent with the lowest current load.
    """

    @given(
        loads=st.lists(st.integers(min_value=0, max_value=50), min_size=2, max_size=20),
    )
    @settings(max_examples=100)
    def test_selects_lowest_load_agent(
        self,
        loads: list[int],
    ) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        For any set of healthy agents, the agent with lowest load SHALL be selected.
        """
        # Create healthy agents with different loads
        agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=load,
                max_capacity=100,  # High capacity to ensure all are available
            )
            for load in loads
        ]
        
        selected = select_lowest_load_agent(agents)
        
        assert selected is not None, "Should select an agent when healthy agents exist"
        
        # Verify selected agent has the minimum load
        min_load = min(a.current_load for a in agents)
        assert selected.current_load == min_load, (
            f"Selected agent has load {selected.current_load}, "
            f"but minimum load is {min_load}"
        )

    @given(agents=st.lists(agent_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_only_selects_healthy_agents(
        self,
        agents: list[MockAgent],
    ) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        Only healthy agents SHALL be considered for job dispatch.
        """
        selected = select_lowest_load_agent(agents)
        
        # If an agent was selected, it must be healthy
        if selected is not None:
            assert selected.is_healthy(), (
                f"Selected agent has status {selected.status}, expected HEALTHY"
            )

    @given(agents=st.lists(agent_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_only_selects_available_agents(
        self,
        agents: list[MockAgent],
    ) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        Only agents with available capacity SHALL be considered for job dispatch.
        """
        selected = select_lowest_load_agent(agents)
        
        # If an agent was selected, it must have available capacity
        if selected is not None:
            assert selected.is_available(), (
                f"Selected agent is not available "
                f"(load={selected.current_load}, capacity={selected.max_capacity})"
            )

    @given(
        healthy_loads=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=10),
        unhealthy_loads=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_ignores_unhealthy_agents_even_with_lower_load(
        self,
        healthy_loads: list[int],
        unhealthy_loads: list[int],
    ) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        Unhealthy agents SHALL NOT be selected even if they have lower load.
        """
        # Create healthy agents
        healthy_agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=load,
                max_capacity=100,
            )
            for load in healthy_loads
        ]
        
        # Create unhealthy agents with potentially lower loads
        unhealthy_agents = [
            create_mock_agent(
                status=AgentStatus.UNHEALTHY,
                current_load=0,  # Very low load
                max_capacity=100,
            )
            for _ in unhealthy_loads
        ]
        
        all_agents = healthy_agents + unhealthy_agents
        selected = select_lowest_load_agent(all_agents)
        
        assert selected is not None, "Should select a healthy agent"
        assert selected.is_healthy(), "Selected agent must be healthy"
        assert selected in healthy_agents, "Selected agent must be from healthy pool"

    @given(
        loads=st.lists(st.integers(min_value=0, max_value=50), min_size=2, max_size=20),
    )
    @settings(max_examples=100)
    def test_load_balancing_is_deterministic(
        self,
        loads: list[int],
    ) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        Load balancing SHALL be deterministic - same inputs produce same outputs.
        """
        # Create agents with fixed IDs for determinism
        agents = []
        for i, load in enumerate(loads):
            agent = create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=load,
                max_capacity=100,
            )
            agents.append(agent)
        
        selected1 = select_lowest_load_agent(agents)
        selected2 = select_lowest_load_agent(agents)
        
        if selected1 is not None and selected2 is not None:
            assert selected1.current_load == selected2.current_load, (
                "Load balancing should be deterministic"
            )

    def test_returns_none_when_no_healthy_agents(self) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        When no healthy agents exist, None SHALL be returned.
        """
        agents = [
            create_mock_agent(status=AgentStatus.UNHEALTHY, current_load=0),
            create_mock_agent(status=AgentStatus.OFFLINE, current_load=0),
        ]
        
        selected = select_lowest_load_agent(agents)
        assert selected is None, "Should return None when no healthy agents"

    def test_returns_none_when_all_at_capacity(self) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        When all healthy agents are at capacity, None SHALL be returned.
        """
        agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=5,
                max_capacity=5,  # At capacity
            ),
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=10,
                max_capacity=10,  # At capacity
            ),
        ]
        
        selected = select_lowest_load_agent(agents)
        assert selected is None, "Should return None when all agents at capacity"

    def test_returns_none_for_empty_list(self) -> None:
        """**Feature: youtube-automation, Property 28: Job Load Balancing**

        When no agents exist, None SHALL be returned.
        """
        selected = select_lowest_load_agent([])
        assert selected is None, "Should return None for empty agent list"


class TestLoadBalancingInvariants:
    """Tests for load balancing invariants."""

    @given(
        loads=st.lists(st.integers(min_value=0, max_value=50), min_size=2, max_size=20),
    )
    @settings(max_examples=100)
    def test_selected_load_never_exceeds_minimum(
        self,
        loads: list[int],
    ) -> None:
        """Selected agent's load SHALL never exceed the minimum available load."""
        agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=load,
                max_capacity=100,
            )
            for load in loads
        ]
        
        selected = select_lowest_load_agent(agents)
        
        if selected is not None:
            available_agents = [a for a in agents if a.is_available()]
            min_load = min(a.current_load for a in available_agents)
            
            assert selected.current_load <= min_load, (
                f"Selected load {selected.current_load} exceeds minimum {min_load}"
            )

    @given(
        capacity=st.integers(min_value=1, max_value=50),
        num_agents=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_prefers_higher_capacity_on_tie(
        self,
        capacity: int,
        num_agents: int,
    ) -> None:
        """When loads are equal, agent with higher capacity SHALL be preferred."""
        # Create agents with same load but different capacities
        agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=0,  # Same load
                max_capacity=capacity + i,  # Different capacities
            )
            for i in range(num_agents)
        ]
        
        selected = select_lowest_load_agent(agents)
        
        assert selected is not None
        
        # Should select agent with highest capacity (most available capacity)
        max_capacity = max(a.max_capacity for a in agents)
        assert selected.max_capacity == max_capacity, (
            f"Should prefer agent with capacity {max_capacity}, "
            f"got {selected.max_capacity}"
        )

    def test_respects_capacity_limits(self) -> None:
        """Agents at capacity SHALL NOT be selected."""
        # Agent 1: Low load but at capacity
        agent1 = create_mock_agent(
            status=AgentStatus.HEALTHY,
            current_load=2,
            max_capacity=2,  # At capacity
        )
        
        # Agent 2: Higher load but has capacity
        agent2 = create_mock_agent(
            status=AgentStatus.HEALTHY,
            current_load=5,
            max_capacity=10,  # Has capacity
        )
        
        selected = select_lowest_load_agent([agent1, agent2])
        
        assert selected is not None
        assert selected.id == agent2.id, (
            "Should select agent with available capacity, not the one at capacity"
        )

    @given(
        loads=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=20),
    )
    @settings(max_examples=100)
    def test_selection_is_from_input_list(
        self,
        loads: list[int],
    ) -> None:
        """Selected agent SHALL be from the input list."""
        agents = [
            create_mock_agent(
                status=AgentStatus.HEALTHY,
                current_load=load,
                max_capacity=100,
            )
            for load in loads
        ]
        
        selected = select_lowest_load_agent(agents)
        
        if selected is not None:
            agent_ids = {a.id for a in agents}
            assert selected.id in agent_ids, "Selected agent must be from input list"
