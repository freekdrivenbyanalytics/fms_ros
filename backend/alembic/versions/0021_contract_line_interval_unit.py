"""replace contract_lines.interval_days with interval_unit + interval_count

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-17

"""

from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

# (interval_unit, interval_count) -> equivalent day count, used only to find
# the nearest supported combination for each existing interval_days value.
_DAY_EQUIVALENTS = {
    ("week", 1): 7,
    ("week", 2): 14,
    ("week", 3): 21,
    ("week", 4): 28,
    ("month", 1): 30,
    ("month", 2): 60,
    ("month", 3): 90,
    ("quarter", 1): 91,
}


def _nearest_interval(interval_days: int) -> tuple[str, int]:
    """The supported (interval_unit, interval_count) whose day-equivalent is
    closest to interval_days; ties favor the smaller pair (dict iteration
    order above). Falls back to ("week", 4) - the pairs above already cover
    everything from 7 to 91 days, and this is only invoked for rows that
    actually exist, so a fallback beyond that range is not expected in
    practice."""
    best = min(
        _DAY_EQUIVALENTS.items(),
        key=lambda pair: abs(pair[1] - interval_days),
        default=None,
    )
    return best[0] if best is not None else ("week", 4)


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("contract_lines", sa.Column("interval_unit", sa.String(), nullable=True))
    op.add_column("contract_lines", sa.Column("interval_count", sa.Integer(), nullable=True))

    distinct_days = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT DISTINCT interval_days FROM contract_lines")
        )
    ]
    for interval_days in distinct_days:
        unit, count = _nearest_interval(interval_days)
        bind.execute(
            sa.text(
                "UPDATE contract_lines SET interval_unit = :unit, interval_count = :count "
                "WHERE interval_days = :interval_days"
            ),
            {"unit": unit, "count": count, "interval_days": interval_days},
        )

    op.alter_column("contract_lines", "interval_unit", nullable=False)
    op.alter_column("contract_lines", "interval_count", nullable=False)
    op.drop_column("contract_lines", "interval_days")


def downgrade() -> None:
    op.add_column("contract_lines", sa.Column("interval_days", sa.Integer(), nullable=True))

    bind = op.get_bind()
    for (unit, count), days in _DAY_EQUIVALENTS.items():
        bind.execute(
            sa.text(
                "UPDATE contract_lines SET interval_days = :days "
                "WHERE interval_unit = :unit AND interval_count = :count"
            ),
            {"days": days, "unit": unit, "count": count},
        )

    op.alter_column("contract_lines", "interval_days", nullable=False)
    op.drop_column("contract_lines", "interval_count")
    op.drop_column("contract_lines", "interval_unit")
