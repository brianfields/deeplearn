"""Add evaluation column to bite_sized_components

Revision ID: a30e90d7ac77
Revises: cf7a898acec8
Create Date: 2025-07-17 19:12:16.709486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a30e90d7ac77'
down_revision: Union[str, None] = 'cf7a898acec8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add evaluation column to bite_sized_components table
    op.add_column('bite_sized_components', sa.Column('evaluation', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove evaluation column from bite_sized_components table
    op.drop_column('bite_sized_components', 'evaluation')
