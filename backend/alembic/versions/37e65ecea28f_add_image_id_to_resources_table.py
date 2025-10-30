"""Add image id to resources table

Revision ID: 37e65ecea28f
Revises: 95283d11506f
Create Date: 2025-10-30 00:16:01.980560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "37e65ecea28f"
down_revision: Union[str, None] = "95283d11506f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add image foreign key reference to resources."""
    op.add_column("resources", sa.Column("object_store_image_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_resources_object_store_image_id_images",
        "resources",
        "images",
        ["object_store_image_id"],
        ["id"],
    )
    op.create_index("ix_resources_object_store_image_id", "resources", ["object_store_image_id"], unique=False)


def downgrade() -> None:
    """Remove image foreign key reference from resources."""
    op.drop_index("ix_resources_object_store_image_id", table_name="resources")
    op.drop_constraint("fk_resources_object_store_image_id_images", "resources", type_="foreignkey")
    op.drop_column("resources", "object_store_image_id")
