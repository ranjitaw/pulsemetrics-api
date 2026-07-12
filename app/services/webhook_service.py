"""Inbound webhook ingestion.

Providers like Stripe and Segment retry webhook deliveries on timeout or a
non-2xx response, which means the same event can arrive more than once. We
rely on a unique constraint on (provider, external_id) as the source of
truth for de-duplication rather than a SELECT-then-INSERT check in
application code, since the latter has a race window between two concurrent
deliveries for the same event.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.webhook import WebhookEvent


class DuplicateWebhookError(Exception):
    """Raised when a webhook with the same (provider, external_id) already exists."""


def process_webhook(db: Session, provider: str, external_id: str, payload: dict) -> WebhookEvent:
    event = WebhookEvent(
        provider=provider,
        external_id=external_id,
        payload=payload,
        status="received",
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        existing = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.provider == provider, WebhookEvent.external_id == external_id)
            .one()
        )
        raise DuplicateWebhookError(
            f"webhook {provider}:{external_id} already processed as webhook_event_id={existing.id}"
        ) from exc
    return event
