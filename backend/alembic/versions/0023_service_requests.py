"""add service_requests table

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-18

"""

from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

service_request_status = sa.Enum("pending", "acknowledged", name="service_request_status")


def upgrade() -> None:
    op.create_table(
        "service_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column(
            "status", service_request_status, nullable=False, server_default="pending"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("service_requests")
    service_request_status.drop(op.get_bind(), checkfirst=True)
