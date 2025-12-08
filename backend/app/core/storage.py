"""Universal storage module supporting multiple backends.

Supports: local filesystem, S3, MinIO, and other S3-compatible storage.
"""

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Union

from app.core.config import settings


@dataclass
class StorageResult:
    """Result of a storage operation."""
    success: bool
    key: str
    url: str
    file_size: int = 0
    etag: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class StorageConfig:
    """Storage configuration."""
    backend: str  # local, s3, minio, gcs
    bucket: str = ""
    region: str = ""
    access_key: str = ""
    secret_key: str = ""
    endpoint_url: Optional[str] = None
    use_ssl: bool = True
    local_path: str = "./storage"
    cdn_domain: Optional[str] = None
    cdn_enabled: bool = False


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file to storage."""
        pass

    @abstractmethod
    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file object to storage."""
        pass

    @abstractmethod
    def download(self, key: str, destination: str) -> bool:
        """Download a file from storage."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        pass

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for a file (presigned for private storage)."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, config: StorageConfig):
        self.base_path = Path(config.local_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.cdn_domain = config.cdn_domain
        self.cdn_enabled = config.cdn_enabled

    def _get_full_path(self, key: str) -> Path:
        """Get full path for a key."""
        return self.base_path / key

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file to local storage."""
        try:
            dest_path = self._get_full_path(key)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(file_path, dest_path)
            file_size = dest_path.stat().st_size
            
            return StorageResult(
                success=True,
                key=key,
                url=self.get_url(key),
                file_size=file_size,
            )
        except Exception as e:
            return StorageResult(
                success=False,
                key=key,
                url="",
                error_message=str(e),
            )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file object to local storage."""
        try:
            dest_path = self._get_full_path(key)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(fileobj, f)
            
            file_size = dest_path.stat().st_size
            
            return StorageResult(
                success=True,
                key=key,
                url=self.get_url(key),
                file_size=file_size,
            )
        except Exception as e:
            return StorageResult(
                success=False,
                key=key,
                url="",
                error_message=str(e),
            )

    def download(self, key: str, destination: str) -> bool:
        """Download a file from local storage."""
        try:
            src_path = self._get_full_path(key)
            if src_path.exists():
                shutil.copy2(src_path, destination)
                return True
            return False
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a file from local storage."""
        try:
            file_path = self._get_full_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if a file exists in local storage."""
        return self._get_full_path(key).exists()

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for a file."""
        if self.cdn_enabled and self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        return f"file://{self._get_full_path(key).absolute()}"

    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix."""
        search_path = self._get_full_path(prefix) if prefix else self.base_path
        if not search_path.exists():
            return []
        
        files = []
        for path in search_path.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.base_path)
                files.append(str(rel_path))
        return files


class S3Storage(StorageBackend):
    """S3/MinIO compatible storage backend."""

    def __init__(self, config: StorageConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
                
                client_kwargs = {
                    "service_name": "s3",
                    "region_name": self.config.region or "us-east-1",
                    "aws_access_key_id": self.config.access_key,
                    "aws_secret_access_key": self.config.secret_key,
                }
                
                # For MinIO or other S3-compatible storage
                if self.config.endpoint_url:
                    client_kwargs["endpoint_url"] = self.config.endpoint_url
                    client_kwargs["config"] = BotoConfig(
                        signature_version="s3v4",
                        s3={"addressing_style": "path"},
                    )
                
                if not self.config.use_ssl and self.config.endpoint_url:
                    # Allow non-SSL for local MinIO
                    client_kwargs["use_ssl"] = False
                
                self._client = boto3.client(**client_kwargs)
            except ImportError:
                raise RuntimeError(
                    "boto3 is required for S3/MinIO storage. "
                    "Install with: pip install boto3"
                )
        
        return self._client

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file to S3/MinIO."""
        try:
            client = self._get_client()
            file_size = os.path.getsize(file_path)
            
            with open(file_path, "rb") as f:
                response = client.put_object(
                    Bucket=self.config.bucket,
                    Key=key,
                    Body=f,
                    ContentType=content_type,
                )
            
            etag = response.get("ETag", "").strip('"')
            
            return StorageResult(
                success=True,
                key=key,
                url=self.get_url(key),
                file_size=file_size,
                etag=etag,
            )
        except Exception as e:
            return StorageResult(
                success=False,
                key=key,
                url="",
                error_message=str(e),
            )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file object to S3/MinIO."""
        try:
            client = self._get_client()
            
            # Get file size
            fileobj.seek(0, 2)
            file_size = fileobj.tell()
            fileobj.seek(0)
            
            response = client.put_object(
                Bucket=self.config.bucket,
                Key=key,
                Body=fileobj,
                ContentType=content_type,
            )
            
            etag = response.get("ETag", "").strip('"')
            
            return StorageResult(
                success=True,
                key=key,
                url=self.get_url(key),
                file_size=file_size,
                etag=etag,
            )
        except Exception as e:
            return StorageResult(
                success=False,
                key=key,
                url="",
                error_message=str(e),
            )

    def download(self, key: str, destination: str) -> bool:
        """Download a file from S3/MinIO."""
        try:
            client = self._get_client()
            client.download_file(self.config.bucket, key, destination)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a file from S3/MinIO."""
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.config.bucket, Key=key)
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if a file exists in S3/MinIO."""
        try:
            client = self._get_client()
            client.head_object(Bucket=self.config.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for a file (presigned URL)."""
        # Use CDN if enabled
        if self.config.cdn_enabled and self.config.cdn_domain:
            return f"https://{self.config.cdn_domain}/{key}"
        
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.config.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            # Fallback to direct URL
            if self.config.endpoint_url:
                return f"{self.config.endpoint_url}/{self.config.bucket}/{key}"
            return f"https://{self.config.bucket}.s3.{self.config.region}.amazonaws.com/{key}"

    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix."""
        try:
            client = self._get_client()
            response = client.list_objects_v2(
                Bucket=self.config.bucket,
                Prefix=prefix,
            )
            
            files = []
            for obj in response.get("Contents", []):
                files.append(obj["Key"])
            return files
        except Exception:
            return []


class Storage:
    """Universal storage interface.
    
    Automatically selects the appropriate backend based on configuration.
    """

    _instance: Optional["Storage"] = None
    _backend: Optional[StorageBackend] = None

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage with configuration.
        
        Args:
            config: Storage configuration (uses settings if not provided)
        """
        if config is None:
            config = StorageConfig(
                backend=settings.STORAGE_BACKEND,
                bucket=settings.STORAGE_BUCKET,
                region=settings.STORAGE_REGION,
                access_key=settings.STORAGE_ACCESS_KEY,
                secret_key=settings.STORAGE_SECRET_KEY,
                endpoint_url=settings.STORAGE_ENDPOINT_URL,
                use_ssl=settings.STORAGE_USE_SSL,
                local_path=settings.LOCAL_STORAGE_PATH,
                cdn_domain=settings.CDN_DOMAIN,
                cdn_enabled=settings.CDN_ENABLED,
            )
        
        self.config = config
        self._backend = self._create_backend(config)

    def _create_backend(self, config: StorageConfig) -> StorageBackend:
        """Create appropriate storage backend."""
        backend_type = config.backend.lower()
        
        if backend_type == "local":
            return LocalStorage(config)
        elif backend_type in ("s3", "minio", "aws"):
            return S3Storage(config)
        else:
            raise ValueError(f"Unsupported storage backend: {backend_type}")

    @classmethod
    def get_instance(cls) -> "Storage":
        """Get singleton storage instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_key(
        self,
        prefix: str,
        filename: str,
        include_date: bool = True,
    ) -> str:
        """Generate a storage key.
        
        Args:
            prefix: Key prefix (e.g., "transcoded", "thumbnails")
            filename: Original filename or identifier
            include_date: Include date in path
            
        Returns:
            Generated key
        """
        if include_date:
            date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
            return f"{prefix}/{date_prefix}/{filename}"
        return f"{prefix}/{filename}"

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file to storage."""
        return self._backend.upload(file_path, key, content_type)

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload a file object to storage."""
        return self._backend.upload_fileobj(fileobj, key, content_type)

    def download(self, key: str, destination: str) -> bool:
        """Download a file from storage."""
        return self._backend.download(key, destination)

    def delete(self, key: str) -> bool:
        """Delete a file from storage."""
        return self._backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        return self._backend.exists(key)

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for a file."""
        return self._backend.get_url(key, expires_in)

    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix."""
        return self._backend.list_files(prefix)


# Convenience function
def get_storage() -> Storage:
    """Get the default storage instance."""
    return Storage.get_instance()


class StorageService:
    """Async-compatible storage service wrapper."""

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize storage service."""
        self._storage = storage or get_storage()

    async def upload_file(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageResult:
        """Upload content to storage.

        Args:
            key: Storage key/path
            content: File content as bytes
            content_type: MIME type

        Returns:
            StorageResult: Upload result
        """
        import io
        fileobj = io.BytesIO(content)
        return self._storage.upload_fileobj(fileobj, key, content_type)

    async def download_file(self, key: str, destination: str) -> bool:
        """Download a file from storage."""
        return self._storage.download(key, destination)

    async def delete_file(self, key: str) -> bool:
        """Delete a file from storage."""
        return self._storage.delete(key)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get URL for a file."""
        return self._storage.get_url(key, expires_in)

    async def exists(self, key: str) -> bool:
        """Check if a file exists."""
        return self._storage.exists(key)


# Global storage service instance
storage_service = StorageService()
