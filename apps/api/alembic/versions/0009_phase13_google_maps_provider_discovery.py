"""Phase 13: Google Maps Provider Discovery and Classification.

Revision ID: 0009_phase13
Revises: 0008_phase12
"""
from alembic import op
import sqlalchemy as sa


revision = "0009_phase13"
down_revision = "0008_phase12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new discovery, classification, and enrichment columns to vendors table
    op.add_column("vendors", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("vendors", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("vendors", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("vendors", sa.Column("website", sa.String(length=500), nullable=True))
    op.add_column("vendors", sa.Column("maps_url", sa.String(length=500), nullable=True))
    op.add_column("vendors", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("vendors", sa.Column("review_count", sa.Integer(), nullable=True))
    op.add_column("vendors", sa.Column("source", sa.String(length=50), nullable=False, server_default="INTERNAL"))
    op.add_column("vendors", sa.Column("source_id", sa.String(length=255), nullable=True))
    op.add_column("vendors", sa.Column("raw_category", sa.String(length=255), nullable=True))
    op.add_column("vendors", sa.Column("capabilities", sa.JSON(), nullable=True))
    op.add_column("vendors", sa.Column("classification_confidence", sa.Float(), nullable=True))

    op.create_index("ix_vendors_source", "vendors", ["source"])
    op.create_index("ix_vendors_source_id", "vendors", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_vendors_source_id", table_name="vendors")
    op.drop_index("ix_vendors_source", table_name="vendors")

    op.drop_column("vendors", "classification_confidence")
    op.drop_column("vendors", "capabilities")
    op.drop_column("vendors", "raw_category")
    op.drop_column("vendors", "source_id")
    op.drop_column("vendors", "source")
    op.drop_column("vendors", "review_count")
    op.drop_column("vendors", "rating")
    op.drop_column("vendors", "maps_url")
    op.drop_column("vendors", "website")
    op.drop_column("vendors", "longitude")
    op.drop_column("vendors", "latitude")
    op.drop_column("vendors", "address")
