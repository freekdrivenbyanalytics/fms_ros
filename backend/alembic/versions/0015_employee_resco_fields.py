"""add first_name/last_name/email/mobile_phone/resco_user_id to employees, make name computed

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-14

"""

from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("employees", sa.Column("last_name", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE employees
        SET first_name = CASE
                WHEN position(' ' in name) > 0 THEN split_part(name, ' ', 1)
                ELSE name
            END,
            last_name = CASE
                WHEN position(' ' in name) > 0 THEN substring(name from position(' ' in name) + 1)
                ELSE ''
            END
        """
    )

    op.alter_column("employees", "first_name", nullable=False)
    op.alter_column("employees", "last_name", nullable=False)

    op.add_column("employees", sa.Column("email", sa.String(), nullable=True))
    op.add_column("employees", sa.Column("mobile_phone", sa.String(), nullable=True))
    op.add_column("employees", sa.Column("resco_user_id", sa.String(), nullable=True))

    op.drop_column("employees", "name")
    op.add_column(
        "employees",
        sa.Column(
            "name",
            sa.String(),
            sa.Computed("first_name || ' ' || last_name", persisted=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("employees", "name")
    op.add_column("employees", sa.Column("name", sa.String(), nullable=True))
    op.execute("UPDATE employees SET name = trim(first_name || ' ' || last_name)")
    op.alter_column("employees", "name", nullable=False)

    op.drop_column("employees", "resco_user_id")
    op.drop_column("employees", "mobile_phone")
    op.drop_column("employees", "email")
    op.drop_column("employees", "first_name")
    op.drop_column("employees", "last_name")
