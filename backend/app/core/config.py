"""Application configuration settings.

All configuration values are loaded from environment variables (.env file).
No sensitive values should be hardcoded here.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    PROJECT_NAME: str = "YouTube Automation API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database - REQUIRED
    DATABASE_URL: str

    # Redis - REQUIRED
    REDIS_URL: str

    # Security - REQUIRED (no defaults for sensitive values)
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # KMS Encryption for OAuth tokens - REQUIRED
    KMS_ENCRYPTION_KEY: str  # Must be 32 bytes for AES-256

    # YouTube OAuth - REQUIRED for YouTube integration
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = ""

    # CORS
    CORS_ORIGINS: list[str] = []

    # Storage Configuration
    # STORAGE_BACKEND: local, s3, minio, gcs (Google Cloud Storage)
    STORAGE_BACKEND: str = "local"
    
    # Local Storage (when STORAGE_BACKEND=local)
    LOCAL_STORAGE_PATH: str = "./storage"
    
    # S3/MinIO/Compatible Storage (when STORAGE_BACKEND=s3 or minio)
    STORAGE_BUCKET: str = ""
    STORAGE_REGION: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_ENDPOINT_URL: Optional[str] = None  # Required for MinIO
    STORAGE_USE_SSL: bool = True
    
    # CDN Configuration (optional, for any backend)
    CDN_DOMAIN: Optional[str] = None
    CDN_ENABLED: bool = False

    # OpenAI API
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Email (for notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_TLS: bool = True

    # Comment Sync Settings
    COMMENT_SYNC_INTERVAL_MINUTES: int = 5
    COMMENT_SYNC_MAX_COMMENTS: int = 1000

    # Moderation Settings
    MODERATION_ANALYSIS_TIMEOUT_SECONDS: float = 2.0
    CHATBOT_RESPONSE_TIMEOUT_SECONDS: float = 3.0

    # Stream Settings
    STREAM_HEALTH_CHECK_INTERVAL_SECONDS: int = 10
    STREAM_RECONNECT_MAX_ATTEMPTS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
