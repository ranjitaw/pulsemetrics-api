"""Tests for CacheService."""
from app.services.cache_service import CacheService


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
