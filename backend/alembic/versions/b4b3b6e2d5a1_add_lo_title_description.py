"""Document learning objective title/description structure.

The learning_objectives JSON payload stored on units now includes
explicit short titles alongside the full description text. The JSON
schema remains flexible, so no database schema alterations are required.
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "b4b3b6e2d5a1"
down_revision = "95f796d6e668"
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Schema tracked for documentation purposes only."""
    pass

def downgrade() -> None:
    """No structural changes to revert."""
    pass
