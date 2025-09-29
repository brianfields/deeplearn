"""add unit cover image fields

Revision ID: d3c8f2b7b3fb
Revises: bcbced6d3bb7
Create Date: 2025-01-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d3c8f2b7b3fb"
down_revision: Union[str, None] = "bcbced6d3bb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI-generated cover image metadata to units."""
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cover_image_url", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("cover_image_prompt", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "cover_image_request_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            )
        )


def downgrade() -> None:
    """Remove AI-generated cover image metadata from units."""
    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("cover_image_request_id")
        batch_op.drop_column("cover_image_prompt")
        batch_op.drop_column("cover_image_url")
