"""Add tasks table and ARQ task relationships."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "3f0b3e9c8b23"
down_revision = "c0c59980549d"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Apply schema changes."""

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("queue_name", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("task_type", sa.String(length=255), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(length=200), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("flow_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unit_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_tasks_task_name", "tasks", ["task_name"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_queue_name", "tasks", ["queue_name"])
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"])
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_flow_run_id", "tasks", ["flow_run_id"])
    op.create_index("ix_tasks_unit_id", "tasks", ["unit_id"])

    op.add_column("flow_runs", sa.Column("arq_task_id", sa.String(length=255), nullable=True))
    op.create_index("ix_flow_runs_arq_task_id", "flow_runs", ["arq_task_id"])

    op.add_column("units", sa.Column("arq_task_id", sa.String(length=255), nullable=True))
    op.create_index("ix_units_arq_task_id", "units", ["arq_task_id"])


def downgrade() -> None:
    """Revert schema changes."""

    op.drop_index("ix_units_arq_task_id", table_name="units")
    op.drop_column("units", "arq_task_id")

    op.drop_index("ix_flow_runs_arq_task_id", table_name="flow_runs")
    op.drop_column("flow_runs", "arq_task_id")

    op.drop_index("ix_tasks_unit_id", table_name="tasks")
    op.drop_index("ix_tasks_flow_run_id", table_name="tasks")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_index("ix_tasks_task_type", table_name="tasks")
    op.drop_index("ix_tasks_queue_name", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_task_name", table_name="tasks")
    op.drop_table("tasks")
