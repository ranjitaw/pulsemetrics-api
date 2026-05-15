"""Redis-backed cache for expensive-to-compute report data."""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from app.config import get_settings
from app.dependencies import get_redis

settings = get_settings()


class CacheService:
    def __init__(self, redis_client=None):
        self._redis = redis_client or get_redis()

    def _key(self, org_id: str, period_key: str) -> str:
        return f"{settings.report_cache_prefix}:{org_id}:{period_key}"

    def get_report(self, org_id: str, period_key: str) -> dict[str, Any] | None:
        raw = self._redis.get(self._key(org_id, period_key))
        return json.loads(raw) if raw else None

    def set_report(self, org_id: str, period_key: str, data: dict[str, Any]) -> None:
        self._redis.set(
            self._key(org_id, period_key),
            json.dumps(data),
            ex=timedelta(seconds=settings.cache_ttl_seconds),
        )

    def invalidate_org(self, org_id: str) -> None:
        """Invalidate all cached reports for an org.

        Called from the nightly cache-invalidation worker when it detects
        new events for an org since the last sweep.
        """
        pattern = f"{settings.report_cache_prefix}:{org_id}:*"
        keys = list(self._redis.scan_iter(match=pattern))
        if keys:
            self._redis.delete(*keys)
