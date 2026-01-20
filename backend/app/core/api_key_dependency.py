"""FastAPI Dependencies for API Key Authentication.

Provides FastAPI dependencies and decorators for API key authentication with
support for JWT fallback and scope-based access control.

Requirements: 1.4, 8.1, 8.2, 8.3, 8.4, 8.5
- 1.4: Return 403 Forbidden when API key lacks required scope
- 8.1: Require read:accounts or write:accounts for /accounts endpoints
- 8.2: Require read:videos or write:videos for /videos endpoints
- 8.3: Require read:streams or write:streams for /streams endpoints
- 8.4: Require read:analytics for /analytics endpoints
- 8.5: Allow full_access (*) scope to access all endpoints
"""

import uuid
from functools import wraps
from typing import Optional, Callable, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.api_key_auth import APIKeyAuthMiddleware, APIKeyAuthError
from app.modules.auth.models import User
from app.modules.auth.jwt import validate_token
from app.modules.auth.repository import UserRepository
from app.modules.integration.models import APIKey, APIKeyScope


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Container for authenticated user with auth method info."""
    
    def __init__(
        self,
        user: User,
        auth_method: str,
        api_key: Optional[APIKey] = None
    ):
        """Initialize authenticated user container.
        
        Args:
            user: The authenticated User object
            auth_method: Either "api_key" or "jwt"
            api_key: The APIKey object if authenticated via API key
        """
        self.user = user
        self.auth_method = auth_method
        self.api_key = api_key
    
    @property
    def user_id(self) -> uuid.UUID:
        """Get the user ID."""
        return self.user.id
    
    @property
    def is_api_key_auth(self) -> bool:
        """Check if authenticated via API key."""
        return self.auth_method == "api_key"
    
    @property
    def is_jwt_auth(self) -> bool:
        """Check if authenticated via JWT."""
        return self.auth_method == "jwt"


async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = Depends(api_key_header),
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    """FastAPI dependency to get authenticated user from API key or JWT.
    
    This dependency supports both API key and JWT authentication with fallback:
    1. If X-API-Key header is present, authenticate via API key
    2. If Authorization Bearer token is present, authenticate via JWT
    3. If neither is present, return 401 Unauthorized
    
    Requirements:
    - 1.2: Allow request to proceed with user context when valid
    - 1.3: Return 401 Unauthorized for invalid/revoked/expired keys
    
    Args:
        request: FastAPI Request object
        x_api_key: API key from X-API-Key header
        bearer_credentials: JWT token from Authorization header
        session: Database session
        
    Returns:
        AuthenticatedUser: Container with user and auth method info
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Try API key authentication first
    if x_api_key:
        return await _authenticate_with_api_key(request, x_api_key, session)
    
    # Fall back to JWT authentication
    if bearer_credentials:
        return await _authenticate_with_jwt(bearer_credentials.credentials, session)
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-API-Key header or Authorization Bearer token.",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


async def _authenticate_with_api_key(
    request: Request,
    api_key: str,
    session: AsyncSession,
) -> AuthenticatedUser:
    """Authenticate using API key.
    
    Args:
        request: FastAPI Request object
        api_key: The API key string
        session: Database session
        
    Returns:
        AuthenticatedUser with api_key auth method
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Get client IP
    client_ip = None
    if request.client:
        client_ip = request.client.host
    
    middleware = APIKeyAuthMiddleware(session)
    is_valid, user, error_msg, error_code = await middleware.authenticate(
        api_key=api_key,
        client_ip=client_ip
    )
    
    if not is_valid:
        status_code = status.HTTP_401_UNAUTHORIZED
        if error_code == APIKeyAuthError.INSUFFICIENT_SCOPE:
            status_code = status.HTTP_403_FORBIDDEN
        elif error_code == APIKeyAuthError.IP_NOT_ALLOWED:
            status_code = status.HTTP_403_FORBIDDEN
        
        raise HTTPException(
            status_code=status_code,
            detail=error_msg or "Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get the API key object for scope checking
    key_hash = APIKey.hash_key(api_key)
    from app.modules.integration.repository import APIKeyRepository
    key_repo = APIKeyRepository(session)
    api_key_obj = await key_repo.get_by_hash(key_hash)
    
    return AuthenticatedUser(user=user, auth_method="api_key", api_key=api_key_obj)


async def _authenticate_with_jwt(
    token: str,
    session: AsyncSession,
) -> AuthenticatedUser:
    """Authenticate using JWT token.
    
    Args:
        token: The JWT token string
        session: Database session
        
    Returns:
        AuthenticatedUser with jwt auth method
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    payload = validate_token(token, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = uuid.UUID(payload.sub)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthenticatedUser(user=user, auth_method="jwt")


def require_scope(scope: str):
    """Decorator/dependency factory for scope-based access control.
    
    Creates a FastAPI dependency that validates the authenticated user
    has the required scope. Works with both API key and JWT authentication.
    
    For JWT authentication, all scopes are allowed (JWT users have full access).
    For API key authentication, the key must have the required scope or full_access (*).
    
    Requirements:
    - 1.4: Return 403 Forbidden when API key lacks required scope
    - 8.1-8.4: Scope requirements for different endpoints
    - 8.5: Allow full_access (*) scope to access all endpoints
    
    Args:
        scope: The required scope (e.g., "read:videos", "write:streams")
        
    Returns:
        FastAPI dependency function
        
    Usage:
        @router.get("/videos")
        async def list_videos(
            auth: AuthenticatedUser = Depends(require_scope("read:videos"))
        ):
            ...
    """
    async def scope_dependency(
        request: Request,
        x_api_key: Optional[str] = Depends(api_key_header),
        bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        session: AsyncSession = Depends(get_session),
    ) -> AuthenticatedUser:
        # First authenticate the user
        auth_user = await get_api_key_user(request, x_api_key, bearer_credentials, session)
        
        # JWT users have full access
        if auth_user.is_jwt_auth:
            return auth_user
        
        # Check API key scope
        if auth_user.api_key:
            # Check for full access scope (Requirement 8.5)
            if auth_user.api_key.has_scope(APIKeyScope.FULL_ACCESS.value):
                return auth_user
            
            # Check for specific scope
            if auth_user.api_key.has_scope(scope):
                return auth_user
            
            # Scope not found - return 403 (Requirement 1.4)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key lacks required scope: {scope}",
            )
        
        # Should not reach here, but handle gracefully
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    return scope_dependency


