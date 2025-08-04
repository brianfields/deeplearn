"""merge podcast and main branches

Revision ID: c6f57a67a0b0
Revises: 669da36b1888, 6c8be4ad7cda
Create Date: 2025-08-03 20:12:27.850150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6f57a67a0b0'
down_revision: Union[str, None] = ('669da36b1888', '6c8be4ad7cda')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
