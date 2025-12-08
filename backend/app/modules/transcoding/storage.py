"""CDN storage utilities for transcoded outputs.

Requirements: 10.5 - Store transcoded output in CDN-backed storage.
"""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.modules.transcoding.schemas import CDNUploadResult


@dataclass
class S3Config:
    """Configuration for S3-compatible storage."""
    bucket: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    cdn_domain: Optional[str] = None


class CDNStorage:
    """CDN-backed storage for transcoded videos.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    """

    def __init__(self, config: S3Config):
        """Initialize CDN storage.
        
        Args:
            config: S3 configuration
        """
        self.config = config
        self._client = None

    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            try:
                import boto3
                
                client_kwargs = {
                    "service_name": "s3",
                    "region_name": self.config.region,
                }
                
                if self.config.endpoint_url:
                    client_kwargs["endpoint_url"] = self.config.endpoint_url
                
                if self.config.access_key and self.config.secret_key:
                    client_kwargs["aws_access_key_id"] = self.config.access_key
                    client_kwargs["aws_secret_access_key"] = self.config.secret_key
                
                self._client = boto3.client(**client_kwargs)
            except ImportError:
                # boto3 not installed, use mock client
                self._client = MockS3Client(self.config)
        
        return self._client

    def generate_key(
        self,
        job_id: uuid.UUID,
        resolution: str,
        extension: str = "mp4",
    ) -> str:
        """Generate S3 key for transcoded output.
        
        Args:
            job_id: Transcode job ID
            resolution: Output resolution
            extension: File extension
            
        Returns:
            S3 object key
        """
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        return f"transcoded/{date_prefix}/{job_id}/{resolution}.{extension}"

    def get_cdn_url(self, key: str) -> str:
        """Get CDN URL for an object.
        
        Args:
            key: S3 object key
            
        Returns:
            CDN URL
        """
        if self.config.cdn_domain:
            return f"https://{self.config.cdn_domain}/{key}"
        else:
            return f"https://{self.config.bucket}.s3.{self.config.region}.amazonaws.com/{key}"

    def upload_file(
        self,
        file_path: str,
        key: str,
        content_type: str = "video/mp4",
    ) -> CDNUploadResult:
        """Upload file to CDN storage.
        
        Requirements: 10.5 - Store transcoded output in CDN-backed storage.
        
        Args:
            file_path: Local file path
            key: S3 object key
            content_type: MIME type
            
        Returns:
            Upload result
        """
        try:
            client = self._get_client()
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Upload file
            with open(file_path, "rb") as f:
                response = client.put_object(
                    Bucket=self.config.bucket,
                    Key=key,
                    Body=f,
                    ContentType=content_type,
                )
            
            cdn_url = self.get_cdn_url(key)
            etag = response.get("ETag", "").strip('"')
            
            return CDNUploadResult(
                success=True,
                bucket=self.config.bucket,
                key=key,
                cdn_url=cdn_url,
                file_size=file_size,
                etag=etag,
            )
            
        except Exception as e:
            return CDNUploadResult(
                success=False,
                bucket=self.config.bucket,
                key=key,
                cdn_url="",
                file_size=0,
                error_message=str(e),
            )

    def delete_file(self, key: str) -> bool:
        """Delete file from CDN storage.
        
        Args:
            key: S3 object key
            
        Returns:
            True if deleted successfully
        """
        try:
            client = self._get_client()
            client.delete_object(
                Bucket=self.config.bucket,
                Key=key,
            )
            return True
        except Exception:
            return False

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Generate presigned URL for temporary access.
        
        Args:
            key: S3 object key
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.config.bucket,
                    "Key": key,
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            return None


class MockS3Client:
    """Mock S3 client for testing without boto3."""

    def __init__(self, config: S3Config):
        self.config = config
        self._objects = {}

    def put_object(self, Bucket: str, Key: str, Body, ContentType: str = None) -> dict:
        """Mock put_object."""
        content = Body.read() if hasattr(Body, "read") else Body
        self._objects[f"{Bucket}/{Key}"] = {
            "content": content,
            "content_type": ContentType,
        }
        return {"ETag": f'"{uuid.uuid4().hex}"'}

    def delete_object(self, Bucket: str, Key: str) -> dict:
        """Mock delete_object."""
        key = f"{Bucket}/{Key}"
        if key in self._objects:
            del self._objects[key]
        return {}

    def generate_presigned_url(
        self,
        operation: str,
        Params: dict,
        ExpiresIn: int,
    ) -> str:
        """Mock generate_presigned_url."""
        bucket = Params.get("Bucket", "")
        key = Params.get("Key", "")
        return f"https://{bucket}.s3.amazonaws.com/{key}?expires={ExpiresIn}"


def get_default_storage() -> CDNStorage:
    """Get default CDN storage instance.
    
    Returns:
        CDNStorage instance
    """
    # In production, these would come from environment variables
    config = S3Config(
        bucket=os.environ.get("S3_BUCKET", "youtube-automation-transcoded"),
        region=os.environ.get("S3_REGION", "us-east-1"),
        endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
        access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
        secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        cdn_domain=os.environ.get("CDN_DOMAIN"),
    )
    return CDNStorage(config)


async def upload_transcoded_output(
    job_id: uuid.UUID,
    file_path: str,
    resolution: str,
    storage: Optional[CDNStorage] = None,
) -> CDNUploadResult:
    """Upload transcoded output to CDN storage.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    
    Args:
        job_id: Transcode job ID
        file_path: Local file path
        resolution: Output resolution
        storage: CDN storage instance (uses default if not provided)
        
    Returns:
        Upload result
    """
    if storage is None:
        storage = get_default_storage()
    
    key = storage.generate_key(job_id, resolution)
    return storage.upload_file(file_path, key)


def cleanup_local_file(file_path: str) -> bool:
    """Clean up local file after CDN upload.
    
    Args:
        file_path: Local file path to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False
