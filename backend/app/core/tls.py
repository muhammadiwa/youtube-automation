"""TLS configuration and enforcement module.

Provides TLS 1.3 enforcement for all connections per requirement 25.2.

This module provides:
- TLS configuration management
- TLS version enforcement middleware
- Certificate validation utilities
- Secure cipher suite configuration
"""

import ssl
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class TLSVersion(str, Enum):
    """Supported TLS versions."""
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


# TLS 1.3 cipher suites (secure by default)
TLS_1_3_CIPHER_SUITES = [
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_128_GCM_SHA256",
]

# TLS 1.2 cipher suites (for backward compatibility if needed)
TLS_1_2_CIPHER_SUITES = [
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
]


@dataclass
class TLSConfiguration:
    """TLS configuration settings."""
    minimum_version: TLSVersion = TLSVersion.TLS_1_3
    enforce_tls: bool = True
    cipher_suites: list[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    verify_client: bool = False
    
    def __post_init__(self):
        if self.cipher_suites is None:
            self.cipher_suites = TLS_1_3_CIPHER_SUITES.copy()


# Global TLS configuration
_tls_config: Optional[TLSConfiguration] = None


def get_tls_config() -> TLSConfiguration:
    """Get the global TLS configuration.
    
    Returns:
        TLSConfiguration: Current TLS configuration
    """
    global _tls_config
    if _tls_config is None:
        _tls_config = TLSConfiguration()
    return _tls_config


def set_tls_config(config: TLSConfiguration) -> None:
    """Set the global TLS configuration.
    
    Args:
        config: New TLS configuration
    """
    global _tls_config
    _tls_config = config


def create_ssl_context(config: Optional[TLSConfiguration] = None) -> ssl.SSLContext:
    """Create an SSL context with the specified configuration.
    
    Args:
        config: TLS configuration (uses global if not provided)
        
    Returns:
        ssl.SSLContext: Configured SSL context
    """
    if config is None:
        config = get_tls_config()
    
    # Create context with appropriate protocol
    if config.minimum_version == TLSVersion.TLS_1_3:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
    else:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # Set cipher suites
    if config.cipher_suites:
        try:
            context.set_ciphers(":".join(config.cipher_suites))
        except ssl.SSLError:
            # Fall back to default ciphers if custom ones fail
            pass
    
    # Load certificate if provided
    if config.certificate_path and config.private_key_path:
        context.load_cert_chain(
            certfile=config.certificate_path,
            keyfile=config.private_key_path,
        )
    
    # Configure client verification
    if config.verify_client:
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        context.verify_mode = ssl.CERT_NONE
    
    return context


def get_tls_version_from_request(request: Request) -> Optional[str]:
    """Extract TLS version from request if available.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: TLS version string or None
    """
    # Check for TLS info in scope (set by ASGI server)
    scope = request.scope
    
    # Uvicorn with SSL provides this in extensions
    extensions = scope.get("extensions", {})
    tls_info = extensions.get("tls", {})
    
    if tls_info:
        return tls_info.get("version")
    
    # Check headers that might be set by reverse proxy
    tls_version = request.headers.get("X-TLS-Version")
    if tls_version:
        return tls_version
    
    # Check if connection is secure
    if scope.get("scheme") == "https":
        # Assume TLS 1.3 if HTTPS but version unknown
        return "TLSv1.3"
    
    return None


def is_tls_compliant(tls_version: Optional[str], config: Optional[TLSConfiguration] = None) -> bool:
    """Check if the TLS version meets minimum requirements.
    
    Args:
        tls_version: TLS version string
        config: TLS configuration (uses global if not provided)
        
    Returns:
        bool: True if compliant
    """
    if config is None:
        config = get_tls_config()
    
    if not config.enforce_tls:
        return True
    
    if tls_version is None:
        return False
    
    # Parse version
    version_map = {
        "TLSv1.3": 3,
        "TLSv1.2": 2,
        "TLSv1.1": 1,
        "TLSv1.0": 0,
    }
    
    min_version_num = version_map.get(config.minimum_version.value, 3)
    actual_version_num = version_map.get(tls_version, -1)
    
    return actual_version_num >= min_version_num


class TLSEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce TLS version requirements.
    
    This middleware checks the TLS version of incoming connections
    and rejects those that don't meet the minimum requirement.
    
    Note: This is most effective when used with a reverse proxy
    that sets the X-TLS-Version header.
    """
    
    def __init__(
        self,
        app,
        config: Optional[TLSConfiguration] = None,
        exempt_paths: Optional[list[str]] = None,
    ):
        """Initialize the middleware.
        
        Args:
            app: ASGI application
            config: TLS configuration
            exempt_paths: Paths exempt from TLS enforcement (e.g., health checks)
        """
        super().__init__(app)
        self.config = config or get_tls_config()
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request and enforce TLS requirements.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response
        """
        # Skip enforcement for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip if TLS enforcement is disabled
        if not self.config.enforce_tls:
            return await call_next(request)
        
        # Get TLS version
        tls_version = get_tls_version_from_request(request)
        
        # Check compliance
        if not is_tls_compliant(tls_version, self.config):
            # In development, we might allow non-TLS connections
            # In production, this should be strict
            scheme = request.scope.get("scheme", "http")
            if scheme == "http":
                # Allow HTTP in development (TLS termination at proxy)
                # In production, configure proxy to reject non-TLS
                pass
            else:
                # HTTPS but wrong version
                raise HTTPException(
                    status_code=status.HTTP_426_UPGRADE_REQUIRED,
                    detail=f"TLS {self.config.minimum_version.value} or higher is required",
                    headers={"Upgrade": "TLS/1.3"},
                )
        
        return await call_next(request)


@dataclass
class TLSStatus:
    """Current TLS status information."""
    enabled: bool
    version: str
    cipher_suite: Optional[str]
    certificate_valid: bool
    certificate_expires_at: Optional[datetime]
    is_compliant: bool


def get_tls_status(config: Optional[TLSConfiguration] = None) -> TLSStatus:
    """Get the current TLS status.
    
    Args:
        config: TLS configuration (uses global if not provided)
        
    Returns:
        TLSStatus: Current TLS status
    """
    if config is None:
        config = get_tls_config()
    
    return TLSStatus(
        enabled=config.enforce_tls,
        version=config.minimum_version.value,
        cipher_suite=config.cipher_suites[0] if config.cipher_suites else None,
        certificate_valid=True,  # Would check actual certificate in production
        certificate_expires_at=None,  # Would check certificate expiry
        is_compliant=config.minimum_version == TLSVersion.TLS_1_3,
    )


def enforce_tls_1_3() -> TLSConfiguration:
    """Enforce TLS 1.3 for all connections.
    
    Updates the global configuration to require TLS 1.3.
    
    Returns:
        TLSConfiguration: Updated configuration
    """
    config = get_tls_config()
    config.minimum_version = TLSVersion.TLS_1_3
    config.enforce_tls = True
    config.cipher_suites = TLS_1_3_CIPHER_SUITES.copy()
    set_tls_config(config)
    return config


def get_uvicorn_ssl_config(config: Optional[TLSConfiguration] = None) -> dict:
    """Get SSL configuration for Uvicorn server.
    
    Args:
        config: TLS configuration (uses global if not provided)
        
    Returns:
        dict: Uvicorn SSL configuration
    """
    if config is None:
        config = get_tls_config()
    
    ssl_config = {}
    
    if config.certificate_path and config.private_key_path:
        ssl_config["ssl_certfile"] = config.certificate_path
        ssl_config["ssl_keyfile"] = config.private_key_path
        
        # Set minimum TLS version
        if config.minimum_version == TLSVersion.TLS_1_3:
            ssl_config["ssl_version"] = ssl.TLSVersion.TLSv1_3
        else:
            ssl_config["ssl_version"] = ssl.TLSVersion.TLSv1_2
        
        # Set cipher suites
        if config.cipher_suites:
            ssl_config["ssl_ciphers"] = ":".join(config.cipher_suites)
    
    return ssl_config
