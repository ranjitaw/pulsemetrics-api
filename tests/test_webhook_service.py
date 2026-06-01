"""Tests for webhook ingestion."""
import pytest

from app.services.webhook_service import DuplicateWebhookError, process_webhook


def test_process_webhook_persists_event(db_session):
    event = process_webhook(db_session, "stripe", "evt_123", {"type": "invoice.paid"})
    db_session.commit()

    assert event.id is not None
    assert event.status == "received"
    assert event.external_id == "evt_123"


def test_process_webhook_rejects_duplicate_external_id(db_session):
    process_webhook(db_session, "stripe", "evt_dup", {"type": "invoice.paid"})
    db_session.commit()

    with pytest.raises(DuplicateWebhookError):
        process_webhook(db_session, "stripe", "evt_dup", {"type": "invoice.paid"})


def test_same_external_id_allowed_across_different_providers(db_session):
    first = process_webhook(db_session, "stripe", "evt_1", {"type": "invoice.paid"})
    db_session.commit()
    second = process_webhook(db_session, "segment", "evt_1", {"type": "track"})
    db_session.commit()

    assert first.id != second.id
