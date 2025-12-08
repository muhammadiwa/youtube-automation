"""Monitoring models for layout preferences.

Implements user preferences for monitoring dashboard layout.
Requirements: 16.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class MonitoringLayoutPreference(Base):
    """User preferences for monitoring dashboard layout.
    
    Requirements: 16.5
    """

    __tablename__ = "monitoring_layout_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Grid layout settings
    grid_columns: Mapped[int] = mapped_column(Integer, default=4)
    grid_rows: Mapped[int] = mapped_column(Integer, default=3)
    
    # Display settings
    show_metrics: Mapped[list] = mapped_column(
        JSON, default=["subscribers", "views", "status", "quota"]
    )
    sort_by: Mapped[str] = mapped_column(String(50), default="status")
    sort_order: Mapped[str] = mapped_column(String(10), default="asc")
    default_filter: Mapped[str] = mapped_column(String(50), default="all")
    compact_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    show_issues_only: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<MonitoringLayoutPreference(user_id={self.user_id}, grid={self.grid_columns}x{self.grid_rows})>"
