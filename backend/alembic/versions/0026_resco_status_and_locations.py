"""Resco status, functional location and customer contacts.

Revision ID: 0026
Revises: 0025
"""
from alembic import op
import sqlalchemy as sa

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("customers", sa.Column("contact_name", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("resco_contact_id", sa.String(), nullable=True))
    op.add_column("customer_locations", sa.Column("resco_functional_location_id", sa.String(), nullable=True))
    op.add_column("service_visits", sa.Column("unassigned_reason", sa.String(), nullable=True))
    op.add_column("assignments", sa.Column("resco_status", sa.String(), nullable=True))
    op.add_column("assignments", sa.Column("resco_statecode", sa.Integer(), nullable=True))
    op.add_column("assignments", sa.Column("resco_statuscode", sa.Integer(), nullable=True))


def downgrade():
    for column in ("resco_statuscode", "resco_statecode", "resco_status"):
        op.drop_column("assignments", column)
    op.drop_column("service_visits", "unassigned_reason")
    op.drop_column("customer_locations", "resco_functional_location_id")
    op.drop_column("customers", "resco_contact_id")
    op.drop_column("customers", "contact_name")