# Pre-configured scope dependencies for common use cases
# Requirements 8.1-8.5

def require_read_accounts():
    """Require read:accounts scope. (Requirement 8.1)"""
    return require_scope("read:accounts")

def require_write_accounts():
    """Require write:accounts scope. (Requirement 8.1)"""
    return require_scope("write:accounts")

def require_read_videos():
    """Require read:videos scope. (Requirement 8.2)"""
    return require_scope("read:videos")

def require_write_videos():
    """Require write:videos scope. (Requirement 8.2)"""
    return require_scope("write:videos")

def require_read_streams():
    """Require read:streams scope. (Requirement 8.3)"""
    return require_scope("read:streams")

def require_write_streams():
    """Require write:streams scope. (Requirement 8.3)"""
    return require_scope("write:streams")

def require_read_analytics():
    """Require read:analytics scope. (Requirement 8.4)"""
    return require_scope("read:analytics")

def require_read_comments():
    """Require read:comments scope."""
    return require_scope("read:comments")

def require_write_comments():
    """Require write:comments scope."""
    return require_scope("write:comments")

def require_admin_accounts():
    """Require admin:accounts scope."""
    return require_scope("admin:accounts")

def require_admin_webhooks():
    """Require admin:webhooks scope."""
    return require_scope("admin:webhooks")


class ScopeChecker:
    """Utility class for checking scopes on API keys.
    
    Provides methods to check if an API key has specific scopes,
    useful for conditional logic within endpoints.
    """
    
    @staticmethod
    def has_scope(auth_user: AuthenticatedUser, scope: str) -> bool:
        """Check if authenticated user has a specific scope.
        
        JWT users always return True (full access).
        API key users are checked against their scope list.
        
        Args:
            auth_user: The authenticated user container
            scope: The scope to check
            
        Returns:
            True if user has the scope, False otherwise
        """
        if auth_user.is_jwt_auth:
            return True
        
        if auth_user.api_key:
            return auth_user.api_key.has_scope(scope)
        
        return False
    
    @staticmethod
    def has_any_scope(auth_user: AuthenticatedUser, scopes: list[str]) -> bool:
        """Check if authenticated user has any of the specified scopes.
        
        Args:
            auth_user: The authenticated user container
            scopes: List of scopes to check
            
        Returns:
            True if user has any of the scopes, False otherwise
        """
        if auth_user.is_jwt_auth:
            return True
        
        if auth_user.api_key:
            return any(auth_user.api_key.has_scope(s) for s in scopes)
        
        return False
    
    @staticmethod
    def has_all_scopes(auth_user: AuthenticatedUser, scopes: list[str]) -> bool:
        """Check if authenticated user has all of the specified scopes.
        
        Args:
            auth_user: The authenticated user container
            scopes: List of scopes to check
            
        Returns:
            True if user has all scopes, False otherwise
        """
        if auth_user.is_jwt_auth:
            return True
        
        if auth_user.api_key:
            return all(auth_user.api_key.has_scope(s) for s in scopes)
        
        return False
