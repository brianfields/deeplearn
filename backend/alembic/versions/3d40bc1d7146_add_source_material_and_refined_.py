"""Add source material and refined material fields to bite_sized_topics

Revision ID: 3d40bc1d7146
Revises: a30e90d7ac77
Create Date: 2025-07-17 19:55:09.747738

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3d40bc1d7146"
down_revision: Union[str, None] = "a30e90d7ac77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source material and refined material fields to bite_sized_topics table
    op.add_column(
        "bite_sized_topics", sa.Column("source_material", sa.Text(), nullable=True)
    )
    op.add_column(
        "bite_sized_topics", sa.Column("source_domain", sa.String(), nullable=True)
    )
    op.add_column(
        "bite_sized_topics", sa.Column("source_level", sa.String(), nullable=True)
    )
    op.add_column(
        "bite_sized_topics", sa.Column("refined_material", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # Remove source material and refined material fields from bite_sized_topics table
    op.drop_column("bite_sized_topics", "refined_material")
    op.drop_column("bite_sized_topics", "source_level")
    op.drop_column("bite_sized_topics", "source_domain")
    op.drop_column("bite_sized_topics", "source_material")
