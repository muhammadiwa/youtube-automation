"""Repository for Agent database operations.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.models import (
    Agent,
    AgentJob,
    AgentStatus,
    JobStatus,
)


class AgentRepository:
    """Repository for Agent database operations.
    
    Requirements: 21.1, 21.2
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(
        self,
        api_key_hash: str,
        agent_type: str,
        hostname: str,
        ip_address: Optional[str] = None,
        max_capacity: int = 5,
        metadata: Optional[dict] = None,
    ) -> Agent:
        """Create a new agent.
        
        Requirements: 21.1
        """
        agent = Agent(
            api_key_hash=api_key_hash,
            type=agent_type,
            hostname=hostname,
            ip_address=ip_address,
            max_capacity=max_capacity,
            agent_metadata=metadata,
            status=AgentStatus.HEALTHY.value,
            last_heartbeat=datetime.utcnow(),
        )
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_agent_by_id(self, agent_id: uuid.UUID) -> Optional[Agent]:
        """Get agent by ID."""
        query = select(Agent).where(Agent.id == agent_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_agent_by_api_key_hash(self, api_key_hash: str) -> Optional[Agent]:
        """Get agent by API key hash.
        
        Requirements: 21.1
        """
        query = select(Agent).where(Agent.api_key_hash == api_key_hash)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_agents(self) -> list[Agent]:
        """Get all agents."""
        query = select(Agent).order_by(Agent.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_healthy_agents(self, agent_type: Optional[str] = None) -> list[Agent]:
        """Get all healthy agents, optionally filtered by type.
        
        Requirements: 21.3
        """
        conditions = [Agent.status == AgentStatus.HEALTHY.value]
        if agent_type:
            conditions.append(Agent.type == agent_type)
        
        query = select(Agent).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_heartbeat(
        self,
        agent_id: uuid.UUID,
        current_load: int,
        metadata: Optional[dict] = None,
    ) -> Optional[Agent]:
        """Update agent heartbeat.
        
        Requirements: 21.1
        """
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        agent.last_heartbeat = datetime.utcnow()
        agent.current_load = current_load
        agent.status = AgentStatus.HEALTHY.value
        
        if metadata:
            agent.agent_metadata = metadata
        
        await self.session.flush()
        return agent

    async def update_agent_status(
        self, agent_id: uuid.UUID, status: AgentStatus
    ) -> Optional[Agent]:
        """Update agent status.
        
        Requirements: 21.2
        """
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        agent.status = status.value
        await self.session.flush()
        return agent

    async def get_agents_with_stale_heartbeat(
        self, threshold_seconds: int = 60
    ) -> list[Agent]:
        """Get agents with heartbeat older than threshold.
        
        Requirements: 21.2 - Mark unhealthy after 60s missed heartbeat
        """
        threshold_time = datetime.utcnow() - timedelta(seconds=threshold_seconds)
        
        query = select(Agent).where(
            and_(
                Agent.status == AgentStatus.HEALTHY.value,
                or_(
                    Agent.last_heartbeat < threshold_time,
                    Agent.last_heartbeat.is_(None),
                ),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def increment_agent_load(self, agent_id: uuid.UUID) -> Optional[Agent]:
        """Increment agent's current load."""
        agent = await self.get_agent_by_id(agent_id)
        if agent:
            agent.current_load += 1
            await self.session.flush()
        return agent

    async def decrement_agent_load(self, agent_id: uuid.UUID) -> Optional[Agent]:
        """Decrement agent's current load."""
        agent = await self.get_agent_by_id(agent_id)
        if agent and agent.current_load > 0:
            agent.current_load -= 1
            await self.session.flush()
        return agent


class AgentJobRepository:
    """Repository for AgentJob database operations.
    
    Requirements: 21.3, 21.4, 21.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(
        self,
        job_type: str,
        payload: dict,
        priority: int = 0,
        max_attempts: int = 3,
        workflow_id: Optional[uuid.UUID] = None,
        next_job_id: Optional[uuid.UUID] = None,
    ) -> AgentJob:
        """Create a new job."""
        job = AgentJob(
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_attempts=max_attempts,
            workflow_id=workflow_id,
            next_job_id=next_job_id,
            status=JobStatus.QUEUED.value,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional[AgentJob]:
        """Get job by ID."""
        query = select(AgentJob).where(AgentJob.id == job_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_jobs(
        self, job_type: Optional[str] = None, limit: int = 100
    ) -> list[AgentJob]:
        """Get pending jobs ordered by priority.
        
        Requirements: 21.3
        """
        conditions = [AgentJob.status == JobStatus.QUEUED.value]
        if job_type:
            conditions.append(AgentJob.job_type == job_type)
        
        query = (
            select(AgentJob)
            .where(and_(*conditions))
            .order_by(AgentJob.priority.desc(), AgentJob.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_jobs_by_agent(
        self, agent_id: uuid.UUID, status: Optional[JobStatus] = None
    ) -> list[AgentJob]:
        """Get jobs assigned to an agent."""
        conditions = [AgentJob.agent_id == agent_id]
        if status:
            conditions.append(AgentJob.status == status.value)
        
        query = select(AgentJob).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def assign_job_to_agent(
        self, job_id: uuid.UUID, agent_id: uuid.UUID
    ) -> Optional[AgentJob]:
        """Assign a job to an agent.
        
        Requirements: 21.3
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.agent_id = agent_id
        job.status = JobStatus.PROCESSING.value
        job.started_at = datetime.utcnow()
        job.attempts += 1
        
        await self.session.flush()
        return job

    async def complete_job(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[AgentJob]:
        """Mark job as completed.
        
        Requirements: 21.4
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = status.value
        job.result = result
        job.error = error
        job.completed_at = datetime.utcnow()
        
        await self.session.flush()
        return job

    async def requeue_job(self, job_id: uuid.UUID) -> Optional[AgentJob]:
        """Requeue a job for processing.
        
        Requirements: 21.5
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.agent_id = None
        job.status = JobStatus.QUEUED.value
        job.started_at = None
        
        await self.session.flush()
        return job

    async def get_processing_jobs_by_agent(
        self, agent_id: uuid.UUID
    ) -> list[AgentJob]:
        """Get jobs currently being processed by an agent.
        
        Requirements: 21.5
        """
        query = select(AgentJob).where(
            and_(
                AgentJob.agent_id == agent_id,
                AgentJob.status == JobStatus.PROCESSING.value,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def move_to_dlq(self, job_id: uuid.UUID, error: str) -> Optional[AgentJob]:
        """Move job to dead letter queue."""
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = JobStatus.DLQ.value
        job.error = error
        job.completed_at = datetime.utcnow()
        
        await self.session.flush()
        return job
