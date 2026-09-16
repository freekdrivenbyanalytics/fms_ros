"""add product_type to products

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-16

"""

from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("product_type", sa.String(), nullable=False, server_default="TJN"),
    )


def downgrade() -> None:
    op.drop_column("products", "product_type")
