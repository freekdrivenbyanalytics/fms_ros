"""replace static employee work hours with schedule templates and day
overrides; add employees.delete_flag

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-31

"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

lunch_type = sa.Enum("none", "fixed", "flexible", name="lunch_type")
day_type = sa.Enum("working", "holiday", "sick", name="day_type")


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "employee_schedule_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("work_start", sa.Time(), nullable=False),
        sa.Column("work_end", sa.Time(), nullable=False),
        sa.Column("max_hours_per_day", sa.Float(), nullable=False),
        sa.Column(
            "lunch_type", lunch_type, nullable=False, server_default="none"
        ),
        sa.Column("lunch_start", sa.Time(), nullable=True),
        sa.Column("lunch_end", sa.Time(), nullable=True),
        sa.Column("lunch_duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    op.create_table(
        "employee_schedule_day_overrides",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("day_type", day_type, nullable=False),
        sa.Column("work_start", sa.Time(), nullable=True),
        sa.Column("work_end", sa.Time(), nullable=True),
        sa.Column("max_hours_per_day", sa.Float(), nullable=True),
        sa.Column("overtime_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    # Backfill one open-ended template per existing employee from their
    # current static hours, so nobody silently loses schedule coverage once
    # employees.work_start/work_end are dropped below. COALESCE covers a
    # downgrade-then-upgrade round trip, where the re-added columns (see
    # downgrade()) come back nullable rather than restoring the original hours.
    op.execute(
        """
        INSERT INTO employee_schedule_templates
            (employee_id, start_date, end_date, work_start, work_end, max_hours_per_day, lunch_type)
        SELECT id, CURRENT_DATE, NULL, COALESCE(work_start, '08:00'), COALESCE(work_end, '16:00'), 8, 'none'
        FROM employees
        """
    )

    op.drop_column("employees", "work_start")
    op.drop_column("employees", "work_end")


def downgrade() -> None:
    op.add_column("employees", sa.Column("work_start", sa.Time(), nullable=True))
    op.add_column("employees", sa.Column("work_end", sa.Time(), nullable=True))

    op.drop_table("employee_schedule_day_overrides")
    op.drop_table("employee_schedule_templates")

    day_type.drop(op.get_bind(), checkfirst=True)
    lunch_type.drop(op.get_bind(), checkfirst=True)

    op.drop_column("employees", "delete_flag")
