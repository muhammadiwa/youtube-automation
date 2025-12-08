"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "YouTube Automation API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # KMS Encryption for OAuth tokens
    KMS_ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here"  # Must be 32 bytes for AES-256

    # YouTube OAuth
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/accounts/oauth/callback"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # S3/CDN Storage for transcoded outputs
    S3_BUCKET: str = "youtube-automation-transcoded"
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""  # For MinIO or other S3-compatible storage
    CDN_DOMAIN: str = ""  # CloudFront or other CDN domain

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
