"""Seed script for announcements.

Creates sample announcements for testing the admin panel and client display.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

# Import all models to ensure they are registered
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.admin.models import Announcement, Admin
from app.core.database import async_session_maker


async def seed_announcements():
    """Seed sample announcements."""
    async with async_session_maker() as session:
        # Check if announcements already exist
        result = await session.execute(select(Announcement).limit(1))
        if result.scalar_one_or_none():
            print("Announcements already exist. Skipping seed.")
            return

        # Get first admin for created_by (optional)
        admin_result = await session.execute(select(Admin).limit(1))
        admin = admin_result.scalar_one_or_none()
        admin_id = admin.id if admin else None

        now = datetime.utcnow()

        announcements = [
            Announcement(
                title="Welcome to YouTube Automation Platform!",
                content="We're excited to have you here. Explore our features including AI-powered thumbnails, multi-account management, and automated streaming.",
                announcement_type="success",
                is_active=True,
                is_dismissible=True,
                target_plans=None,
                start_date=now - timedelta(days=7),
                end_date=None,
                created_by=admin_id,
            ),
            Announcement(
                title="Scheduled Maintenance",
                content="We will be performing scheduled maintenance on Saturday, December 21st from 2:00 AM to 6:00 AM UTC. Some services may be temporarily unavailable.",
                announcement_type="warning",
                is_active=True,
                is_dismissible=True,
                target_plans=None,
                start_date=now,
                end_date=now + timedelta(days=7),
                created_by=admin_id,
            ),
            Announcement(
                title="New Feature: AI Thumbnail Generation",
                content="Generate stunning thumbnails for your videos using our new AI-powered feature. Available now for Pro and Enterprise plans!",
                announcement_type="info",
                is_active=True,
                is_dismissible=True,
                target_plans=["pro", "enterprise"],
                start_date=now - timedelta(days=3),
                end_date=None,
                created_by=admin_id,
            ),
            Announcement(
                title="Holiday Support Schedule",
                content="Our support team will have limited availability from December 24th to January 2nd. Response times may be longer than usual.",
                announcement_type="info",
                is_active=False,  # Inactive - for testing toggle
                is_dismissible=False,
                target_plans=None,
                start_date=now + timedelta(days=10),
                end_date=now + timedelta(days=20),
                created_by=admin_id,
            ),
            Announcement(
                title="Important: API Rate Limit Changes",
                content="Starting January 1st, 2025, we will be updating our API rate limits. Please review the documentation for details.",
                announcement_type="error",
                is_active=True,
                is_dismissible=False,
                target_plans=None,
                start_date=now,
                end_date=now + timedelta(days=30),
                created_by=admin_id,
            ),
        ]

        for announcement in announcements:
            session.add(announcement)

        await session.commit()
        print(f"Successfully seeded {len(announcements)} announcements.")


if __name__ == "__main__":
    asyncio.run(seed_announcements())
