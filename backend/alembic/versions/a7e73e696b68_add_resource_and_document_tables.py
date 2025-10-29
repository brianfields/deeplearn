"""
Add resource, document, and unit resource tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7e73e696b68"
down_revision: Union[str, None] = "1cde343a5f8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("s3_bucket", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_s3_key", "documents", ["s3_key"], unique=True)
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "resources",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_type", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.String(length=1024)),
        sa.Column("filename", sa.String(length=255)),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extraction_metadata", sa.JSON(), nullable=False),
        sa.Column("file_size", sa.Integer()),
        sa.Column("object_store_document_id", sa.UUID(), sa.ForeignKey("documents.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resources_user_id", "resources", ["user_id"])
    op.create_index("ix_resources_created_at", "resources", ["created_at"])

    op.create_table(
        "unit_resources",
        sa.Column("unit_id", sa.String(length=36), sa.ForeignKey("units.id"), primary_key=True, nullable=False),
        sa.Column("resource_id", sa.UUID(), sa.ForeignKey("resources.id"), primary_key=True, nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_unit_resources_unit_id", "unit_resources", ["unit_id"])
    op.create_index("ix_unit_resources_resource_id", "unit_resources", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_unit_resources_resource_id", table_name="unit_resources")
    op.drop_index("ix_unit_resources_unit_id", table_name="unit_resources")
    op.drop_table("unit_resources")

    op.drop_index("ix_resources_created_at", table_name="resources")
    op.drop_index("ix_resources_user_id", table_name="resources")
    op.drop_table("resources")

    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_index("ix_documents_s3_key", table_name="documents")
    op.drop_table("documents")
