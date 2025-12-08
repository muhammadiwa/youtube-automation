"""API router for Agent service.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.agent.service import AgentService
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
    HealthCheckSummary,
)

router = APIRouter(prefix="/agents", tags=["agents"])


async def get_agent_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> AgentService:
    """Dependency to get AgentService instance."""
    return AgentService(session)


# ==================== Agent Registration (21.1) ====================

@router.post(
    "/register",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
    description="Register a new agent or update existing one with API key authentication.",
)
async def register_agent(
    request: AgentRegistrationRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentRegistrationResponse:
    """Register a new agent.
    
    Requirements: 21.1 - Agent registration with API key authentication
    """
    return await service.register_agent(request)


# ==================== Heartbeat (21.1) ====================

@router.post(
    "/heartbeat",
    response_model=AgentHeartbeatResponse,
    summary="Send agent heartbeat",
    description="Send heartbeat to indicate agent is alive and report current load.",
)
async def send_heartbeat(
    request: AgentHeartbeatRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentHeartbeatResponse:
    """Process agent heartbeat.
    
    Requirements: 21.1 - Heartbeat tracking
    """
    return await service.process_heartbeat(request)


# ==================== Health Check (21.2) ====================

@router.post(
    "/health-check",
    response_model=HealthCheckSummary,
    summary="Run health check on all agents",
    description="Check health of all agents and mark unhealthy ones. Reassigns jobs from unhealthy agents.",
)
async def run_health_check(
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> HealthCheckSummary:
    """Run health check on all agents.
    
    Requirements: 21.2 - Mark unhealthy after 60s missed heartbeat, reassign pending jobs
    """
    return await service.check_agent_health()


# ==================== Agent Queries ====================

@router.get(
    "",
    response_model=AgentListResponse,
    summary="List all agents",
    description="Get list of all registered agents with their status.",
)
async def list_agents(
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentListResponse:
    """List all agents."""
    return await service.list_agents()


@router.get(
    "/{agent_id}",
    response_model=AgentInfo,
    summary="Get agent details",
    description="Get detailed information about a specific agent.",
)
async def get_agent(
    agent_id: uuid.UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentInfo:
    """Get agent information."""
    agent = await service.get_agent_info(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent


# ==================== Job Management (21.3, 21.4) ====================

@router.post(
    "/jobs",
    response_model=JobDispatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and dispatch a job",
    description="Create a new job and dispatch it to the best available agent.",
)
async def create_job(
    request: JobCreateRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> JobDispatchResponse:
    """Create and dispatch a job.
    
    Requirements: 21.3 - Select lowest load healthy agent
    """
    result = await service.create_and_dispatch_job(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No available agents to process job",
        )
    return result


@router.post(
    "/jobs/{job_id}/dispatch",
    response_model=JobDispatchResponse,
    summary="Dispatch an existing job",
    description="Dispatch an existing queued job to an available agent.",
)
async def dispatch_job(
    job_id: uuid.UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> JobDispatchResponse:
    """Dispatch a job to an agent.
    
    Requirements: 21.3
    """
    result = await service.dispatch_job(job_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No available agents or job not found/not queued",
        )
    return result


@router.post(
    "/jobs/complete",
    response_model=JobCompletionResponse,
    summary="Mark job as completed",
    description="Mark a job as completed and trigger next workflow step if applicable.",
)
async def complete_job(
    request: JobCompletionRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> JobCompletionResponse:
    """Complete a job.
    
    Requirements: 21.4 - Update status on completion, trigger next workflow step
    """
    result = await service.complete_job(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return result


@router.get(
    "/jobs/{job_id}",
    response_model=JobInfo,
    summary="Get job details",
    description="Get detailed information about a specific job.",
)
async def get_job(
    job_id: uuid.UUID,
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> JobInfo:
    """Get job information."""
    job = await service.get_job_info(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job
