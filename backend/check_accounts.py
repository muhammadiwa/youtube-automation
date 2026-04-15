"""Quick script to check accounts in database."""
import asyncio
from sqlalchemy import select
from app.core.database import get_session
from app.modules.account.models import YouTubeAccount
from app.modules.auth.models import User

async def check_accounts():
    async for session in get_session():
        # Get users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"=== USERS ({len(users)}) ===")
        for user in users:
            print(f"  - {user.email} (id: {user.id})")
        
        # Get accounts
        result = await session.execute(select(YouTubeAccount))
        accounts = result.scalars().all()
        
        print(f"\n=== YOUTUBE ACCOUNTS ({len(accounts)}) ===")
        for acc in accounts:
            print(f"  - {acc.channel_title}")
            print(f"    user_id: {acc.user_id}")
            print(f"    status: {acc.status}")
            print(f"    id: {acc.id}")
            print()
        
        break

if __name__ == "__main__":
    asyncio.run(check_accounts())
