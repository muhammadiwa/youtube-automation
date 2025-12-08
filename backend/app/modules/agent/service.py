"""Agent service for distributed worker management.

Implements agent registration, heartbeat, health detection, job dispatch, and completion.
Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.models import AgentStatus, JobStatus
from app.modules.agent.repository import AgentRepository, AgentJobRepository
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
    JobReassignmentResult,
    HealthCheckResult,
    HealthCheckSummary,
    AgentType as SchemaAgentType,
    AgentStatus as SchemaAgentStatus,
    JobStatus as SchemaJobStatus,
)


# Health detection threshold in seconds (Requirements: 21.2)
HEARTBEAT_TIMEOUT_SECONDS = 60


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


class AgentService:
    """Service for agent management.
    
    Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agent_repo = AgentRepository(session)
        self.job_repo = AgentJobRepository(session)

    # ==================== Agent Registration (21.1) ====================

    async def register_agent(
        self, request: AgentRegistrationRequest
    ) -> AgentRegistrationResponse:
        """Register a new agent or update existing one.
        
        Requirements: 21.1 - Agent registration with API key authentication
        """
        api_key_hash = hash_api_key(request.api_key)
        
        # Check if agent already exists
        existing = await self.agent_repo.get_agent_by_api_key_hash(api_key_hash)
        
        if existing:
            # Update existing agent
            existing.hostname = request.hostname
            existing.ip_address = request.ip_address
            existing.max_capacity = request.max_capacity
            existing.metadata = request.metadata
            existing.status = AgentStatus.HEALTHY.value
            existing.last_heartbeat = datetime.utcnow()
            await self.session.flush()
            
            return AgentRegistrationResponse(
                agent_id=existing.id,
                status=SchemaAgentStatus.HEALTHY,
                message="Agent re-registered successfully",
            )
        
        # Create new agent
        agent = await self.agent_repo.create_agent(
            api_key_hash=api_key_hash,
            agent_type=request.agent_type.value,
            hostname=request.hostname,
            ip_address=request.ip_address,
            max_capacity=request.max_capacity,
            metadata=request.metadata,
        )
        
        return AgentRegistrationResponse(
            agent_id=agent.id,
            status=SchemaAgentStatus.HEALTHY,
            message="Agent registered successfully",
        )

    async def authenticate_agent(self, api_key: str) -> Optional[uuid.UUID]:
        """Authenticate agent by API key.
        
        Requirements: 21.1
        """
        api_key_hash = hash_api_key(api_key)
        agent = await self.agent_repo.get_agent_by_api_key_hash(api_key_hash)
        return agent.id if agent else None

    # ==================== Heartbeat (21.1) ====================

    async def process_heartbeat(
        self, request: AgentHeartbeatRequest
    ) -> AgentHeartbeatResponse:
        """Process agent heartbeat.
        
        Requirements: 21.1 - Heartbeat tracking
        """
        agent = await self.agent_repo.update_heartbeat(
            agent_id=request.agent_id,
            current_load=request.current_load,
            metadata=request.metadata,
        )
        
        if not agent:
            return AgentHeartbeatResponse(
                status=SchemaAgentStatus.OFFLINE,
                acknowledged=False,
                server_time=datetime.utcnow(),
            )
        
        return AgentHeartbeatResponse(
            status=SchemaAgentStatus(agent.status),
            acknowledged=True,
            server_time=datetime.utcnow(),
        )

    # ==================== Health Detection (21.2) ====================

    async def check_agent_health(self) -> HealthCheckSummary:
        """Check health of all agents and mark unhealthy ones.
        
        Requirements: 21.2 - Mark unhealthy after 60s missed heartbeat
        """
        all_agents = await self.agent_repo.get_all_agents()
        stale_agents = await self.agent_repo.get_agents_with_stale_heartbeat(
            threshold_seconds=HEARTBEAT_TIMEOUT_SECONDS
        )
        
        newly_unhealthy: list[HealthCheckResult] = []
        total_jobs_reassigned = 0
        
        for agent in stale_agents:
            # Calculate seconds since last heartbeat
            if agent.last_heartbeat:
                seconds_since = (datetime.utcnow() - agent.last_heartbeat.replace(tzinfo=None)).total_seconds()
            else:
                seconds_since = float('inf')
            
            previous_status = SchemaAgentStatus(agent.status)
            
            # Mark as unhealthy
            await self.agent_repo.update_agent_status(agent.id, AgentStatus.UNHEALTHY)
            
            # Reassign pending jobs (Requirements: 21.2)
            reassignment = await self.reassign_agent_jobs(agent.id)
            total_jobs_reassigned += reassignment.reassigned_count
            
            newly_unhealthy.append(HealthCheckResult(
                agent_id=agent.id,
                previous_status=previous_status,
                new_status=SchemaAgentStatus.UNHEALTHY,
                seconds_since_heartbeat=seconds_since,
                jobs_reassigned=reassignment.reassigned_count,
            ))
        
        healthy_count = sum(1 for a in all_agents if a.status == AgentStatus.HEALTHY.value)
        unhealthy_count = len(all_agents) - healthy_count
        
        return HealthCheckSummary(
            checked_at=datetime.utcnow(),
            total_agents=len(all_agents),
            healthy_agents=healthy_count,
            unhealthy_agents=unhealthy_count,
            newly_unhealthy=newly_unhealthy,
            total_jobs_reassigned=total_jobs_reassigned,
        )

    def is_agent_healthy(
        self, last_heartbeat: Optional[datetime], threshold_seconds: int = HEARTBEAT_TIMEOUT_SECONDS
    ) -> bool:
        """Check if an agent is healthy based on heartbeat.
        
        Requirements: 21.2 - Mark unhealthy after 60s missed heartbeat
        
        Args:
            last_heartbeat: The agent's last heartbeat timestamp
            threshold_seconds: Seconds after which agent is considered unhealthy
            
        Returns:
            True if agent is healthy, False otherwise
        """
        if last_heartbeat is None:
            return False
        
        # Handle timezone-aware datetimes
        heartbeat_time = last_heartbeat.replace(tzinfo=None) if last_heartbeat.tzinfo else last_heartbeat
        elapsed = (datetime.utcnow() - heartbeat_time).total_seconds()
        
        return elapsed < threshold_seconds

    # ==================== Job Dispatch (21.3) ====================

    async def dispatch_job(self, job_id: uuid.UUID) -> Optional[JobDispatchResponse]:
        """Dispatch a job to the best available agent.
        
        Requirements: 21.3 - Select lowest load healthy agent
        """
        job = await self.job_repo.get_job_by_id(job_id)
        if not job or job.status != JobStatus.QUEUED.value:
            return None
        
        # Get healthy agents
        healthy_agents = await self.agent_repo.get_healthy_agents()
        
        if not healthy_agents:
            return None
        
        # Select agent with lowest load (Requirements: 21.3)
        best_agent = self.select_lowest_load_agent(healthy_agents)
        
        if not best_agent or not best_agent.is_available():
            return None
        
        # Assign job to agent
        await self.job_repo.assign_job_to_agent(job_id, best_agent.id)
        await self.agent_repo.increment_agent_load(best_agent.id)
        
        return JobDispatchResponse(
            job_id=job_id,
            agent_id=best_agent.id,
            status=SchemaJobStatus.PROCESSING,
            message=f"Job dispatched to agent {best_agent.hostname}",
        )

    def select_lowest_load_agent(self, agents: list) -> Optional[object]:
        """Select the healthy agent with the lowest current load.
        
        Requirements: 21.3 - Select lowest load healthy agent
        
        Args:
            agents: List of agent objects with current_load and max_capacity attributes
            
        Returns:
            The agent with lowest load that has available capacity, or None
        """
        available_agents = [a for a in agents if a.is_available()]
        
        if not available_agents:
            return None
        
        # Sort by current_load ascending, then by available capacity descending
        return min(available_agents, key=lambda a: (a.current_load, -a.get_available_capacity()))

    async def create_and_dispatch_job(
        self, request: JobCreateRequest
    ) -> Optional[JobDispatchResponse]:
        """Create a job and dispatch it to an agent.
        
        Requirements: 21.3
        """
        job = await self.job_repo.create_job(
            job_type=request.job_type,
            payload=request.payload,
            priority=request.priority,
            max_attempts=request.max_attempts,
            workflow_id=request.workflow_id,
            next_job_id=request.next_job_id,
        )
        
        return await self.dispatch_job(job.id)

    # ==================== Job Completion (21.4) ====================

    async def complete_job(
        self, request: JobCompletionRequest
    ) -> Optional[JobCompletionResponse]:
        """Mark a job as completed and trigger next workflow step.
        
        Requirements: 21.4 - Update status on completion, trigger next workflow step
        """
        job = await self.job_repo.get_job_by_id(request.job_id)
        if not job:
            return None
        
        # Update job status
        await self.job_repo.complete_job(
            job_id=request.job_id,
            status=JobStatus(request.status.value),
            result=request.result,
            error=request.error,
        )
        
        # Decrement agent load
        if job.agent_id:
            await self.agent_repo.decrement_agent_load(job.agent_id)
        
        # Trigger next workflow step if job completed successfully
        next_job_triggered = False
        next_job_id = None
        
        if request.status == SchemaJobStatus.COMPLETED and job.next_job_id:
            dispatch_result = await self.dispatch_job(job.next_job_id)
            if dispatch_result:
                next_job_triggered = True
                next_job_id = job.next_job_id
        
        return JobCompletionResponse(
            job_id=request.job_id,
            status=request.status,
            next_job_triggered=next_job_triggered,
            next_job_id=next_job_id,
        )

    # ==================== Job Reassignment (21.5) ====================

    async def reassign_agent_jobs(
        self, agent_id: uuid.UUID
    ) -> JobReassignmentResult:
        """Reassign all processing jobs from an agent.
        
        Requirements: 21.5 - Requeue on agent disconnect
        """
        processing_jobs = await self.job_repo.get_processing_jobs_by_agent(agent_id)
        
        reassigned_ids: list[uuid.UUID] = []
        
        for job in processing_jobs:
            await self.job_repo.requeue_job(job.id)
            reassigned_ids.append(job.id)
        
        return JobReassignmentResult(
            reassigned_count=len(reassigned_ids),
            job_ids=reassigned_ids,
        )

    # ==================== Query Methods ====================

    async def get_agent_info(self, agent_id: uuid.UUID) -> Optional[AgentInfo]:
        """Get agent information."""
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        return AgentInfo(
            id=agent.id,
            type=SchemaAgentType(agent.type),
            hostname=agent.hostname,
            ip_address=agent.ip_address,
            status=SchemaAgentStatus(agent.status),
            current_load=agent.current_load,
            max_capacity=agent.max_capacity,
            last_heartbeat=agent.last_heartbeat,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    async def list_agents(self) -> AgentListResponse:
        """List all agents."""
        agents = await self.agent_repo.get_all_agents()
        
        agent_infos = [
            AgentInfo(
                id=a.id,
                type=SchemaAgentType(a.type),
                hostname=a.hostname,
                ip_address=a.ip_address,
                status=SchemaAgentStatus(a.status),
                current_load=a.current_load,
                max_capacity=a.max_capacity,
                last_heartbeat=a.last_heartbeat,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in agents
        ]
        
        healthy_count = sum(1 for a in agents if a.status == AgentStatus.HEALTHY.value)
        
        return AgentListResponse(
            agents=agent_infos,
            total=len(agents),
            healthy_count=healthy_count,
            unhealthy_count=len(agents) - healthy_count,
        )

    async def get_job_info(self, job_id: uuid.UUID) -> Optional[JobInfo]:
        """Get job information."""
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            return None
        
        return JobInfo(
            id=job.id,
            agent_id=job.agent_id,
            job_type=job.job_type,
            payload=job.payload,
            priority=job.priority,
            status=SchemaJobStatus(job.status),
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            result=job.result,
            error=job.error,
            workflow_id=job.workflow_id,
            next_job_id=job.next_job_id,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
