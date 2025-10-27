"""Add lesson podcast columns

Revision ID: 202411050001
Revises: 8f22bdd4a329
Create Date: 2024-11-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202411050001"
down_revision: Union[str, None] = "8f22bdd4a329"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("podcast_transcript", sa.Text(), nullable=True))
    op.add_column("lessons", sa.Column("podcast_voice", sa.String(length=100), nullable=True))
    op.add_column("lessons", sa.Column("podcast_audio_object_id", sa.UUID(), nullable=True))
    op.add_column("lessons", sa.Column("podcast_generated_at", sa.DateTime(), nullable=True))
    op.add_column("lessons", sa.Column("podcast_duration_seconds", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "podcast_duration_seconds")
    op.drop_column("lessons", "podcast_generated_at")
    op.drop_column("lessons", "podcast_audio_object_id")
    op.drop_column("lessons", "podcast_voice")
    op.drop_column("lessons", "podcast_transcript")

