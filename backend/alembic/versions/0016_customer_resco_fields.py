"""add resco_address_*/resco_account_id to customers, resco_asset_id to customer_locations

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-14

"""

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("resco_address_line1", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_city", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_postal_code", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_country", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_account_id", sa.String(), nullable=True))
    op.add_column(
        "customer_locations", sa.Column("resco_asset_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("customer_locations", "resco_asset_id")
    op.drop_column("customers", "resco_account_id")
    op.drop_column("customers", "resco_country")
    op.drop_column("customers", "resco_postal_code")
    op.drop_column("customers", "resco_city")
    op.drop_column("customers", "resco_address_line1")
