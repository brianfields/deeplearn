"""single_lesson_model_with_package

Revision ID: 9661888248d9
Revises: 0bf61cd98700
Create Date: 2025-09-11 11:54:46.085079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9661888248d9'
down_revision: Union[str, None] = '0bf61cd98700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the lesson_components table (clean slate approach)
    op.drop_table('lesson_components')

    # Remove old columns from lessons table
    op.drop_column('lessons', 'learning_objectives')
    op.drop_column('lessons', 'key_concepts')

    # Add new package columns
    op.add_column('lessons', sa.Column('package', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('lessons', sa.Column('package_version', sa.Integer(), nullable=False, server_default='1'))

    # Remove server defaults after adding columns
    op.alter_column('lessons', 'package', server_default=None)
    op.alter_column('lessons', 'package_version', server_default=None)


def downgrade() -> None:
    # Recreate lesson_components table
    op.create_table('lesson_components',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('lesson_id', sa.String(length=36), nullable=False),
        sa.Column('component_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('learning_objective', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Remove new columns
    op.drop_column('lessons', 'package_version')
    op.drop_column('lessons', 'package')

    # Restore old columns
    op.add_column('lessons', sa.Column('learning_objectives', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('lessons', sa.Column('key_concepts', sa.JSON(), nullable=False, server_default='[]'))

    # Remove server defaults
    op.alter_column('lessons', 'learning_objectives', server_default=None)
    op.alter_column('lessons', 'key_concepts', server_default=None)
