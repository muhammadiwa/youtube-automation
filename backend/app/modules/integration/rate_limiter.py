"""Rate limiting middleware and utilities for API key authentication.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
- 2.1: Check usage against minute/hour/day limits
- 2.2: Return 429 Too Many Requests with Retry-After header when exceeded
- 2.3: Track usage per time window (minute, hour, day) separately
- 2.4: Increment usage counter for all applicable windows
- 2.5: Include rate limit status in response headers (X-RateLimit-Remaining, X-RateLimit-Reset)
"""

import uuid
from datetime import datetime
from typing import Optional, Callable, Dict
from functools import wraps

from fastapi import Request, HTTPException, status, Depends, Response
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.database import get_session
from app.modules.integration.service import APIKeyService
from app.modules.integration.models import APIKey


# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded.
    
    Requirements: 2.2 - Return 429 Too Many Requests with Retry-After header
    """
    
    def __init__(self, limit_type: str, retry_after: int, rate_limit_headers: Optional[Dict[str, str]] = None):
        """Initialize rate limit exceeded exception.
        
        Args:
            limit_type: The type of limit exceeded (minute, hour, day)
            retry_after: Seconds until the rate limit resets
            rate_limit_headers: Optional rate limit headers to include
        """
        headers = {"Retry-After": str(retry_after)}
        if rate_limit_headers:
            headers.update(rate_limit_headers)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded for {limit_type} window",
                "retry_after_seconds": retry_after,
                "limit_type": limit_type,
            },
            headers=headers,
        )


class APIKeyAuth:
    """API Key authentication and rate limiting dependency.
    
    Requirements: 
    - 1.1: Authenticate API requests
    - 2.1: Check usage against minute/hour/day limits
    - 2.2: Return 429 with Retry-After header when exceeded
    - 2.3: Track usage per time window separately
    - 2.4: Increment usage counter for all applicable windows
    - 2.5: Include rate limit status in response headers
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
        
        # Check rate limit (Requirement 2.1)
        if self.check_rate_limit:
            is_allowed, limit_type, retry_after = await service.check_rate_limit(key_obj)
            
            if not is_allowed:
                # Get rate limit headers for the response (Requirement 2.5)
                rate_limit_headers = await get_rate_limit_headers(key_obj, session)
                raise RateLimitExceeded(limit_type, retry_after, rate_limit_headers)
        
        # Record the request (Requirement 2.4)
        await service.record_request(key_obj)
        
        # Store rate limit info in request state for response headers
        request.state.api_key = key_obj
        request.state.api_key_session = session
        
        return key_obj


def require_api_key(
    scope: Optional[str] = None,
    rate_limit: bool = True,
) -> Callable:
    """Decorator to require API key authentication on an endpoint.
    
    Requirements: 
    - 1.4: Scoped permissions
    - 2.1-2.5: Rate limiting
    
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
) -> Dict[str, str]:
    """Get rate limit headers to include in response.
    
    Requirements: 2.5 - Include rate limit status in response headers
    (X-RateLimit-Remaining, X-RateLimit-Reset)
    
    Args:
        api_key: The validated API key
        session: Database session
        
    Returns:
        Dictionary of rate limit headers
    """
    service = APIKeyService(session)
    rate_status = await service.get_rate_limit_status(api_key)
    
    return {
        "X-RateLimit-Limit-Minute": str(rate_status.minute_limit),
        "X-RateLimit-Remaining-Minute": str(rate_status.minute_remaining),
        "X-RateLimit-Limit-Hour": str(rate_status.hour_limit),
        "X-RateLimit-Remaining-Hour": str(rate_status.hour_remaining),
        "X-RateLimit-Limit-Day": str(rate_status.day_limit),
        "X-RateLimit-Remaining-Day": str(rate_status.day_remaining),
        "X-RateLimit-Reset": rate_status.reset_at.isoformat(),
    }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to all API key authenticated responses.
    
    Requirements: 2.5 - Include rate limit status in response headers
    
    This middleware checks if the request was authenticated with an API key
    and adds rate limit headers to the response.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add rate limit headers to response.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler
            
        Returns:
            Response with rate limit headers if applicable
        """
        response = await call_next(request)
        
        # Check if request was authenticated with API key
        if hasattr(request.state, 'api_key') and hasattr(request.state, 'api_key_session'):
            try:
                headers = await get_rate_limit_headers(
                    request.state.api_key,
                    request.state.api_key_session
                )
                for key, value in headers.items():
                    response.headers[key] = value
            except Exception:
                # Don't fail the request if we can't add headers
                pass
        
        return response


def add_rate_limit_headers_to_response(
    response: Response,
    rate_limit_headers: Dict[str, str]
) -> Response:
    """Add rate limit headers to a response object.
    
    Requirements: 2.5 - Include rate limit status in response headers
    
    Args:
        response: The response object to modify
        rate_limit_headers: Dictionary of rate limit headers
        
    Returns:
        The modified response with headers added
    """
    for key, value in rate_limit_headers.items():
        response.headers[key] = value
    return response
