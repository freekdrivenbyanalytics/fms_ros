"""redefine customer_locations to mirror Tripletex delivery addresses, add
delete_flag, make region/coordinates nullable, add customer_location_sync_log

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-30

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

customer_location_change_type = sa.Enum(
    "created", "updated", "deleted", "restored", name="customer_location_change_type"
)


def upgrade() -> None:
    # Existing demo data references the fictional locations about to be
    # removed; it is recreated by the restructured seed script afterward.
    op.execute(
        "TRUNCATE TABLE assignments, service_visits, contracts, customer_locations CASCADE"
    )

    # customer_locations.id is now populated with Tripletex's own delivery
    # address id, not an app-generated identity.
    op.execute("ALTER TABLE customer_locations ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS customer_locations_id_seq")

    op.add_column("customer_locations", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column("customer_locations", sa.Column("url", sa.String(), nullable=True))
    op.add_column(
        "customer_locations", sa.Column("address_line_1", sa.String(), nullable=True)
    )
    op.add_column(
        "customer_locations", sa.Column("address_line_2", sa.String(), nullable=True)
    )
    op.add_column(
        "customer_locations", sa.Column("postal_code", sa.String(), nullable=True)
    )
    op.add_column("customer_locations", sa.Column("city", sa.String(), nullable=True))
    op.add_column("customer_locations", sa.Column("country", JSONB(), nullable=True))
    op.add_column("customer_locations", sa.Column("name", sa.String(), nullable=True))

    op.add_column(
        "customer_locations",
        sa.Column(
            "delete_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Region assignment is deferred to a future geofencing-based lookup;
    # coordinates are geocoded locally rather than sourced from Tripletex.
    op.alter_column("customer_locations", "region_id", nullable=True)
    op.alter_column("customer_locations", "latitude", nullable=True)
    op.alter_column("customer_locations", "longitude", nullable=True)

    op.create_table(
        "customer_location_sync_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_location_id",
            sa.Integer(),
            sa.ForeignKey("customer_locations.id"),
            nullable=False,
        ),
        sa.Column("change_type", customer_location_change_type, nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("customer_location_sync_log")
    customer_location_change_type.drop(op.get_bind(), checkfirst=True)

    op.alter_column("customer_locations", "longitude", nullable=False)
    op.alter_column("customer_locations", "latitude", nullable=False)
    op.alter_column("customer_locations", "region_id", nullable=False)

    op.drop_column("customer_locations", "delete_flag")

    for column in [
        "name",
        "country",
        "city",
        "postal_code",
        "address_line_2",
        "address_line_1",
        "url",
        "version",
    ]:
        op.drop_column("customer_locations", column)

    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS customer_locations_id_seq "
        "OWNED BY customer_locations.id"
    )
    op.execute(
        "ALTER TABLE customer_locations ALTER COLUMN id "
        "SET DEFAULT nextval('customer_locations_id_seq')"
    )
