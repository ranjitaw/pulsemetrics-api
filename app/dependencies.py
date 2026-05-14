"""Shared FastAPI dependencies."""
from __future__ import annotations

import redis
from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()
_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def get_org_id(x_org_id: str = Header(..., alias="X-Org-Id")) -> str:
    """Resolve the calling organization from the request header.

    In production this is set by the API gateway after validating the
    caller's API key; we trust it here rather than re-validating per request.
    """
    if not x_org_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing X-Org-Id header")
    return x_org_id
