"""Seed subscription plans with proper data.

Run with: python -m scripts.seed_plans
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from app.core.database import async_session_maker
from app.modules.billing.models import Plan


# Plan data with proper icons, colors, and display features
PLANS_DATA = [
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
        "icon": "Sparkles",
        "color": "slate",
        "is_active": True,
        "is_popular": False,
        "sort_order": 0,
    },
    {
        "slug": "basic",
        "name": "Basic",
        "description": "Perfect for content creators getting started",
        "price_monthly": 999,  # $9.99
        "price_yearly": 9999,  # $99.99
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
        "features": [
            "basic_upload", "basic_analytics", "scheduled_publishing",
            "ai_titles", "live_streaming"
        ],
        "display_features": [
            {"name": "3 YouTube Accounts", "included": True},
            {"name": "50 Videos/month", "included": True},
            {"name": "Advanced Analytics", "included": True},
            {"name": "AI Features (100/month)", "included": True},
            {"name": "Live Streaming (5/month)", "included": True},
        ],
        "icon": "Zap",
        "color": "blue",
        "is_active": True,
        "is_popular": False,
        "sort_order": 1,
    },
    {
        "slug": "pro",
        "name": "Pro",
        "description": "For professional creators and small teams",
        "price_monthly": 2999,  # $29.99
        "price_yearly": 29999,  # $299.99
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
            "basic_upload", "basic_analytics", "scheduled_publishing",
            "ai_titles", "ai_thumbnails", "bulk_upload", "simulcast",
            "chat_moderation", "competitor_analysis", "live_streaming",
            "advanced_analytics"
        ],
        "display_features": [
            {"name": "10 YouTube Accounts", "included": True},
            {"name": "Unlimited Videos", "included": True},
            {"name": "Full Analytics Suite", "included": True},
            {"name": "AI Features (500/month)", "included": True},
            {"name": "Unlimited Streaming", "included": True},
        ],
        "icon": "Crown",
        "color": "violet",
        "is_active": True,
        "is_popular": True,
        "sort_order": 2,
    },
    {
        "slug": "enterprise",
        "name": "Enterprise",
        "description": "For large teams and agencies",
        "price_monthly": 9999,  # $99.99
        "price_yearly": 99999,  # $999.99
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
            "basic_upload", "basic_analytics", "scheduled_publishing",
            "ai_titles", "ai_thumbnails", "bulk_upload", "simulcast",
            "chat_moderation", "competitor_analysis", "api_access",
            "webhooks", "priority_support", "custom_branding",
            "sla_guarantee", "live_streaming", "advanced_analytics",
            "team_collaboration"
        ],
        "display_features": [
            {"name": "Unlimited Accounts", "included": True},
            {"name": "Unlimited Everything", "included": True},
            {"name": "Priority Support", "included": True},
            {"name": "Custom Integrations", "included": True},
            {"name": "Dedicated Account Manager", "included": True},
        ],
        "icon": "Building2",
        "color": "amber",
        "is_active": True,
        "is_popular": False,
        "sort_order": 3,
    },
]


async def seed_plans(reset: bool = False):
    """Seed plans into database.
    
    Args:
        reset: If True, delete all existing plans first
    """
    async with async_session_maker() as session:
        if reset:
            print("Deleting existing plans...")
            await session.execute(delete(Plan))
            await session.commit()
            print("Existing plans deleted.")
        
        for plan_data in PLANS_DATA:
            # Check if plan already exists
            result = await session.execute(
                select(Plan).where(Plan.slug == plan_data["slug"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing plan
                print(f"Updating plan: {plan_data['slug']}")
                for key, value in plan_data.items():
                    setattr(existing, key, value)
            else:
                # Create new plan
                print(f"Creating plan: {plan_data['slug']}")
                plan = Plan(**plan_data)
                session.add(plan)
        
        await session.commit()
        print("\nPlans seeded successfully!")
        
        # Display summary
        result = await session.execute(select(Plan).order_by(Plan.sort_order))
        plans = result.scalars().all()
        
        print("\n" + "=" * 60)
        print("PLANS SUMMARY")
        print("=" * 60)
        for plan in plans:
            price_monthly = plan.price_monthly / 100
            print(f"\n{plan.name} ({plan.slug})")
            print(f"  Icon: {plan.icon}, Color: {plan.color}")
            print(f"  Price: ${price_monthly:.2f}/month")
            print(f"  Accounts: {plan.max_accounts if plan.max_accounts != -1 else 'Unlimited'}")
            print(f"  Videos: {plan.max_videos_per_month if plan.max_videos_per_month != -1 else 'Unlimited'}/month")
            print(f"  AI: {plan.ai_generations_per_month if plan.ai_generations_per_month != -1 else 'Unlimited'}/month")
            print(f"  Popular: {'Yes' if plan.is_popular else 'No'}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed subscription plans")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing plans before seeding"
    )
    args = parser.parse_args()
    
    asyncio.run(seed_plans(reset=args.reset))
