"""Add local_thumbnail_path to videos table

Revision ID: 044_local_thumbnail
Revises: 043_template_fields
Create Date: 2024-12-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "044_local_thumbnail"
down_revision = "043_template_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add local_thumbnail_path column for storing thumbnail before YouTube upload
    op.add_column(
        "videos",
        sa.Column("local_thumbnail_path", sa.String(512), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("videos", "local_thumbnail_path")
