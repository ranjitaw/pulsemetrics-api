"""Add unique constraint on (provider, external_id) for webhook idempotency.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-29
"""
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_webhook_events_provider_external_id",
        "webhook_events",
        ["provider", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_webhook_events_provider_external_id", "webhook_events", type_="unique")
