"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-19

"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

visit_status = sa.Enum("unassigned", "assigned", name="visit_status")


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("work_start", sa.Time(), nullable=False),
        sa.Column("work_end", sa.Time(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
    )

    op.create_table(
        "service_visits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            visit_status,
            nullable=False,
            server_default="unassigned",
        ),
    )

    op.create_table(
        "assignments",
        sa.Column(
            "service_visit_id",
            sa.Integer(),
            sa.ForeignKey("service_visits.id"),
            primary_key=True,
        ),
        sa.Column(
            "employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column("planned_start", sa.DateTime(), nullable=False),
        sa.Column("planned_end", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("assignments")
    op.drop_table("service_visits")
    op.drop_table("employees")
    visit_status.drop(op.get_bind(), checkfirst=True)
