"""Seed subscription plans with proper data.

Run with: python -m scripts.seed_plans
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete, text
from app.core.database import async_session_maker

# Import all models to ensure relationships are resolved
from app.modules.auth.models import User
from app.modules.account.models import YouTubeAccount
from app.modules.billing.models import Plan


# Plan data with proper icons, colors, and display features
# Bandwidth calculation:
# - 1 hour streaming @6000kbps = 2.7 GB
# - 1 hour streaming @3000kbps = 1.35 GB
# - Average stream duration: 4-8 hours
PLANS_DATA = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Get started with basic features",
        "price_monthly": 0,  # in cents
        "price_yearly": 0,
        "currency": "USD",
        "max_accounts": 1,
        "max_videos_per_month": 5,  # Limit uploads to prevent spam
        "max_streams_per_month": 1,
        "max_storage_gb": 1,  # Primary cost control
        "max_bandwidth_gb": 15,  # ~1 stream x 8 hours x 3000kbps = 4GB, buffer for testing
        "ai_generations_per_month": 0,
        "api_calls_per_month": 1000,
        "encoding_minutes_per_month": 60,
        "concurrent_streams": 1,
        "features": ["basic_upload", "basic_analytics", "live_streaming", "strike_monitoring"],
        "display_features": [
            {"name": "1 YouTube Account", "included": True},
            {"name": "1 GB Storage", "included": True},
            {"name": "5 Uploads/month", "included": True},
            {"name": "15 GB Bandwidth/month", "included": True},
            {"name": "1 Concurrent Stream", "included": True},
            {"name": "Basic Analytics", "included": True},
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
        "description": "Perfect for growing creators",
        "price_monthly": 999,  # $9.99
        "price_yearly": 9999,  # $99.99
        "currency": "USD",
        "max_accounts": 5,
        "max_videos_per_month": 20,  # Limit uploads to prevent spam
        "max_streams_per_month": 10,
        "max_storage_gb": 20,  # Primary cost control
        "max_bandwidth_gb": 100,  # ~10 streams x 4 hours x 4500kbps = 81GB + buffer
        "ai_generations_per_month": 0,
        "api_calls_per_month": 10000,
        "encoding_minutes_per_month": 300,
        "concurrent_streams": 2,
        "features": [
            "basic_upload", "basic_analytics", "advanced_analytics",
            "live_streaming", "strike_monitoring", "basic_moderation"
        ],
        "display_features": [
            {"name": "5 YouTube Accounts", "included": True},
            {"name": "20 GB Storage", "included": True},
            {"name": "20 Uploads/month", "included": True},
            {"name": "100 GB Bandwidth/month", "included": True},
            {"name": "2 Concurrent Streams", "included": True},
            {"name": "Advanced Analytics", "included": True},
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
        "description": "For professional creators & agencies",
        "price_monthly": 2999,  # $29.99
        "price_yearly": 29999,  # $299.99
        "currency": "USD",
        "max_accounts": 10,
        "max_videos_per_month": 100,  # Limit uploads to prevent spam
        "max_streams_per_month": 50,
        "max_storage_gb": 50,  # Primary cost control
        "max_bandwidth_gb": 500,  # ~30 streams x 6 hours x 6000kbps = 486GB + buffer
        "ai_generations_per_month": 0,
        "api_calls_per_month": 100000,
        "encoding_minutes_per_month": 1000,
        "concurrent_streams": 5,
        "features": [
            "basic_upload", "basic_analytics", "advanced_analytics",
            "live_streaming", "strike_monitoring", "advanced_moderation",
            "ai_insights", "report_generation", "channel_comparison"
        ],
        "display_features": [
            {"name": "10 YouTube Accounts", "included": True},
            {"name": "50 GB Storage", "included": True},
            {"name": "100 Uploads/month", "included": True},
            {"name": "500 GB Bandwidth/month", "included": True},
            {"name": "5 Concurrent Streams", "included": True},
            {"name": "Full Analytics Suite", "included": True},
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
        "description": "For agencies & MCN with custom needs",
        "price_monthly": 9999,  # $99.99
        "price_yearly": 99999,  # $999.99
        "currency": "USD",
        "max_accounts": -1,  # Unlimited
        "max_videos_per_month": -1,
        "max_streams_per_month": -1,
        "max_storage_gb": 500,  # Still have a high limit for cost control
        "max_bandwidth_gb": 5000,  # 5 TB
        "ai_generations_per_month": -1,
        "api_calls_per_month": -1,
        "encoding_minutes_per_month": -1,
        "concurrent_streams": -1,
        "features": [
            "basic_upload", "basic_analytics", "advanced_analytics",
            "live_streaming", "strike_monitoring", "advanced_moderation",
            "ai_insights", "report_generation", "channel_comparison",
            "priority_support", "custom_reports", "advanced_monitoring"
        ],
        "display_features": [
            {"name": "Unlimited Accounts", "included": True},
            {"name": "500 GB Storage", "included": True},
            {"name": "Unlimited Uploads", "included": True},
            {"name": "5 TB Bandwidth/month", "included": True},
            {"name": "Unlimited Concurrent Streams", "included": True},
            {"name": "Priority Support 24/7", "included": True},
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
