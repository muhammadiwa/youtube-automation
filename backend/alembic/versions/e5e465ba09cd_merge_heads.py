"""merge_heads

Revision ID: e5e465ba09cd
Revises: 049_drop_comment_tables, 050_soft_delete
Create Date: 2026-01-08 16:09:41.894520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5e465ba09cd'
down_revision: Union[str, None] = ('049_drop_comment_tables', '050_soft_delete')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
