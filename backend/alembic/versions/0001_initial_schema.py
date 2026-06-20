"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("paperless_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("document_type", sa.String(length=255), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("paperless_url", sa.String(length=1024), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("paperless_id", name="uq_documents_paperless_id"),
    )
    op.create_index("ix_documents_document_date", "documents", ["document_date"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_filename", "documents", ["filename"])
    op.execute("CREATE INDEX ix_documents_ocr_text_fts ON documents USING gin (to_tsvector('german', coalesce(ocr_text, '')))")

    op.create_table(
        "creditors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("canonical_name", name="uq_creditors_canonical_name"),
    )

    op.create_table(
        "creditor_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creditor_id", sa.Integer(), sa.ForeignKey("creditors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("alias", name="uq_creditor_aliases_alias"),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creditor_id", sa.Integer(), sa.ForeignKey("creditors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("claim_reference", sa.String(length=255), nullable=True),
        sa.Column("contract_reference", sa.String(length=255), nullable=True),
        sa.Column("title_exists", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("title_type", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=100), server_default="unknown", nullable=False),
        sa.Column("first_seen", sa.Date(), nullable=True),
        sa.Column("last_seen", sa.Date(), nullable=True),
    )
    op.create_index("ix_claims_claim_reference", "claims", ["claim_reference"])
    op.create_index("ix_claims_contract_reference", "claims", ["contract_reference"])
    op.create_index("ix_claims_status", "claims", ["status"])

    op.create_table(
        "claim_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_claim_events_event_type", "claim_events", ["event_type"])
    op.create_index("ix_claim_events_event_date", "claim_events", ["event_date"])

    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
    )
    op.execute("ALTER TABLE embeddings ADD COLUMN embedding vector(1024)")
    op.execute("CREATE INDEX ix_embeddings_embedding ON embeddings USING ivfflat (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.drop_table("embeddings")
    op.drop_table("claim_events")
    op.drop_table("claims")
    op.drop_table("creditor_aliases")
    op.drop_table("creditors")
    op.drop_table("documents")
