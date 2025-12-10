"""Seed default subscription plans into the database.

This script creates the default plans (Free, Basic, Pro, Enterprise) in the database.
Run this after migrations to populate the plans table.

Usage:
    python scripts/seed_plans.py
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.billing.models import Plan


# Default plans configuration
DEFAULT_PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Get started with basic features",
        "price_monthly": 0,  # in cents
        "price_yearly": 0,
        "currency": "USD",
        "max_accounts": 1,
        "max_videos_per_month": 5,
        "max_streams_per_month": 0,
        "max_storage_gb": 1,
        "max_bandwidth_gb": 5,
        "ai_generations_per_month": 0,
        "api_calls_per_month": 1000,
        "encoding_minutes_per_month": 60,
        "concurrent_streams": 1,
        "features": ["basic_upload", "basic_analytics"],
        "display_features": [
            {"name": "1 YouTube Account", "included": True},
            {"name": "5 Videos/month", "included": True},
            {"name": "Basic Analytics", "included": True},
            {"name": "AI Features", "included": False},
            {"name": "Live Streaming", "included": False},
        ],
        "is_active": True,
        "is_popular": False,
        "sort_order": 0,
    },
    {
        "slug": "basic",
        "name": "Basic",
        "description": "Perfect for content creators getting started",
        "price_monthly": 999,  # $9.99 in cents
        "price_yearly": 9999,  # $99.99 in cents
        "currency": "USD",
        "max_accounts": 3,
        "max_videos_per_month": 50,
        "max_streams_per_month": 5,
        "max_storage_gb": 10,
        "max_bandwidth_gb": 50,
        "ai_generations_per_month": 100,
        "api_calls_per_month": 10000,
        "encoding_minutes_per_month": 300,
        "concurrent_streams": 2,
        "features": ["basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles", "live_streaming"],
        "display_features": [
            {"name": "3 YouTube Accounts", "included": True},
            {"name": "50 Videos/month", "included": True},
            {"name": "Advanced Analytics", "included": True},
            {"name": "AI Features (100/month)", "included": True},
            {"name": "Live Streaming (5/month)", "included": True},
        ],
        "is_active": True,
        "is_popular": False,
        "sort_order": 1,
    },
    {
        "slug": "pro",
        "name": "Pro",
        "description": "For professional creators and small teams",
        "price_monthly": 2999,  # $29.99 in cents
        "price_yearly": 29999,  # $299.99 in cents
        "currency": "USD",
        "max_accounts": 10,
        "max_videos_per_month": -1,  # Unlimited
        "max_streams_per_month": -1,
        "max_storage_gb": 100,
        "max_bandwidth_gb": 500,
        "ai_generations_per_month": 500,
        "api_calls_per_month": 100000,
        "encoding_minutes_per_month": 1000,
        "concurrent_streams": 5,
        "features": [
            "basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles",
            "ai_thumbnails", "bulk_upload", "simulcast", "chat_moderation", "competitor_analysis"
        ],
        "display_features": [
            {"name": "10 YouTube Accounts", "included": True},
            {"name": "Unlimited Videos", "included": True},
            {"name": "Full Analytics Suite", "included": True},
            {"name": "AI Features (500/month)", "included": True},
            {"name": "Unlimited Streaming", "included": True},
        ],
        "is_active": True,
        "is_popular": True,  # Mark as most popular
        "sort_order": 2,
    },
    {
        "slug": "enterprise",
        "name": "Enterprise",
        "description": "For large teams and agencies",
        "price_monthly": 9999,  # $99.99 in cents
        "price_yearly": 99999,  # $999.99 in cents
        "currency": "USD",
        "max_accounts": -1,  # Unlimited
        "max_videos_per_month": -1,
        "max_streams_per_month": -1,
        "max_storage_gb": -1,
        "max_bandwidth_gb": -1,
        "ai_generations_per_month": -1,
        "api_calls_per_month": -1,
        "encoding_minutes_per_month": -1,
        "concurrent_streams": -1,
        "features": [
            "basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles",
            "ai_thumbnails", "bulk_upload", "simulcast", "chat_moderation", "competitor_analysis",
            "api_access", "webhooks", "priority_support", "custom_branding", "sla_guarantee"
        ],
        "display_features": [
            {"name": "Unlimited Accounts", "included": True},
            {"name": "Unlimited Everything", "included": True},
            {"name": "Priority Support", "included": True},
            {"name": "Custom Integrations", "included": True},
            {"name": "Dedicated Account Manager", "included": True},
        ],
        "is_active": True,
        "is_popular": False,
        "sort_order": 3,
    },
]


async def seed_plans():
    """Seed default plans into the database."""
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True,
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        print("Starting plan seeding...")
        
        for plan_data in DEFAULT_PLANS:
            # Check if plan already exists
            result = await session.execute(
                select(Plan).where(Plan.slug == plan_data["slug"])
            )
            existing_plan = result.scalar_one_or_none()
            
            if existing_plan:
                print(f"Updating existing plan: {plan_data['slug']}")
                # Update existing plan
                for key, value in plan_data.items():
                    setattr(existing_plan, key, value)
            else:
                print(f"Creating new plan: {plan_data['slug']}")
                # Create new plan
                plan = Plan(**plan_data)
                session.add(plan)
        
        await session.commit()
        print("Plan seeding completed successfully!")
        
        # Verify plans
        result = await session.execute(select(Plan).order_by(Plan.sort_order))
        plans = result.scalars().all()
        print(f"\nSeeded {len(plans)} plans:")
        for plan in plans:
            print(f"  - {plan.name} (${plan.price_monthly/100}/mo)")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_plans())
