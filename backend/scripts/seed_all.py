"""
Master seeder information script.

This script provides information about available seeders and how to use them.

Run: python scripts/seed_all.py
"""

def main():
    print("=" * 70)
    print("🌱 YOUTUBE AUTOMATION - DATABASE SEEDERS")
    print("=" * 70)
    
    print("\n📦 AUTOMATIC SEEDERS (via migrations):")
    print("-" * 70)
    print("""
The following data is automatically seeded when you run migrations:

  alembic upgrade head

This will create:
  ✅ Plans (Free, Basic, Pro, Enterprise)
  ✅ Payment Gateways (Stripe, PayPal, Midtrans, Xendit)
  ✅ Default Admin User
     - Email: admin@youtubeautomation.com
     - Password: Admin@123456
""")
    
    print("\n📦 MANUAL SEEDERS (optional):")
    print("-" * 70)
    print("""
1. Moderation Rules (requires YouTube account):
   python scripts/seed_moderation_rules.py --account-id <uuid>
   
   Creates sample moderation rules for chat moderation.

2. Plans (standalone, if needed):
   python scripts/seed_plans.py
   
   Creates subscription plans (also done via migration).
""")
    
    print("\n📋 NOTES:")
    print("-" * 70)
    print("""
- Most seed data is now included in migrations for consistency
- Moderation rules require a YouTube account to be connected first
- Custom commands, chatbot settings, etc. are per-account and should
  be configured through the UI after connecting a YouTube account
""")
    
    print("\n" + "=" * 70)
    print("For more information, check the README.md in backend/scripts/")
    print("=" * 70)


if __name__ == "__main__":
    main()
