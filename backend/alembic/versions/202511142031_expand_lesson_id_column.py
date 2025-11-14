"""Expand lesson id column to accommodate intro lesson ID suffix

Intro lessons use ID pattern: {unit_id}-intro
Standard UUIDs are 36 chars, so this can reach 42+ chars depending on unit_id length.
Expanding to VARCHAR(50) to safely accommodate this.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202511142031"
down_revision = "202511130142"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Expand the id column from VARCHAR(36) to VARCHAR(50)
    op.alter_column(
        "lessons",
        "id",
        existing_type=sa.String(36),
        type_=sa.String(50),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert to VARCHAR(36)
    op.alter_column(
        "lessons",
        "id",
        existing_type=sa.String(50),
        type_=sa.String(36),
        existing_nullable=False,
    )
