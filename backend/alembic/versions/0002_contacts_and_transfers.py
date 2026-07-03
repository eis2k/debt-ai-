"""contacts and claim transfers

Revision ID: 0002_contacts_and_transfers
Revises: 0001_initial_schema
Create Date: 2026-07-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_contacts_and_transfers"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=True),
        sa.Column("person_name", sa.String(length=255), nullable=True),
        sa.Column("street", sa.String(length=255), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), server_default="DE", nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("display_name", name="uq_contacts_display_name"),
    )
    op.create_table(
        "contact_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("alias", name="uq_contact_aliases_alias"),
    )
    op.create_table(
        "document_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="unknown", nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "contact_id", "role", name="uq_document_contacts_role"),
    )
    op.add_column("creditors", sa.Column("contact_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_creditors_contact_id_contacts",
        "creditors",
        "contacts",
        ["contact_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "claim_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.Integer(), nullable=False),
        sa.Column("from_creditor_id", sa.Integer(), nullable=True),
        sa.Column("to_creditor_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("transfer_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_creditor_id"], ["creditors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_creditor_id"], ["creditors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_document_contacts_document_id", "document_contacts", ["document_id"])
    op.create_index("ix_claim_transfers_claim_id", "claim_transfers", ["claim_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_transfers_claim_id", table_name="claim_transfers")
    op.drop_index("ix_document_contacts_document_id", table_name="document_contacts")
    op.drop_table("claim_transfers")
    op.drop_constraint("fk_creditors_contact_id_contacts", "creditors", type_="foreignkey")
    op.drop_column("creditors", "contact_id")
    op.drop_table("document_contacts")
    op.drop_table("contact_aliases")
    op.drop_table("contacts")
