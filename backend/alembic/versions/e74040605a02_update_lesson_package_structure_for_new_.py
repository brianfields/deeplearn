"""Update lesson package structure for new exercise generation.

This migration records the switch to the new lesson package JSON schema.
All fields remain in JSON columns so there are no SQL DDL changes.

Revision ID: e74040605a02
Revises: 37e65ecea28f
Create Date: 2025-11-05 21:31:57.046089

"""
from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = 'e74040605a02'
down_revision: Union[str, None] = '37e65ecea28f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op because package content lives in JSON columns."""
    pass


def downgrade() -> None:
    """No-op because package content lives in JSON columns."""
    pass
