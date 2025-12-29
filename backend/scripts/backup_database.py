"""Database backup script.

Creates a backup of the PostgreSQL database before running migrations.

Usage:
    python scripts/backup_database.py
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def backup_database():
    """Create a database backup using pg_dump."""
    # Parse DATABASE_URL to get connection details
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "")
    
    # Extract components
    if "@" in db_url:
        auth, rest = db_url.split("@")
        user, password = auth.split(":")
        host_port, dbname = rest.split("/")
        host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
    else:
        print("ERROR: Could not parse DATABASE_URL")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f"backup_{timestamp}.sql"
    
    print(f"🔄 Creating database backup...")
    print(f"   Database: {dbname}")
    print(f"   Host: {host}:{port}")
    print(f"   Backup file: {backup_file}")
    
    try:
        # Run pg_dump
        env = {"PGPASSWORD": password}
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            "-f", str(backup_file),
            "--verbose"
        ]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Backup created successfully!")
            print(f"   File: {backup_file}")
            print(f"   Size: {file_size:.2f} MB")
            return True
        else:
            print(f"❌ Backup failed!")
            print(f"   Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ ERROR: pg_dump not found!")
        print("   Please install PostgreSQL client tools")
        print("   Windows: Install PostgreSQL from https://www.postgresql.org/download/windows/")
        print("   Linux: sudo apt-get install postgresql-client")
        print("   Mac: brew install postgresql")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Main entry point."""
    print("🚀 Database Backup Script")
    print("=" * 50)
    
    success = backup_database()
    
    if success:
        print("\n✅ Backup complete! You can now run the migration.")
        print("   To run migration: cd backend && alembic upgrade head")
        sys.exit(0)
    else:
        print("\n❌ Backup failed! Please fix the errors before running migration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
