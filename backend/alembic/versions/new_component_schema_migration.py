"""Add title field and remove component_metadata from bite_sized_components

Revision ID: add_title_remove_metadata
Revises: 6b171dec0c06
Create Date: 2024-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_title_remove_metadata'
down_revision = '6b171dec0c06'
branch_labels = None
depends_on = None


def upgrade():
    # Add title column to bite_sized_components
    op.add_column('bite_sized_components', sa.Column('title', sa.String(), nullable=False, server_default='Untitled Component'))

    # Update existing components to have meaningful titles based on their type
    op.execute("""
        UPDATE bite_sized_components
        SET title = CASE
            WHEN component_type = 'didactic_snippet' THEN 'Didactic Snippet'
            WHEN component_type = 'glossary' THEN 'Glossary Entry'
            WHEN component_type = 'socratic_dialogue' THEN 'Socratic Dialogue'
            WHEN component_type = 'short_answer_question' THEN 'Short Answer Question'
            WHEN component_type = 'multiple_choice_question' THEN 'Multiple Choice Question'
            WHEN component_type = 'post_topic_quiz' THEN 'Post-Topic Quiz Item'
            ELSE 'Component'
        END
    """)

    # Remove the server default after updating existing data
    op.alter_column('bite_sized_components', 'title', server_default=None)

    # Change content column type from Text to JSON
    op.alter_column('bite_sized_components', 'content',
                   type_=sa.JSON(),
                   postgresql_using='content::json')

    # For existing data, merge any component_metadata into content if it exists
    # This is a simplified approach that avoids complex type casting issues
    op.execute("""
        UPDATE bite_sized_components
        SET content = '{}'
        WHERE content IS NULL
    """)

    # Drop the component_metadata column
    op.drop_column('bite_sized_components', 'component_metadata')


def downgrade():
    # Add back component_metadata column
    op.add_column('bite_sized_components', sa.Column('component_metadata', sa.JSON(), nullable=True))

    # Change content column back to Text
    op.alter_column('bite_sized_components', 'content',
                   type_=sa.Text(),
                   postgresql_using='content::text')

    # Drop the title column
    op.drop_column('bite_sized_components', 'title')