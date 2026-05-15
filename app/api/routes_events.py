"""Event ingestion endpoint."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_org_id
from app.models.event import Event
from app.schemas.event_schemas import EventCreate, EventOut
from app.services.validation_service import validate_event_payload

router = APIRouter()


@router.post("", response_model=EventOut, status_code=201)
def ingest_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_org_id),
) -> Event:
    validate_event_payload(body.payload)

    event = Event(
        org_id=org_id,
        event_type=body.event_type,
        payload=body.payload,
        occurred_at=body.occurred_at,
        received_at=datetime.now(timezone.utc),
        source=body.source,
    )
    db.add(event)
    db.flush()
    db.refresh(event)
    return event
