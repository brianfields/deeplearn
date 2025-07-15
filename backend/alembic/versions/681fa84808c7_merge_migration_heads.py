"""Merge migration heads

Revision ID: 681fa84808c7
Revises: add_title_remove_metadata, 5d2b95576a92
Create Date: 2025-07-14 16:02:04.116252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '681fa84808c7'
down_revision: Union[str, None] = ('add_title_remove_metadata', '5d2b95576a92')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
