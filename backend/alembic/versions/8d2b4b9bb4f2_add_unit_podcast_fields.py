"""Add podcast transcript and audio fields to units table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d2b4b9bb4f2"
down_revision: Union[str, None] = "bcbced6d3bb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add podcast-related metadata fields to the units table."""

    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.add_column(sa.Column("podcast_transcript", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("podcast_voice", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("podcast_audio", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("podcast_audio_mime_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("podcast_duration_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("podcast_generated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove podcast fields from the units table."""

    with op.batch_alter_table("units", schema=None) as batch_op:
        batch_op.drop_column("podcast_generated_at")
        batch_op.drop_column("podcast_duration_seconds")
        batch_op.drop_column("podcast_audio_mime_type")
        batch_op.drop_column("podcast_audio")
        batch_op.drop_column("podcast_voice")
        batch_op.drop_column("podcast_transcript")
