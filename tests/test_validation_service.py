"""Tests for event payload validation."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.validation_service import (
    ValidationError,
    validate_event_occurred_at,
    validate_event_payload,
    validate_required_payload_fields,
)


def test_validate_event_payload_accepts_small_payload():
    validate_event_payload({"button": "signup_cta"})


def test_validate_event_payload_rejects_oversized_payload():
    huge_payload = {"blob": "x" * 40_000}

    with pytest.raises(ValidationError):
        validate_event_payload(huge_payload)


def test_validate_event_occurred_at_accepts_slightly_stale_timestamp():
    occurred_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    validate_event_occurred_at("page_view", occurred_at)


def test_validate_event_occurred_at_rejects_far_future_timestamp():
    occurred_at = datetime.now(timezone.utc) + timedelta(hours=2)

    with pytest.raises(ValidationError) as exc_info:
        validate_event_occurred_at("page_view", occurred_at)

    assert "ahead of server time" in str(exc_info.value)


def test_validate_event_occurred_at_allows_small_clock_skew():
    occurred_at = datetime.now(timezone.utc) + timedelta(seconds=30)

    validate_event_occurred_at("page_view", occurred_at)


def test_validate_required_payload_fields_missing_raises():
    with pytest.raises(ValidationError):
        validate_required_payload_fields("signup", {})


def test_validate_required_payload_fields_present_ok():
    validate_required_payload_fields("signup", {"plan": "pro"})


def test_validate_required_payload_fields_unknown_event_type_is_noop():
    validate_required_payload_fields("some_custom_event", {})
