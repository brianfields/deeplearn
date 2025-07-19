"""remove_creation_strategy_column

Revision ID: 669da36b1888
Revises: 3d40bc1d7146
Create Date: 2025-07-18 17:04:33.784844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '669da36b1888'
down_revision: Union[str, None] = '3d40bc1d7146'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the index first (if it exists)
    try:
        op.drop_index('idx_bite_sized_topics_creation_strategy', table_name='bite_sized_topics')
    except Exception:
        # Index might not exist, continue
        pass

    # Remove the creation_strategy column
    op.drop_column('bite_sized_topics', 'creation_strategy')


def downgrade() -> None:
    # Add the creation_strategy column back
    op.add_column('bite_sized_topics', sa.Column('creation_strategy', sa.String(), nullable=False, server_default='content_creation'))

    # Recreate the index
    op.create_index('idx_bite_sized_topics_creation_strategy', 'bite_sized_topics', ['creation_strategy'], unique=False)
