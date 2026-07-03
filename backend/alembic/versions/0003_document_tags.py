"""document tags

Revision ID: 0003_document_tags
Revises: 0002_contacts_and_transfers
Create Date: 2026-07-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_document_tags"
down_revision = "0002_contacts_and_transfers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_tags_gin", "documents", ["tags"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_documents_tags_gin", table_name="documents")
    op.drop_column("documents", "tags")
