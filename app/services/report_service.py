"""Weekly report generation."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.services.cache_service import CacheService


def _period_key(period_start: datetime, period_end: datetime) -> str:
    return f"{period_start.date().isoformat()}_{period_end.date().isoformat()}"


def generate_weekly_report(
    db: Session,
    org_id: str,
    period_start: datetime,
    period_end: datetime,
    cache: CacheService | None = None,
) -> dict:
    cache = cache or CacheService()
    period_key = _period_key(period_start, period_end)

    cached = cache.get_report(org_id, period_key)
    if cached is not None:
        return cached

    # selectinload issues a single extra query (SELECT ... WHERE org_id IN
    # (...)) instead of one lazy-load per event. We use selectinload rather
    # than joinedload here specifically because joinedload would produce a
    # cartesian product against the events rows for large weeks - the org
    # row would be repeated once per event in the result set.
    events = (
        db.query(Event)
        .options(selectinload(Event.organization))
        .filter(
            Event.org_id == org_id,
            Event.occurred_at >= period_start,
            Event.occurred_at < period_end,
        )
        .all()
    )

    counts_by_type: dict[str, int] = {}
    for event in events:
        counts_by_type[event.event_type] = counts_by_type.get(event.event_type, 0) + 1

    report = {
        "org_id": org_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "total_events": len(events),
        "counts_by_type": counts_by_type,
    }
    cache.set_report(org_id, period_key, report)
    return report


def record_event_and_invalidate(db: Session, event: Event, cache: CacheService | None = None) -> None:
    """Persist a new event and invalidate the org's cached reports inline.

    Invalidating here - synchronously with the write - closes the race
    window between a write landing and the cache_invalidation_worker's next
    sweep (up to 5 minutes). The worker sweep still runs as a safety net for
    invalidation paths we haven't wired up yet (e.g. bulk imports).
    """
    cache = cache or CacheService()
    db.add(event)
    db.flush()
    cache.invalidate_org(event.org_id)
