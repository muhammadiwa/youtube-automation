"""
Setup Admin User Script.

This script helps setup or verify admin user configuration.
It can:
1. Check if admin user exists
2. Check if admin has 2FA enabled
3. Generate 2FA secret for admin if needed

Run: python scripts/setup_admin.py

Usage:
  python scripts/setup_admin.py --check          # Check admin status
  python scripts/setup_admin.py --setup-2fa     # Setup 2FA for admin
  python scripts/setup_admin.py --create        # Create admin if not exists
"""

import asyncio
import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Load environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation")


async def get_session():
    """Create database session."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


async def check_admin_status():
    """Check admin user status."""
    print("\n" + "=" * 60)
    print("🔍 CHECKING ADMIN STATUS")
    print("=" * 60)
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if admin user exists
        result = await session.execute(
            select("*").select_from(
                __import__('sqlalchemy').text("users")
            ).where(
                __import__('sqlalchemy').text("email = 'admin@youtubeautomation.com'")
            )
        )
        
        from sqlalchemy import text
        
        # Check user
        user_result = await session.execute(
            text("SELECT id, email, name, is_active, totp_secret FROM users WHERE email = 'admin@youtubeautomation.com'")
        )
        user = user_result.fetchone()
        
        if not user:
            print("\n❌ Admin user NOT FOUND!")
            print("   Run migrations first: alembic upgrade head")
            await engine.dispose()
            return False
        
        user_id, email, name, is_active, totp_secret = user
        
        print(f"\n✅ Admin User Found:")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Name: {name}")
        print(f"   Active: {is_active}")
        print(f"   2FA Enabled: {'Yes' if totp_secret else 'No'}")
        
        # Check admin record
        admin_result = await session.execute(
            text("SELECT id, role, is_active, permissions FROM admins WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        admin = admin_result.fetchone()
        
        if not admin:
            print("\n❌ Admin record NOT FOUND in admins table!")
            print("   Run migrations: alembic upgrade head")
            await engine.dispose()
            return False
        
        admin_id, role, admin_active, permissions = admin
        
        print(f"\n✅ Admin Record Found:")
        print(f"   Admin ID: {admin_id}")
        print(f"   Role: {role}")
        print(f"   Active: {admin_active}")
        print(f"   Permissions: {permissions}")
        
        # Check 2FA status
        if not totp_secret:
            print("\n📝 2FA is NOT enabled (optional)")
            print("   Admin can login without 2FA.")
            print("   To enable 2FA: python scripts/setup_admin.py --setup-2fa")
        else:
            print("\n✅ 2FA is enabled - Admin will need 2FA code to login")
        
        print("\n" + "=" * 60)
        print("📋 LOGIN CREDENTIALS:")
        print("   Email: admin@youtubeautomation.com")
        print("   Password: Admin@123456")
        print("=" * 60)
        
    await engine.dispose()
    return True


async def setup_2fa():
    """Setup 2FA for admin user."""
    print("\n" + "=" * 60)
    print("🔐 SETTING UP 2FA FOR ADMIN")
    print("=" * 60)
    
    import pyotp
    import qrcode
    import io
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import text
        
        # Get admin user
        user_result = await session.execute(
            text("SELECT id, email, totp_secret FROM users WHERE email = 'admin@youtubeautomation.com'")
        )
        user = user_result.fetchone()
        
        if not user:
            print("\n❌ Admin user NOT FOUND!")
            print("   Run migrations first: alembic upgrade head")
            await engine.dispose()
            return
        
        user_id, email, existing_secret = user
        
        if existing_secret:
            print(f"\n⚠️  2FA is already enabled for {email}")
            confirm = input("   Do you want to regenerate? (yes/no): ")
            if confirm.lower() != "yes":
                print("   Cancelled.")
                await engine.dispose()
                return
        
        # Generate new TOTP secret
        secret = pyotp.random_base32()
        
        # Update user with new secret
        await session.execute(
            text("UPDATE users SET totp_secret = :secret WHERE id = :user_id"),
            {"secret": secret, "user_id": user_id}
        )
        await session.commit()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="YouTube Automation Admin"
        )
        
        print(f"\n✅ 2FA Secret Generated!")
        print(f"\n📱 SETUP INSTRUCTIONS:")
        print("-" * 60)
        print(f"1. Open your authenticator app (Google Authenticator, Authy, etc.)")
        print(f"2. Add a new account using one of these methods:")
        print(f"\n   Option A - Manual Entry:")
        print(f"   Secret Key: {secret}")
        print(f"\n   Option B - QR Code URL:")
        print(f"   {provisioning_uri}")
        
        # Try to generate QR code in terminal
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            print(f"\n   Option C - Scan QR Code:")
            # Print QR code to terminal
            qr.print_ascii(invert=True)
        except Exception:
            pass
        
        print("\n" + "-" * 60)
        print(f"3. After adding, verify with a test code:")
        
        # Test verification
        test_code = input("   Enter current 6-digit code from app: ")
        if totp.verify(test_code):
            print("   ✅ Code verified! 2FA is working correctly.")
        else:
            print("   ❌ Invalid code. Please try again or re-scan the QR code.")
        
        print("\n" + "=" * 60)
        print("🎉 2FA SETUP COMPLETE!")
        print("   You can now login to the admin panel.")
        print("=" * 60)
        
    await engine.dispose()


async def main():
    parser = argparse.ArgumentParser(description="Setup Admin User")
    parser.add_argument("--check", action="store_true", help="Check admin status")
    parser.add_argument("--setup-2fa", action="store_true", help="Setup 2FA for admin")
    
    args = parser.parse_args()
    
    if args.setup_2fa:
        await setup_2fa()
    else:
        # Default to check
        await check_admin_status()


if __name__ == "__main__":
    asyncio.run(main())
