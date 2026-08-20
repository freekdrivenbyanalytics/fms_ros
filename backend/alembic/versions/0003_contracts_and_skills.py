"""add skills, employee_skills, contracts, contract_skills; move visit contract/duration fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-20

"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "employee_skills",
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
    )

    op.create_table(
        "contract_skills",
        sa.Column(
            "contract_id",
            sa.Integer(),
            sa.ForeignKey("contracts.id"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )

    op.add_column(
        "service_visits",
        sa.Column(
            "contract_id",
            sa.Integer(),
            sa.ForeignKey("contracts.id"),
            nullable=False,
        ),
    )
    op.drop_column("service_visits", "customer_location_id")
    op.drop_column("service_visits", "duration_minutes")


def downgrade() -> None:
    op.add_column(
        "service_visits",
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
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
    op.drop_column("service_visits", "contract_id")

    op.drop_table("contract_skills")
    op.drop_table("contracts")
    op.drop_table("employee_skills")
    op.drop_table("skills")
