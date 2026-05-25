"""Tests for CacheService."""
from datetime import datetime, timezone

from app.models.event import Event
from app.services.cache_service import CacheService
from app.services.report_service import generate_weekly_report, record_event_and_invalidate


def test_set_and_get_report_round_trips(fake_redis):
    cache = CacheService(redis_client=fake_redis)
    cache.set_report("org_123", "2026-05-01_2026-05-08", {"total_events": 42})

    result = cache.get_report("org_123", "2026-05-01_2026-05-08")

    assert result == {"total_events": 42}


def test_get_report_returns_none_when_missing(fake_redis):
    cache = CacheService(redis_client=fake_redis)

    assert cache.get_report("org_123", "missing_period") is None


def test_invalidate_org_removes_only_that_orgs_keys(fake_redis):
    cache = CacheService(redis_client=fake_redis)
    cache.set_report("org_123", "week1", {"total_events": 1})
    cache.set_report("org_456", "week1", {"total_events": 2})

    cache.invalidate_org("org_123")

    assert cache.get_report("org_123", "week1") is None
    assert cache.get_report("org_456", "week1") == {"total_events": 2}


def test_report_reflects_new_events_written_after_first_read(db_session, sample_org, fake_redis):
    """Regression test for the stale-cache race: a write immediately after a
    cached read must not be masked until the invalidation worker's next
    sweep. See PR #101.
    """
    cache = CacheService(redis_client=fake_redis)
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 8, tzinfo=timezone.utc)

    generate_weekly_report(db_session, sample_org.id, period_start, period_end, cache=cache)

    new_event = Event(
        org_id=sample_org.id,
        event_type="signup",
        payload={},
        occurred_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
        received_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    # Go through the same write path the API uses, since that's what
    # actually triggers synchronous invalidation.
    record_event_and_invalidate(db_session, new_event, cache=cache)
    db_session.commit()

    # Without synchronous invalidation on write, this would still return the
    # cached report with total_events == 0, hiding the new signup event for
    # up to the worker's 5-minute poll interval.
    report = generate_weekly_report(db_session, sample_org.id, period_start, period_end, cache=cache)

    assert report["total_events"] == 1
