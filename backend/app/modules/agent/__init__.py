"""Agent module for distributed worker management.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

from app.modules.agent.models import Agent, AgentJob, AgentType, AgentStatus, JobStatus
from app.modules.agent.schemas import (
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentInfo,
    AgentListResponse,
    JobCreateRequest,
    JobInfo,
    JobDispatchResponse,
    JobCompletionRequest,
    JobCompletionResponse,
    HealthCheckResult,
    HealthCheckSummary,
)
from app.modules.agent.repository import AgentRepository, AgentJobRepository
from app.modules.agent.router import router as agent_router
from app.modules.agent.service import AgentService

__all__ = [
    # Models
    "Agent",
    "AgentJob",
    "AgentType",
    "AgentStatus",
    "JobStatus",
    # Schemas
    "AgentRegistrationRequest",
    "AgentRegistrationResponse",
    "AgentHeartbeatRequest",
    "AgentHeartbeatResponse",
    "AgentInfo",
    "AgentListResponse",
    "JobCreateRequest",
    "JobInfo",
    "JobDispatchResponse",
    "JobCompletionRequest",
    "JobCompletionResponse",
    "HealthCheckResult",
    "HealthCheckSummary",
    # Repositories
    "AgentRepository",
    "AgentJobRepository",
    # Service
    "AgentService",
    # Router
    "agent_router",
]
