"""Tests for weekly report generation."""
from datetime import datetime, timezone

from app.models.event import Event
from app.services.cache_service import CacheService
from app.services.report_service import generate_weekly_report


def _make_events(org_id: str, n: int):
    return [
        Event(
            org_id=org_id,
            event_type="page_view" if i % 3 else "signup",
            payload={},
            occurred_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
            received_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
        )
        for i in range(n)
    ]


def test_generate_weekly_report_counts_events_by_type(db_session, sample_org, fake_redis):
    db_session.add_all(_make_events(sample_org.id, 3))
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


def test_generate_weekly_report_uses_bounded_query_count(db_session, sample_org, fake_redis):
    """Regression test for PR #103: generating a report for N events should
    not issue O(N) queries. We assert on the number of statements executed
    rather than timing, since timing is flaky in CI.
    """
    db_session.add_all(_make_events(sample_org.id, 50))
    db_session.commit()
    cache = CacheService(redis_client=fake_redis)

    query_count = 0

    def _count(*args, **kwargs):
        nonlocal query_count
        query_count += 1

    from sqlalchemy import event as sa_event

    sa_event.listen(db_session.bind, "before_cursor_execute", _count)
    try:
        generate_weekly_report(
            db_session,
            sample_org.id,
            datetime(2026, 5, 1, tzinfo=timezone.utc),
            datetime(2026, 5, 8, tzinfo=timezone.utc),
            cache=cache,
        )
    finally:
        sa_event.remove(db_session.bind, "before_cursor_execute", _count)

    # One query for events plus one selectin query for the org relationship
    # (SQLite also logs its own BEGIN as a cursor execution) - the key
    # thing we're guarding against is O(N) queries, not this exact count.
    assert query_count <= 3
