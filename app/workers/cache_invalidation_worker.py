"""Periodic sweep that invalidates stale report caches.

Runs every few minutes and invalidates the cache for any org that has
received new events since the worker's last pass.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models.event import Event
from app.services.cache_service import CacheService

_POLL_INTERVAL = timedelta(minutes=5)


def run_invalidation_sweep(since: datetime | None = None) -> int:
    since = since or (datetime.now(timezone.utc) - _POLL_INTERVAL)
    cache = CacheService()

    db = SessionLocal()
    try:
        stmt = select(Event.org_id).where(Event.received_at >= since).distinct()
        org_ids = [row[0] for row in db.execute(stmt).all()]
        for org_id in org_ids:
            cache.invalidate_org(org_id)
        return len(org_ids)
    finally:
        db.close()
