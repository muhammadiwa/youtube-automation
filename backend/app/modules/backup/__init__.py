"""Backup module for data backup, export, and import.

Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

from app.modules.backup.router import router as backup_router

__all__ = ["backup_router"]
