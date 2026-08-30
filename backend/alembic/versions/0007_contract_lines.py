"""split contracts into contracts (customer-level) and contract_lines
(customer-location-level)

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30

"""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing demo data references the contract shape about to be replaced;
    # it is recreated by the restructured seed script afterward.
    op.execute(
        "TRUNCATE TABLE assignments, service_visits, contract_skills, contracts CASCADE"
    )
    op.drop_table("contract_skills")

    # contracts becomes a bare customer-level grouping entity; everything it
    # used to carry directly moves to the new contract_lines table.
    op.drop_column("contracts", "customer_location_id")
    op.drop_column("contracts", "start_date")
    op.drop_column("contracts", "interval_days")
    op.drop_column("contracts", "duration_minutes")
    op.add_column(
        "contracts",
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
    )
    op.add_column(
        "contracts",
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "contract_lines",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=False
        ),
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    op.create_table(
        "contract_line_skills",
        sa.Column(
            "contract_line_id",
            sa.Integer(),
            sa.ForeignKey("contract_lines.id"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )

    op.add_column(
        "service_visits",
        sa.Column(
            "contract_line_id",
            sa.Integer(),
            sa.ForeignKey("contract_lines.id"),
            nullable=False,
        ),
    )
    op.drop_column("service_visits", "contract_id")


def downgrade() -> None:
    op.add_column(
        "service_visits",
        sa.Column(
            "contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=False
        ),
    )
    op.drop_column("service_visits", "contract_line_id")

    op.drop_table("contract_line_skills")
    op.drop_table("contract_lines")

    op.drop_column("contracts", "delete_flag")
    op.drop_column("contracts", "customer_id")
    op.add_column(
        "contracts",
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
    )
    op.add_column(
        "contracts",
        sa.Column("interval_days", sa.Integer(), nullable=False),
    )
    op.add_column(
        "contracts",
        sa.Column("start_date", sa.Date(), nullable=False),
    )
    op.add_column(
        "contracts",
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
    )

    op.create_table(
        "contract_skills",
        sa.Column(
            "contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), primary_key=True
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )
