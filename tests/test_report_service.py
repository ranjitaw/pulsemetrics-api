"""Tests for weekly report generation."""
from datetime import datetime, timezone

from app.models.event import Event
from app.services.report_service import generate_weekly_report


def test_generate_weekly_report_counts_events_by_type(db_session, sample_org, fake_redis):
    from app.services.cache_service import CacheService

    db_session.add_all(
        [
            Event(
                org_id=sample_org.id,
                event_type="page_view",
                payload={},
                occurred_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
                received_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
            ),
            Event(
                org_id=sample_org.id,
                event_type="page_view",
                payload={},
                occurred_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
                received_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            ),
            Event(
                org_id=sample_org.id,
                event_type="signup",
                payload={},
                occurred_at=datetime(2026, 5, 4, tzinfo=timezone.utc),
                received_at=datetime(2026, 5, 4, tzinfo=timezone.utc),
            ),
        ]
    )
    db_session.commit()
    cache = CacheService(redis_client=fake_redis)

    report = generate_weekly_report(
        db_session,
        sample_org.id,
        datetime(2026, 5, 1, tzinfo=timezone.utc),
        datetime(2026, 5, 8, tzinfo=timezone.utc),
        cache=cache,
    )

    assert report["total_events"] == 3
    assert report["counts_by_type"] == {"page_view": 2, "signup": 1}
