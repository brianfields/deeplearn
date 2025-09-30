"""Add unit artwork fields."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e2bd904a2f4"
down_revision: Union[str, None] = "df47171ac6ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("units", sa.Column("art_image_id", sa.UUID(), nullable=True))
    op.add_column("units", sa.Column("art_image_description", sa.Text(), nullable=True))
    op.create_index("idx_units_art_image_id", "units", ["art_image_id"], unique=False)
    op.create_foreign_key(
        "fk_units_art_image_id_images",
        "units",
        "images",
        ["art_image_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_units_art_image_id_images", "units", type_="foreignkey")
    op.drop_index("idx_units_art_image_id", table_name="units")
    op.drop_column("units", "art_image_description")
    op.drop_column("units", "art_image_id")
