"""Add index to speed up weekly report lookups by org and period.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-09
"""
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.create_index(
        "ix_reports_org_id_period_start",
        "reports",
        ["org_id", "period_start"],
    )


def downgrade() -> None:
    op.drop_index("ix_reports_org_id_period_start", table_name="reports")
