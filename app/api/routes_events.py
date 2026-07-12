"""Event ingestion endpoint."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_org_id
from app.models.event import Event
from app.schemas.event_schemas import EventCreate, EventOut
from app.services.report_service import record_event_and_invalidate
from app.services.validation_service import (
    validate_event_occurred_at,
    validate_event_payload,
    validate_required_payload_fields,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=EventOut, status_code=201)
def ingest_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_org_id),
) -> Event:
    # Validate the full payload before touching the database. `db` here is
    # already a live session/connection from the pool (see get_db); running
    # validation first means a malformed request never holds a pooled
    # connection open while we build the ORM object and validation error
    # messages, which matters under load when the pool is close to its
    # ceiling.
    validate_event_payload(body.payload)
    validate_event_occurred_at(body.event_type, body.occurred_at)
    validate_required_payload_fields(body.event_type, body.payload)

    event = Event(
        org_id=org_id,
        event_type=body.event_type,
        payload=body.payload,
        occurred_at=body.occurred_at,
        received_at=datetime.now(timezone.utc),
        source=body.source,
    )
    record_event_and_invalidate(db, event)
    logger.info("invalidated report cache for org=%s after event write", org_id)
    db.refresh(event)
    return event
