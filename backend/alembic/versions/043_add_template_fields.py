"""Add title_template and is_default to video_templates

Revision ID: 043_template_fields
Revises: 042_plan_icon_color
Create Date: 2024-12-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "043_template_fields"
down_revision = "042_plan_icon_color"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title_template column
    op.add_column('video_templates', sa.Column('title_template', sa.String(200), nullable=True))
    # Add is_default column
    op.add_column('video_templates', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('video_templates', 'is_default')
    op.drop_column('video_templates', 'title_template')
