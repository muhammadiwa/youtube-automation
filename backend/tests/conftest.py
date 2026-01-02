"""Pytest configuration and fixtures for all tests.

This module sets up the test environment, including:
- Loading environment variables from .env file
- Configuring test database
- Setting up common fixtures
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file before any imports
env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Set minimal required environment variables for testing
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("KMS_ENCRYPTION_KEY", "test-32-byte-encryption-key-test")
    os.environ.setdefault("PROJECT_NAME", "YouTube Automation API - Test")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("STORAGE_BACKEND", "local")
    os.environ.setdefault("LOCAL_STORAGE_PATH", "./storage")


@pytest.fixture(scope="session")
def test_env():
    """Provide test environment configuration."""
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "REDIS_URL": os.getenv("REDIS_URL"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
    }
