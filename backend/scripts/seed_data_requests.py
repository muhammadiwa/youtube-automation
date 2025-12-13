"""Seed script for data export and deletion requests.

This script populates the database with sample data export and deletion requests
for testing the Data Requests admin page.

Usage:
    cd backend
    python -m scripts.seed_data_requests
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.auth.models import User
from app.modules.admin.models import (
    DataExportRequest,
    DataExportRequestStatus,
    DeletionRequest,
    DeletionRequestStatusEnum,
)


async def seed_data_requests():
    """Seed data export and deletion requests."""
    async with async_session_maker() as session:
        # Get some users to create requests for
        result = await session.execute(select(User).limit(10))
        users = result.scalars().all()
        
        if not users:
            print("No users found. Please create some users first.")
            return
        
        print(f"Found {len(users)} users")
        
        # Clear existing requests
        await session.execute(
            DataExportRequest.__table__.delete()
        )
        await session.execute(
            DeletionRequest.__table__.delete()
        )
        await session.commit()
        print("Cleared existing data requests")
        
        now = datetime.utcnow()
        
        # Create data export requests
        export_requests = []
        statuses = [
            DataExportRequestStatus.PENDING,
            DataExportRequestStatus.COMPLETED,  # Make sure we have completed ones
            DataExportRequestStatus.PROCESSING,
            DataExportRequestStatus.FAILED,
        ]
        
        for i, user in enumerate(users):
            status = statuses[i % len(statuses)]
            requested_at = now - timedelta(days=i * 2, hours=i * 3)
            
            request = DataExportRequest(
                id=uuid.uuid4(),
                user_id=user.id,
                status=status.value,
                requested_at=requested_at,
            )
            
            if status == DataExportRequestStatus.PROCESSING:
                request.processed_at = requested_at + timedelta(hours=1)
            elif status == DataExportRequestStatus.COMPLETED:
                request.processed_at = requested_at + timedelta(hours=1)
                request.completed_at = requested_at + timedelta(hours=2)
                request.download_url = f"/compliance/exports/{request.id}/download"
                request.expires_at = now + timedelta(days=7)
                request.file_size = 1024 * 100 * (i + 1)
            elif status == DataExportRequestStatus.FAILED:
                request.processed_at = requested_at + timedelta(hours=1)
                request.error_message = "Failed to generate export: timeout"
            
            export_requests.append(request)
            session.add(request)
        
        print(f"Created {len(export_requests)} data export requests")
        
        # Create deletion requests
        deletion_requests = []
        deletion_statuses = [
            DeletionRequestStatusEnum.PENDING,
            DeletionRequestStatusEnum.SCHEDULED,
            DeletionRequestStatusEnum.PROCESSING,
            DeletionRequestStatusEnum.COMPLETED,
            DeletionRequestStatusEnum.CANCELLED,
        ]
        
        for i, user in enumerate(users[3:8] if len(users) > 3 else users):
            status = deletion_statuses[i % len(deletion_statuses)]
            requested_at = now - timedelta(days=i * 5, hours=i * 2)
            scheduled_for = requested_at + timedelta(days=30)  # 30-day grace period
            
            request = DeletionRequest(
                id=uuid.uuid4(),
                user_id=user.id,
                status=status.value,
                requested_at=requested_at,
                scheduled_for=scheduled_for,
            )
            
            if status == DeletionRequestStatusEnum.SCHEDULED:
                request.processed_at = requested_at + timedelta(hours=1)
            elif status == DeletionRequestStatusEnum.PROCESSING:
                request.processed_at = requested_at + timedelta(hours=1)
            elif status == DeletionRequestStatusEnum.COMPLETED:
                request.processed_at = requested_at + timedelta(hours=1)
                request.completed_at = scheduled_for + timedelta(hours=1)
            elif status == DeletionRequestStatusEnum.CANCELLED:
                request.cancelled_at = requested_at + timedelta(days=10)
                request.cancellation_reason = "User requested to keep account"
            
            deletion_requests.append(request)
            session.add(request)
        
        print(f"Created {len(deletion_requests)} deletion requests")
        
        await session.commit()
        print("Data requests seeded successfully!")
        
        # Print summary
        print("\n=== Data Export Requests ===")
        for req in export_requests:
            result = await session.execute(select(User).where(User.id == req.user_id))
            user = result.scalar_one_or_none()
            print(f"  - {user.email if user else 'Unknown'}: {req.status}")
        
        print("\n=== Deletion Requests ===")
        for req in deletion_requests:
            result = await session.execute(select(User).where(User.id == req.user_id))
            user = result.scalar_one_or_none()
            days_remaining = max(0, (req.scheduled_for - now).days)
            print(f"  - {user.email if user else 'Unknown'}: {req.status} ({days_remaining} days remaining)")


if __name__ == "__main__":
    asyncio.run(seed_data_requests())
