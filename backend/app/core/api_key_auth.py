"""API Key Authentication Middleware.

Provides authentication middleware for external applications using API keys.

Requirements: 1.1, 1.2, 1.3, 1.5, 1.6
- 1.1: Validate API key against stored hash
- 1.2: Allow request to proceed with user context when valid
- 1.3: Return 401 Unauthorized for invalid/revoked/expired keys
- 1.5: Verify client IP is in allowed list
- 1.6: Update last_used_at timestamp after successful authentication
"""

import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow, ensure_utc
from app.modules.integration.models import APIKey
from app.modules.integration.repository import APIKeyRepository
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository


class APIKeyAuthError:
    """Error codes for API key authentication failures."""
    INVALID_KEY = "INVALID_API_KEY"
    KEY_REVOKED = "API_KEY_REVOKED"
    KEY_EXPIRED = "API_KEY_EXPIRED"
    KEY_INACTIVE = "API_KEY_INACTIVE"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    IP_NOT_ALLOWED = "IP_NOT_ALLOWED"


class APIKeyAuthMiddleware:
    """Middleware for API key authentication from external applications.
    
    This middleware validates API keys and provides user context for authenticated requests.
    
    Requirements:
    - 1.1: WHEN an external request includes X-API-Key header, THE Integration_Service 
           SHALL validate the key against stored hash
    - 1.2: WHEN the API key is valid and active, THE Integration_Service SHALL allow 
           the request to proceed with user context
    - 1.3: WHEN the API key is invalid, revoked, or expired, THE Integration_Service 
           SHALL return 401 Unauthorized with descriptive error
    - 1.5: WHEN the API key has IP restrictions, THE Integration_Service SHALL verify 
           client IP is in allowed list
    - 1.6: THE Integration_Service SHALL update last_used_at timestamp after successful 
           authentication
    """

    def __init__(self, session: AsyncSession):
        """Initialize the middleware with a database session.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        self.key_repo = APIKeyRepository(session)
        self.user_repo = UserRepository(session)

    async def authenticate(
        self,
        api_key: str,
        required_scope: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> Tuple[bool, Optional[User], Optional[str], Optional[str]]:
        """Validate API key and return user context.
        
        This method performs the following validations:
        1. Hash comparison to verify key authenticity (Requirement 1.1)
        2. Check if key is active and not revoked (Requirement 1.3)
        3. Check if key has expired (Requirement 1.3)
        4. Verify client IP is allowed if restrictions exist (Requirement 1.5)
        5. Verify required scope if specified (Requirement 1.4)
        6. Update last_used_at on successful auth (Requirement 1.6)
        
        Args:
            api_key: The API key string from X-API-Key header
            required_scope: Optional scope required for the endpoint
            client_ip: Optional client IP address for IP restriction check
            
        Returns:
            Tuple of (is_valid, user, error_message, error_code)
            - is_valid: True if authentication succeeded
            - user: User object if authentication succeeded, None otherwise
            - error_message: Human-readable error message if failed
            - error_code: Error code constant if failed
        """
        # Step 1: Hash the key and look it up (Requirement 1.1)
        key_hash = APIKey.hash_key(api_key)
        key_obj = await self.key_repo.get_by_hash(key_hash)
        
        if not key_obj:
            return False, None, "Invalid API key", APIKeyAuthError.INVALID_KEY
        
        # Step 2: Check if key is active (Requirement 1.3)
        if not key_obj.is_active:
            return False, None, "API key is inactive", APIKeyAuthError.KEY_INACTIVE
        
        # Step 3: Check if key is revoked (Requirement 1.3)
        if key_obj.revoked_at:
            return False, None, "API key has been revoked", APIKeyAuthError.KEY_REVOKED
        
        # Step 4: Check if key has expired (Requirement 1.3)
        if key_obj.expires_at:
            if utcnow() > ensure_utc(key_obj.expires_at):
                return False, None, "API key has expired", APIKeyAuthError.KEY_EXPIRED
        
        # Step 5: Check IP restriction (Requirement 1.5)
        if client_ip and not key_obj.is_ip_allowed(client_ip):
            return (
                False, 
                None, 
                f"IP address {client_ip} is not allowed for this API key", 
                APIKeyAuthError.IP_NOT_ALLOWED
            )
        
        # Step 6: Check scope if required (Requirement 1.4)
        if required_scope and not key_obj.has_scope(required_scope):
            return (
                False, 
                None, 
                f"API key lacks required scope: {required_scope}", 
                APIKeyAuthError.INSUFFICIENT_SCOPE
            )
        
        # Step 7: Get user context (Requirement 1.2)
        user = await self.user_repo.get_by_id(key_obj.user_id)
        if not user:
            return False, None, "User not found for API key", APIKeyAuthError.INVALID_KEY
        
        if not user.is_active:
            return False, None, "User account is inactive", APIKeyAuthError.INVALID_KEY
        
        # Step 8: Update last_used_at (Requirement 1.6)
        await self._update_last_used(key_obj)
        
        return True, user, None, None

    async def _update_last_used(self, api_key: APIKey) -> None:
        """Update the last_used_at timestamp for an API key.
        
        Requirement 1.6: THE Integration_Service SHALL update last_used_at 
        timestamp after successful authentication
        
        Args:
            api_key: The API key to update
        """
        await self.key_repo.record_usage(api_key.id)

    async def validate_key_only(
        self,
        api_key: str,
    ) -> Tuple[bool, Optional[APIKey], Optional[str], Optional[str]]:
        """Validate API key without getting user context.
        
        Useful for rate limiting checks where full user context isn't needed.
        
        Args:
            api_key: The API key string
            
        Returns:
            Tuple of (is_valid, api_key_obj, error_message, error_code)
        """
        key_hash = APIKey.hash_key(api_key)
        key_obj = await self.key_repo.get_by_hash(key_hash)
        
        if not key_obj:
            return False, None, "Invalid API key", APIKeyAuthError.INVALID_KEY
        
        if not key_obj.is_active:
            return False, key_obj, "API key is inactive", APIKeyAuthError.KEY_INACTIVE
        
        if key_obj.revoked_at:
            return False, key_obj, "API key has been revoked", APIKeyAuthError.KEY_REVOKED
        
        if key_obj.expires_at:
            if utcnow() > ensure_utc(key_obj.expires_at):
                return False, key_obj, "API key has expired", APIKeyAuthError.KEY_EXPIRED
        
        return True, key_obj, None, None

    def verify_scope(
        self,
        api_key: APIKey,
        required_scope: str
    ) -> Tuple[bool, Optional[str]]:
        """Verify that an API key has the required scope.
        
        Requirement 1.4: WHEN the API key lacks required scope for an endpoint, 
        THE Integration_Service SHALL return 403 Forbidden
        
        Args:
            api_key: The validated API key object
            required_scope: The scope required for the endpoint
            
        Returns:
            Tuple of (has_scope, error_message)
        """
        if api_key.has_scope(required_scope):
            return True, None
        return False, f"API key lacks required scope: {required_scope}"

    def verify_ip(
        self,
        api_key: APIKey,
        client_ip: str
    ) -> Tuple[bool, Optional[str]]:
        """Verify that the client IP is allowed for the API key.
        
        Requirement 1.5: WHEN the API key has IP restrictions, THE Integration_Service 
        SHALL verify client IP is in allowed list
        
        Args:
            api_key: The validated API key object
            client_ip: The client's IP address
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if api_key.is_ip_allowed(client_ip):
            return True, None
        return False, f"IP address {client_ip} is not allowed for this API key"
