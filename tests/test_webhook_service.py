"""Tests for webhook ingestion."""
from app.services.webhook_service import process_webhook


def test_process_webhook_persists_event(db_session):
    event = process_webhook(db_session, "stripe", "evt_123", {"type": "invoice.paid"})

    assert event.id is not None
    assert event.status == "received"
    assert event.external_id == "evt_123"
