"""Seed script for backup schedules.

This script creates default backup schedules for the platform.
Run with: python -m scripts.seed_backups
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.admin.models import BackupSchedule, BackupType


async def seed_backup_schedules():
    """Create default backup schedules."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if schedules already exist
        result = await session.execute(select(BackupSchedule))
        existing = result.scalars().all()
        
        if existing:
            print(f"Found {len(existing)} existing backup schedules. Skipping seed.")
            return
        
        # Default admin user ID (you may need to adjust this)
        admin_id = uuid.uuid4()  # Placeholder - should be actual admin ID
        
        # Create default schedules
        schedules = [
            BackupSchedule(
                name="Daily Full Backup",
                backup_type=BackupType.FULL.value,
                frequency="daily",
                cron_expression="0 2 * * *",  # 2 AM daily
                retention_days=30,
                max_backups=30,
                storage_provider="local",
                storage_location="/backups/daily",
                is_active=True,
                next_run_at=datetime.utcnow() + timedelta(days=1),
                configured_by=admin_id,
            ),
            BackupSchedule(
                name="Weekly Full Backup",
                backup_type=BackupType.FULL.value,
                frequency="weekly",
                cron_expression="0 3 * * 0",  # 3 AM Sunday
                retention_days=90,
                max_backups=12,
                storage_provider="local",
                storage_location="/backups/weekly",
                is_active=True,
                next_run_at=datetime.utcnow() + timedelta(weeks=1),
                configured_by=admin_id,
            ),
            BackupSchedule(
                name="Monthly Archive Backup",
                backup_type=BackupType.FULL.value,
                frequency="monthly",
                cron_expression="0 4 1 * *",  # 4 AM on 1st of month
                retention_days=365,
                max_backups=12,
                storage_provider="local",
                storage_location="/backups/monthly",
                is_active=True,
                next_run_at=datetime.utcnow() + timedelta(days=30),
                configured_by=admin_id,
            ),
            BackupSchedule(
                name="Hourly Incremental Backup",
                backup_type=BackupType.INCREMENTAL.value,
                frequency="hourly",
                cron_expression="0 * * * *",  # Every hour
                retention_days=7,
                max_backups=168,  # 7 days * 24 hours
                storage_provider="local",
                storage_location="/backups/hourly",
                is_active=False,  # Disabled by default
                next_run_at=datetime.utcnow() + timedelta(hours=1),
                configured_by=admin_id,
            ),
        ]
        
        for schedule in schedules:
            session.add(schedule)
        
        await session.commit()
        print(f"Created {len(schedules)} backup schedules successfully!")
        
        # Print created schedules
        for schedule in schedules:
            status = "Active" if schedule.is_active else "Inactive"
            print(f"  - {schedule.name} ({schedule.frequency}) [{status}]")


if __name__ == "__main__":
    asyncio.run(seed_backup_schedules())
