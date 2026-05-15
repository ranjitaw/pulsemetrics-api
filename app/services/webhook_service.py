"""Inbound webhook ingestion."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook import WebhookEvent


def process_webhook(db: Session, provider: str, external_id: str, payload: dict) -> WebhookEvent:
    event = WebhookEvent(
        provider=provider,
        external_id=external_id,
        payload=payload,
        status="received",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event
