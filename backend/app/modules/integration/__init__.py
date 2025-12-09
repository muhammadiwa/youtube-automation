"""Integration module for API key management and webhooks.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""

from app.modules.integration.router import router as integration_router

__all__ = ["integration_router"]
