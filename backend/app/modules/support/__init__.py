"""User Support module for customer support ticket management.

This module provides endpoints for users to:
- Create support tickets
- View their tickets and messages
- Reply to tickets
- Get ticket statistics
"""

from app.modules.support.router import router as support_router

__all__ = ["support_router"]
