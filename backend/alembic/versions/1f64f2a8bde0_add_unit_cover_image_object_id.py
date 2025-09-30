"""add cover_image_object_id to units"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "1f64f2a8bde0"
down_revision = "d3c8f2b7b3fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("cover_image_object_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("units", "cover_image_object_id")
