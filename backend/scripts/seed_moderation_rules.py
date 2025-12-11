"""
Seed sample moderation rules for a YouTube account.

This seeder requires an existing YouTube account ID.
Run: python scripts/seed_moderation_rules.py --account-id <uuid>

Or run without arguments to see usage instructions.
"""

import asyncio
import sys
import os
import argparse
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Sample moderation rules
SAMPLE_RULES = [
    {
        "name": "Block Spam Links",
        "description": "Automatically remove messages containing suspicious links",
        "rule_type": "links",
        "pattern": r"(https?:\/\/(?!youtube\.com|youtu\.be)[^\s]+)",
        "action_type": "delete",
        "severity": "medium",
        "is_enabled": True,
        "priority": 1,
    },
    {
        "name": "Excessive Caps Filter",
        "description": "Warn users who type in ALL CAPS excessively",
        "rule_type": "caps",
        "caps_threshold_percent": 70,
        "min_message_length": 10,
        "action_type": "warn",
        "severity": "low",
        "is_enabled": True,
        "priority": 2,
    },
    {
        "name": "Spam Detection",
        "description": "Detect and timeout users sending repetitive messages",
        "rule_type": "spam",
        "action_type": "timeout",
        "timeout_duration_seconds": 300,
        "severity": "medium",
        "is_enabled": True,
        "priority": 3,
    },
    {
        "name": "Self-Promotion Block",
        "description": "Block messages promoting other channels",
        "rule_type": "regex",
        "pattern": r"(subscribe|sub\s*to|check\s*out)\s*(my|our)\s*(channel|video)",
        "action_type": "delete",
        "severity": "medium",
        "is_enabled": True,
        "priority": 5,
    },
]


async def seed_moderation_rules(account_id: str):
    """Seed sample moderation rules for an account."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Verify account exists
        result = await session.execute(
            text("SELECT id FROM youtube_accounts WHERE id = :id"),
            {"id": account_id}
        )
        if not result.fetchone():
            print(f"❌ Error: YouTube account with ID '{account_id}' not found.")
            print("Please provide a valid account ID.")
            return
        
        # Check existing rules for this account
        result = await session.execute(
            text("SELECT COUNT(*) FROM moderation_rules WHERE account_id = :id"),
            {"id": account_id}
        )
        count = result.scalar()
        
        if count > 0:
            print(f"Found {count} existing rules for this account.")
            response = input("Do you want to add more rules? (y/n): ")
            if response.lower() != 'y':
                print("Skipping seed.")
                return
        
        # Insert sample rules
        for rule_data in SAMPLE_RULES:
            rule_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO moderation_rules 
                    (id, account_id, name, description, rule_type, pattern, 
                     action_type, severity, is_enabled, priority,
                     caps_threshold_percent, min_message_length, timeout_duration_seconds)
                    VALUES 
                    (:id, :account_id, :name, :description, :rule_type, :pattern,
                     :action_type, :severity, :is_enabled, :priority,
                     :caps_threshold_percent, :min_message_length, :timeout_duration_seconds)
                """),
                {
                    "id": rule_id,
                    "account_id": account_id,
                    "name": rule_data["name"],
                    "description": rule_data.get("description"),
                    "rule_type": rule_data["rule_type"],
                    "pattern": rule_data.get("pattern"),
                    "action_type": rule_data["action_type"],
                    "severity": rule_data.get("severity", "medium"),
                    "is_enabled": rule_data.get("is_enabled", True),
                    "priority": rule_data.get("priority", 0),
                    "caps_threshold_percent": rule_data.get("caps_threshold_percent"),
                    "min_message_length": rule_data.get("min_message_length"),
                    "timeout_duration_seconds": rule_data.get("timeout_duration_seconds"),
                }
            )
            print(f"✅ Created rule: {rule_data['name']}")
        
        await session.commit()
        print(f"\n🎉 Successfully seeded {len(SAMPLE_RULES)} moderation rules!")


def main():
    parser = argparse.ArgumentParser(description="Seed moderation rules for a YouTube account")
    parser.add_argument(
        "--account-id", "-a",
        type=str,
        help="YouTube account UUID to add rules to"
    )
    args = parser.parse_args()
    
    if not args.account_id:
        print("=" * 60)
        print("Moderation Rules Seeder")
        print("=" * 60)
        print("\nUsage: python scripts/seed_moderation_rules.py --account-id <uuid>")
        print("\nThis seeder creates sample moderation rules for a YouTube account.")
        print("You need to provide a valid YouTube account ID.")
        print("\nTo find account IDs, check the youtube_accounts table in your database.")
        return
    
    asyncio.run(seed_moderation_rules(args.account_id))


if __name__ == "__main__":
    main()
