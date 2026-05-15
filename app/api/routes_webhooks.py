"""Inbound webhook endpoints, one per upstream provider."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.webhook_service import process_webhook

router = APIRouter()


@router.post("/{provider}", status_code=202)
async def receive_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    body = await request.json()
    external_id = body.get("id") or body.get("event_id", "")
    event = process_webhook(db, provider, external_id, body)
    return {"status": "accepted", "webhook_event_id": event.id}
