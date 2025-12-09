"""Create PostgreSQL database if it doesn't exist."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "youtube_automation")


async def create_database():
    """Create the database if it doesn't exist."""
    print("=" * 50)
    print("Creating PostgreSQL Database")
    print("=" * 50)
    print()
    print(f"Database Configuration:")
    print(f"  Host: {DATABASE_HOST}")
    print(f"  Port: {DATABASE_PORT}")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  User: {DATABASE_USER}")
    print()

    try:
        # Connect to postgres database (default database)
        print("Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database="postgres",
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DATABASE_NAME
        )

        if exists:
            print(f"✓ Database '{DATABASE_NAME}' already exists.")
        else:
            # Create database
            print(f"Creating database '{DATABASE_NAME}'...")
            await conn.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
            print(f"✓ Database '{DATABASE_NAME}' created successfully!")

        await conn.close()

        print()
        print("=" * 50)
        print("Database setup complete!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("  1. Run migrations: .\\scripts\\run_migrations.bat")
        print("  2. Start the server: .\\scripts\\run_dev.bat")
        print()

        return 0

    except asyncpg.exceptions.InvalidPasswordError:
        print("✗ Error: Invalid database password")
        print("  Please check your DATABASE_PASSWORD in .env file")
        return 1
    except asyncpg.exceptions.InvalidCatalogNameError:
        print("✗ Error: Could not connect to PostgreSQL")
        print("  Please ensure PostgreSQL is running")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(create_database())
    sys.exit(exit_code)
