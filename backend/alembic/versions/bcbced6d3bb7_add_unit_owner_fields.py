"""add_unit_owner_fields

Revision ID: bcbced6d3bb7
Revises: 4f3f8c5f4c5a
Create Date: 2025-09-25 16:09:15.515024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bcbced6d3bb7"
down_revision: Union[str, None] = "4f3f8c5f4c5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ownership metadata to the units table."""
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_global",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        batch_op.create_index("ix_units_user_id", ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_units_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade() -> None:
    """Remove ownership metadata from the units table."""
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_constraint("fk_units_user_id_users", type_="foreignkey")
        batch_op.drop_index("ix_units_user_id")
        batch_op.drop_column("is_global")
        batch_op.drop_column("user_id")
