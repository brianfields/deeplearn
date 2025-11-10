"""add_partial_status_to_units

Revision ID: c340fb60e2a2
Revises: d8cc3fa711f1
Create Date: 2025-11-10 10:23:46.572555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c340fb60e2a2'
down_revision: Union[str, None] = 'd8cc3fa711f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old check constraint
    op.drop_constraint('check_unit_status', 'units', type_='check')

    # Create the new check constraint with 'partial' added
    op.create_check_constraint(
        'check_unit_status',
        'units',
        "status IN ('draft', 'in_progress', 'completed', 'partial', 'failed')"
    )


def downgrade() -> None:
    # Drop the new check constraint
    op.drop_constraint('check_unit_status', 'units', type_='check')

    # Restore the old check constraint without 'partial'
    op.create_check_constraint(
        'check_unit_status',
        'units',
        "status IN ('draft', 'in_progress', 'completed', 'failed')"
    )
