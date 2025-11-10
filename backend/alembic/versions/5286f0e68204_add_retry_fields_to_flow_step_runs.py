"""add_retry_fields_to_flow_step_runs

Revision ID: 5286f0e68204
Revises: c340fb60e2a2
Create Date: 2025-11-10 10:53:24.539592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5286f0e68204'
down_revision: Union[str, None] = 'c340fb60e2a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add retry tracking fields to flow_step_runs
    op.add_column('flow_step_runs', sa.Column('retry_attempt', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flow_step_runs', sa.Column('retry_of_step_run_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add foreign key and index for retry_of_step_run_id
    op.create_foreign_key('fk_flow_step_runs_retry_of', 'flow_step_runs', 'flow_step_runs', ['retry_of_step_run_id'], ['id'])
    op.create_index('ix_flow_step_runs_retry_of_step_run_id', 'flow_step_runs', ['retry_of_step_run_id'])


def downgrade() -> None:
    # Remove retry tracking fields
    op.drop_index('ix_flow_step_runs_retry_of_step_run_id', table_name='flow_step_runs')
    op.drop_constraint('fk_flow_step_runs_retry_of', 'flow_step_runs', type_='foreignkey')
    op.drop_column('flow_step_runs', 'retry_of_step_run_id')
    op.drop_column('flow_step_runs', 'retry_attempt')
