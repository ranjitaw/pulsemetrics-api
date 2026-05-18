"""Shared pytest fixtures."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import Organization


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def sample_org(db_session):
    org = Organization(id="org_123", name="Acme Inc", plan="pro", created_at=datetime.now(timezone.utc))
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture()
def fake_redis():
    store: dict[str, str] = {}
    client = MagicMock()
    client.get.side_effect = lambda k: store.get(k)
    client.set.side_effect = lambda k, v, ex=None: store.__setitem__(k, v)
    client.scan_iter.side_effect = lambda match: [k for k in store if _matches(k, match)]
    client.delete.side_effect = lambda *keys: [store.pop(k, None) for k in keys]
    return client


def _matches(key: str, pattern: str) -> bool:
    prefix = pattern.rstrip("*")
    return key.startswith(prefix)
