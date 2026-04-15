"""Drop strike tables.

Revision ID: 051
Revises: e5e465ba09cd
Create Date: 2026-01-15 00:00:00.000000

Removes Strike, StrikeAlert, and PausedStream tables.
Strike feature has been removed as YouTube API doesn't provide public access to strike data.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "051"
down_revision = "e5e465ba09cd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop paused_streams table first (has FK to strikes)
    op.drop_index(op.f("ix_paused_streams_account_id"), table_name="paused_streams", if_exists=True)
    op.drop_index(op.f("ix_paused_streams_live_event_id"), table_name="paused_streams", if_exists=True)
    op.drop_index(op.f("ix_paused_streams_strike_id"), table_name="paused_streams", if_exists=True)
    op.drop_index("ix_paused_streams_account_resumed", table_name="paused_streams", if_exists=True)
    op.drop_table("paused_streams", if_exists=True)
    
    # Drop strike_alerts table (has FK to strikes)
    op.drop_index(op.f("ix_strike_alerts_account_id"), table_name="strike_alerts", if_exists=True)
    op.drop_index(op.f("ix_strike_alerts_strike_id"), table_name="strike_alerts", if_exists=True)
    op.drop_table("strike_alerts", if_exists=True)
    
    # Drop strikes table
    op.drop_index("ix_strikes_issued_at", table_name="strikes", if_exists=True)
    op.drop_index("ix_strikes_account_status", table_name="strikes", if_exists=True)
    op.drop_index(op.f("ix_strikes_status"), table_name="strikes", if_exists=True)
    op.drop_index(op.f("ix_strikes_youtube_strike_id"), table_name="strikes", if_exists=True)
    op.drop_index(op.f("ix_strikes_account_id"), table_name="strikes", if_exists=True)
    op.drop_table("strikes", if_exists=True)


def downgrade() -> None:
    # Strike feature has been removed - no downgrade path
    # If needed, restore from backup or re-run migration 016_strike_models.py
    pass
