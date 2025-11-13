"""Add podcast transcript segments column to lessons table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202511130142"
down_revision = "46476cb0b280"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("podcast_transcript_segments", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lessons", "podcast_transcript_segments")
