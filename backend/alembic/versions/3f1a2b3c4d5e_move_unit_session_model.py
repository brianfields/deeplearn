"""Move UnitSessionModel to learning_session module (no schema changes)

Revision ID: 3f1a2b3c4d5e
Revises: 17580e04bfdc
Create Date: 2025-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op  # noqa: F401  # imported for Alembic operations
import sqlalchemy as sa  # noqa: F401  # imported for completeness

# revision identifiers, used by Alembic.
revision: str = "3f1a2b3c4d5e"
down_revision: Union[str, None] = "17580e04bfdc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op migration. Model moved modules; table unchanged."""
    # No schema changes required
    pass


def downgrade() -> None:
    """No-op downgrade. Model move is code-only."""
    # No schema changes to revert
    pass
