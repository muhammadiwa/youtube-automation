"""AI Logs model for tracking AI API usage.

Requirements: 13.1, 13.3 - AI Service Management

Revision ID: 036_ai_logs_model
Revises: 035_support_communication_models
Create Date: 2024-12-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "036_ai_logs_model"
down_revision = "035_support_communication_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ai_logs table."""
    op.create_table(
        "ai_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Request details
        sa.Column("feature", sa.String(50), nullable=False, index=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("request_summary", sa.Text, nullable=True),
        sa.Column("response_summary", sa.Text, nullable=True),
        # Token usage
        sa.Column("tokens_input", sa.Integer, nullable=False, default=0),
        sa.Column("tokens_output", sa.Integer, nullable=False, default=0),
        sa.Column("total_tokens", sa.Integer, nullable=False, default=0),
        # Performance metrics
        sa.Column("latency_ms", sa.Float, nullable=False, default=0),
        sa.Column("cost_usd", sa.Float, nullable=False, default=0),
        # Status
        sa.Column("status", sa.String(20), nullable=False, default="success", index=True),
        sa.Column("error_message", sa.Text, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )
    
    # Create indexes for common queries
    op.create_index(
        "ix_ai_logs_feature_created_at",
        "ai_logs",
        ["feature", "created_at"],
    )
    op.create_index(
        "ix_ai_logs_user_feature",
        "ai_logs",
        ["user_id", "feature"],
    )


def downgrade() -> None:
    """Drop ai_logs table."""
    op.drop_index("ix_ai_logs_user_feature", table_name="ai_logs")
    op.drop_index("ix_ai_logs_feature_created_at", table_name="ai_logs")
    op.drop_table("ai_logs")
