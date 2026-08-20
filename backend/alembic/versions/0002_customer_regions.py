"""add regions, customers, customer_locations, employee_regions; move visit customer fields to customer_location

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20

"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "customer_locations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False
        ),
        sa.Column(
            "region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=False
        ),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
    )

    op.create_table(
        "employee_regions",
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id"),
            primary_key=True,
        ),
        sa.Column(
            "region_id", sa.Integer(), sa.ForeignKey("regions.id"), primary_key=True
        ),
    )

    op.add_column(
        "service_visits",
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
    )
    op.drop_column("service_visits", "customer_name")
    op.drop_column("service_visits", "address")
    op.drop_column("service_visits", "latitude")
    op.drop_column("service_visits", "longitude")


def downgrade() -> None:
    op.add_column(
        "service_visits", sa.Column("customer_name", sa.String(), nullable=False)
    )
    op.add_column("service_visits", sa.Column("address", sa.String(), nullable=False))
    op.add_column(
        "service_visits", sa.Column("latitude", sa.Float(), nullable=False)
    )
    op.add_column(
        "service_visits", sa.Column("longitude", sa.Float(), nullable=False)
    )
    op.drop_column("service_visits", "customer_location_id")

    op.drop_table("employee_regions")
    op.drop_table("customer_locations")
    op.drop_table("customers")
    op.drop_table("regions")
