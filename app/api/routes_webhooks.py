"""Inbound webhook endpoints, one per upstream provider."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.webhook_service import DuplicateWebhookError, process_webhook

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{provider}", status_code=202)
async def receive_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    body = await request.json()
    external_id = body.get("id") or body.get("event_id", "")

    try:
        event = process_webhook(db, provider, external_id, body)
    except DuplicateWebhookError:
        logger.info("duplicate webhook ignored provider=%s external_id=%s", provider, external_id)
        return {"status": "duplicate_ignored"}

    return {"status": "accepted", "webhook_event_id": event.id}
