"""Rate limiting middleware and utilities for API key authentication.

Requirements: 29.2 - Per-key rate limits, reject exceeded requests
"""

import uuid
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.integration.service import APIKeyService
from app.modules.integration.models import APIKey


# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded.
    
    Requirements: 29.2 - Reject exceeded requests
    """
    
    def __init__(self, limit_type: str, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded for {limit_type}",
                "retry_after_seconds": retry_after,
                "limit_type": limit_type,
            },
            headers={"Retry-After": str(retry_after)},
        )


class APIKeyAuth:
    """API Key authentication and rate limiting dependency.
    
    Requirements: 29.1 - Authenticate API requests
    Requirements: 29.2 - Rate limiting per key
    """
    
    def __init__(
        self,
        required_scope: Optional[str] = None,
        check_rate_limit: bool = True,
    ):
        self.required_scope = required_scope
        self.check_rate_limit = check_rate_limit
    
    async def __call__(
        self,
        request: Request,
        api_key: Optional[str] = Depends(api_key_header),
        session: AsyncSession = Depends(get_session),
    ) -> APIKey:
        """Validate API key and check rate limits.
        
        Returns the validated APIKey object.
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        service = APIKeyService(session)
        
        # Get client IP
        client_ip = None
        if request.client:
            client_ip = request.client.host
        
        # Validate key
        is_valid, key_obj, error = await service.validate_api_key(
            api_key, self.required_scope, client_ip
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error or "Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Check rate limit
        if self.check_rate_limit:
            is_allowed, limit_type, retry_after = await service.check_rate_limit(key_obj)
            
            if not is_allowed:
                raise RateLimitExceeded(limit_type, retry_after)
        
        # Record the request
        await service.record_request(key_obj)
        
        return key_obj


def require_api_key(
    scope: Optional[str] = None,
    rate_limit: bool = True,
) -> Callable:
    """Decorator to require API key authentication on an endpoint.
    
    Requirements: 29.1 - Scoped permissions
    Requirements: 29.2 - Rate limiting
    
    Usage:
        @router.get("/protected")
        @require_api_key(scope="read:videos")
        async def protected_endpoint(api_key: APIKey = Depends()):
            ...
    """
    return Depends(APIKeyAuth(required_scope=scope, check_rate_limit=rate_limit))


# Pre-configured dependencies for common scopes
require_read_accounts = APIKeyAuth(required_scope="read:accounts")
require_read_videos = APIKeyAuth(required_scope="read:videos")
require_read_streams = APIKeyAuth(required_scope="read:streams")
require_read_analytics = APIKeyAuth(required_scope="read:analytics")
require_read_comments = APIKeyAuth(required_scope="read:comments")
require_write_videos = APIKeyAuth(required_scope="write:videos")
require_write_streams = APIKeyAuth(required_scope="write:streams")
require_write_comments = APIKeyAuth(required_scope="write:comments")
require_admin_accounts = APIKeyAuth(required_scope="admin:accounts")
require_admin_webhooks = APIKeyAuth(required_scope="admin:webhooks")
require_full_access = APIKeyAuth(required_scope="*")


async def get_rate_limit_headers(
    api_key: APIKey,
    session: AsyncSession,
) -> dict[str, str]:
    """Get rate limit headers to include in response.
    
    Requirements: 29.2 - Rate limit information
    """
    service = APIKeyService(session)
    status = await service.get_rate_limit_status(api_key)
    
    return {
        "X-RateLimit-Limit-Minute": str(status.minute_limit),
        "X-RateLimit-Remaining-Minute": str(status.minute_remaining),
        "X-RateLimit-Limit-Hour": str(status.hour_limit),
        "X-RateLimit-Remaining-Hour": str(status.hour_remaining),
        "X-RateLimit-Limit-Day": str(status.day_limit),
        "X-RateLimit-Remaining-Day": str(status.day_remaining),
        "X-RateLimit-Reset": status.reset_at.isoformat(),
    }
