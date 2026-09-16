"""add resco_product_id to products; add archived to customers/customer_locations/products

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-16

"""

from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("resco_product_id", sa.String(), nullable=True))
    op.add_column(
        "products",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "customers",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "customer_locations",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("customer_locations", "archived")
    op.drop_column("customers", "archived")
    op.drop_column("products", "archived")
    op.drop_column("products", "resco_product_id")
