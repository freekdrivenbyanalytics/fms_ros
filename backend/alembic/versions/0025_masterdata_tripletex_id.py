"""switch products/customers/customer_locations to app-generated ids, add tripletex_id

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-20

Additive-only: no existing row's id changes, and therefore no foreign key
anywhere (contract_lines.customer_location_id, contracts.customer_id,
contract_line_products, *_sync_log tables) needs updating. Every existing
row's id already equals the real Tripletex id, so it's simply copied into
the new tripletex_id column, then id's generation strategy switches to an
app-owned sequence seeded above the current max so new locally-created rows
never collide with it. See local-first-masterdata-sync's design.md.
"""

from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

_TABLES = ("products", "customers", "customer_locations")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("tripletex_id", sa.Integer(), nullable=True))
        op.create_unique_constraint(f"uq_{table}_tripletex_id", table, ["tripletex_id"])
        op.execute(f"UPDATE {table} SET tripletex_id = id")

        seq_name = f"{table}_id_seq"
        op.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} OWNED BY {table}.id")
        op.execute(
            f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
        )
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT nextval('{seq_name}')")


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")
        op.execute(f"DROP SEQUENCE IF EXISTS {table}_id_seq")
        op.drop_constraint(f"uq_{table}_tripletex_id", table, type_="unique")
        op.drop_column(table, "tripletex_id")
