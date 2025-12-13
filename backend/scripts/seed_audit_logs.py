"""Seed audit logs for testing.

Run with: python -m scripts.seed_audit_logs
"""

import asyncio
import uuid
from datetime import datetime, timedelta
import random

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.auth.audit import AuditLog, AuditAction


# Sample events for testing
SAMPLE_EVENTS = [
    {"action": "login", "event": None, "resource_type": None},
    {"action": "login_failed", "event": None, "resource_type": None},
    {"action": "logout", "event": None, "resource_type": None},
    {"action": "admin_action", "event": "admin_access_denied", "resource_type": None},
    {"action": "admin_action", "event": "subscription_modified", "resource_type": "subscription"},
    {"action": "admin_action", "event": "discount_code_created", "resource_type": "discount_code"},
    {"action": "admin_action", "event": "discount_code_updated", "resource_type": "discount_code"},
    {"action": "admin_action", "event": "user_suspended", "resource_type": "user"},
    {"action": "admin_action", "event": "user_activated", "resource_type": "user"},
    {"action": "admin_action", "event": "config_updated", "resource_type": "system_config"},
    {"action": "admin_action", "event": "backup_created", "resource_type": "backup"},
    {"action": "admin_action", "event": "content_approved", "resource_type": "content_report"},
    {"action": "admin_action", "event": "content_removed", "resource_type": "content_report"},
    {"action": "admin_action", "event": "user_warned", "resource_type": "user"},
    {"action": "admin_action", "event": "refund_processed", "resource_type": "refund"},
    {"action": "password_change", "event": None, "resource_type": None},
    {"action": "2fa_enable", "event": None, "resource_type": None},
    {"action": "2fa_disable", "event": None, "resource_type": None},
    {"action": "account_update", "event": None, "resource_type": None},
]

SAMPLE_IPS = [
    "127.0.0.1",
    "192.168.1.100",
    "10.0.0.50",
    "172.16.0.25",
]

SAMPLE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


async def seed_audit_logs():
    """Seed audit logs to database."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Generate sample user IDs
        user_ids = [uuid.uuid4() for _ in range(5)]
        admin_id = uuid.uuid4()
        
        # Create 50 sample audit logs
        logs = []
        now = datetime.utcnow()
        
        for i in range(50):
            sample = random.choice(SAMPLE_EVENTS)
            
            # Build details
            details = {}
            if sample["event"]:
                details["event"] = sample["event"]
            if sample["resource_type"]:
                details["resource_type"] = sample["resource_type"]
                details["resource_id"] = str(uuid.uuid4())
            if sample["action"] == "admin_action":
                details["admin_id"] = str(admin_id)
            
            # Random timestamp in last 7 days
            timestamp = now - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            
            log = AuditLog(
                user_id=random.choice(user_ids) if sample["action"] != "login_failed" else None,
                action=sample["action"],
                details=details if details else None,
                ip_address=random.choice(SAMPLE_IPS),
                user_agent=random.choice(SAMPLE_USER_AGENTS),
            )
            # Override timestamp
            log.timestamp = timestamp
            
            logs.append(log)
        
        # Add all logs
        session.add_all(logs)
        await session.commit()
        
        print(f"✅ Created {len(logs)} audit log entries")


if __name__ == "__main__":
    asyncio.run(seed_audit_logs())
