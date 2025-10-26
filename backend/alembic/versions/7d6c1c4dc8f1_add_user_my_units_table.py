"""Add user_my_units join table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d6c1c4dc8f1'
down_revision: Union[str, None] = '95f796d6e668'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_my_units join table."""
    op.create_table(
        'user_my_units',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.String(length=36), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'unit_id'),
    )
    op.create_index('ix_user_my_units_user_id', 'user_my_units', ['user_id'], unique=False)
    op.create_index('ix_user_my_units_unit_id', 'user_my_units', ['unit_id'], unique=False)


def downgrade() -> None:
    """Drop user_my_units join table."""
    op.drop_index('ix_user_my_units_unit_id', table_name='user_my_units')
    op.drop_index('ix_user_my_units_user_id', table_name='user_my_units')
    op.drop_table('user_my_units')
