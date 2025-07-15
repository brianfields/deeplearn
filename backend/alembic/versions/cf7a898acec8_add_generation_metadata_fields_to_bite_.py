"""Add generation metadata fields to bite_sized_components

Revision ID: cf7a898acec8
Revises: 681fa84808c7
Create Date: 2025-07-14 17:07:49.861803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf7a898acec8'
down_revision: Union[str, None] = '681fa84808c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add generation metadata fields to bite_sized_components table
    op.add_column('bite_sized_components', sa.Column('generation_prompt', sa.Text(), nullable=True))
    op.add_column('bite_sized_components', sa.Column('raw_llm_response', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove generation metadata fields from bite_sized_components table
    op.drop_column('bite_sized_components', 'raw_llm_response')
    op.drop_column('bite_sized_components', 'generation_prompt')
