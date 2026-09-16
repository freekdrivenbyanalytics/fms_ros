"""drop resco_address_line1/city/postal_code/country from customers

Populating a customer-level physical address via Tripletex's API turned out
to have a side effect: it creates a brand-new delivery address (customer
location) rather than just updating the customer's own address in place.
The Resco Account payload now sources its address from the customer's
existing customer_location instead, so these columns are unused.

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-16

"""

from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("customers", "resco_address_line1")
    op.drop_column("customers", "resco_city")
    op.drop_column("customers", "resco_postal_code")
    op.drop_column("customers", "resco_country")


def downgrade() -> None:
    op.add_column("customers", sa.Column("resco_address_line1", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_city", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_postal_code", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_country", sa.String(), nullable=True))
