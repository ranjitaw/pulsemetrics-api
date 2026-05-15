"""Weekly report generation."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

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

    events = (
        db.query(Event)
        .filter(
            Event.org_id == org_id,
            Event.occurred_at >= period_start,
            Event.occurred_at < period_end,
        )
        .all()
    )

    counts_by_type: dict[str, int] = {}
    for event in events:
        # NOTE: touching event.organization here triggers a lazy load per
        # row since the relationship isn't eagerly loaded above.
        _ = event.organization.plan
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
