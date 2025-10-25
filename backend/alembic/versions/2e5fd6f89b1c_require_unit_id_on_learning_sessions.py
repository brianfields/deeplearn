"""Make learning session unit_id required and enforce FK"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2e5fd6f89b1c"
down_revision: Union[str, None] = "9cb0b78b0c16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove legacy sessions without unit context before enforcing NOT NULL
    op.execute("DELETE FROM learning_sessions WHERE unit_id IS NULL")

    op.alter_column(
        "learning_sessions",
        "unit_id",
        existing_type=sa.String(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_learning_sessions_unit_id_units",
        "learning_sessions",
        "units",
        ["unit_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_learning_sessions_unit_id_units", "learning_sessions", type_="foreignkey")
    op.alter_column(
        "learning_sessions",
        "unit_id",
        existing_type=sa.String(),
        nullable=True,
    )
