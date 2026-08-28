"""redefine customers to mirror Tripletex fields, add delete_flag, add customer_sync_log

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

customer_change_type = sa.Enum(
    "created", "updated", "deleted", "restored", name="customer_change_type"
)


def upgrade() -> None:
    # Existing demo data references the fictional customers about to be
    # removed; it is recreated by the restructured seed script afterward.
    op.execute(
        "TRUNCATE TABLE assignments, service_visits, contracts, "
        "customer_locations, customers CASCADE"
    )

    # customers.id is now populated with Tripletex's own customer id, not
    # an app-generated identity.
    op.execute("ALTER TABLE customers ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS customers_id_seq")

    op.add_column("customers", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column("customers", sa.Column("url", sa.String(), nullable=True))
    op.add_column(
        "customers", sa.Column("organization_number", sa.String(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("global_location_number", sa.Integer(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("supplier_number", sa.Integer(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("customer_number", sa.Integer(), nullable=True)
    )
    op.add_column("customers", sa.Column("is_supplier", sa.Boolean(), nullable=True))
    op.add_column("customers", sa.Column("is_customer", sa.Boolean(), nullable=True))
    op.add_column("customers", sa.Column("is_inactive", sa.Boolean(), nullable=True))
    op.add_column("customers", sa.Column("email", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("invoice_email", sa.String(), nullable=True))
    op.add_column(
        "customers", sa.Column("overdue_notice_email", sa.String(), nullable=True)
    )
    op.add_column("customers", sa.Column("phone_number", sa.String(), nullable=True))
    op.add_column(
        "customers", sa.Column("phone_number_mobile", sa.String(), nullable=True)
    )
    op.add_column("customers", sa.Column("description", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("language", sa.String(), nullable=True))
    op.add_column("customers", sa.Column("display_name", sa.String(), nullable=True))
    op.add_column(
        "customers", sa.Column("is_private_individual", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("single_customer_invoice", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("invoice_send_method", sa.String(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("email_attachment_type", sa.String(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("invoices_due_in", sa.Integer(), nullable=True)
    )
    op.add_column(
        "customers", sa.Column("invoices_due_in_type", sa.String(), nullable=True)
    )
    op.add_column("customers", sa.Column("is_factoring", sa.Boolean(), nullable=True))
    op.add_column(
        "customers",
        sa.Column("invoice_send_sms_notification", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column("invoice_sms_notification_number", sa.String(), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column("is_automatic_soft_reminder_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column("is_automatic_reminder_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column(
            "is_automatic_notice_of_debt_collection_enabled",
            sa.Boolean(),
            nullable=True,
        ),
    )
    op.add_column(
        "customers", sa.Column("discount_percentage", sa.Float(), nullable=True)
    )
    op.add_column("customers", sa.Column("website", sa.String(), nullable=True))

    op.add_column("customers", sa.Column("account_manager", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("department", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("postal_address", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("physical_address", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("delivery_address", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("category1", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("category2", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("category3", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("currency", JSONB(), nullable=True))
    op.add_column("customers", sa.Column("ledger_account", JSONB(), nullable=True))
    op.add_column(
        "customers", sa.Column("bank_account_presentation", JSONB(), nullable=True)
    )

    op.add_column(
        "customers",
        sa.Column(
            "delete_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "customer_sync_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False
        ),
        sa.Column("change_type", customer_change_type, nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("customer_sync_log")
    customer_change_type.drop(op.get_bind(), checkfirst=True)

    op.drop_column("customers", "delete_flag")

    for column in [
        "bank_account_presentation",
        "ledger_account",
        "currency",
        "category3",
        "category2",
        "category1",
        "delivery_address",
        "physical_address",
        "postal_address",
        "department",
        "account_manager",
        "website",
        "discount_percentage",
        "is_automatic_notice_of_debt_collection_enabled",
        "is_automatic_reminder_enabled",
        "is_automatic_soft_reminder_enabled",
        "invoice_sms_notification_number",
        "invoice_send_sms_notification",
        "is_factoring",
        "invoices_due_in_type",
        "invoices_due_in",
        "email_attachment_type",
        "invoice_send_method",
        "single_customer_invoice",
        "is_private_individual",
        "display_name",
        "language",
        "description",
        "phone_number_mobile",
        "phone_number",
        "overdue_notice_email",
        "invoice_email",
        "email",
        "is_inactive",
        "is_customer",
        "is_supplier",
        "customer_number",
        "supplier_number",
        "global_location_number",
        "organization_number",
        "url",
        "version",
    ]:
        op.drop_column("customers", column)

    op.execute("CREATE SEQUENCE IF NOT EXISTS customers_id_seq OWNED BY customers.id")
    op.execute(
        "ALTER TABLE customers ALTER COLUMN id SET DEFAULT nextval('customers_id_seq')"
    )
