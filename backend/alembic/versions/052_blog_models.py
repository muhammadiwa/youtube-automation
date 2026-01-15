"""Blog models migration.

Revision ID: 052_blog_models
Revises: 051_drop_strike_tables
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, unique=True),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("featured_image", sa.String(500), nullable=True),
        sa.Column("meta_title", sa.String(200), nullable=True),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("featured", sa.Boolean, default=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_name", sa.String(255), nullable=False),
        sa.Column("view_count", sa.Integer, default=0),
        sa.Column("read_time_minutes", sa.Integer, default=5),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index("ix_article_slug", "articles", ["slug"])
    op.create_index("ix_article_category", "articles", ["category"])
    op.create_index("ix_article_status", "articles", ["status"])
    op.create_index("ix_article_author_id", "articles", ["author_id"])
    op.create_index("ix_article_status_published", "articles", ["status", "published_at"])
    op.create_index("ix_article_category_status", "articles", ["category", "status"])


def downgrade() -> None:
    op.drop_index("ix_article_category_status", table_name="articles")
    op.drop_index("ix_article_status_published", table_name="articles")
    op.drop_index("ix_article_author_id", table_name="articles")
    op.drop_index("ix_article_status", table_name="articles")
    op.drop_index("ix_article_category", table_name="articles")
    op.drop_index("ix_article_slug", table_name="articles")
    op.drop_table("articles")
