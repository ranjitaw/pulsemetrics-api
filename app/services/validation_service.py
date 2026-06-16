"""Validation for inbound analytics events beyond basic pydantic schema checks."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.config import get_settings

settings = get_settings()

REQUIRED_PAYLOAD_KEYS_BY_TYPE = {
    "signup": {"plan"},
    "invoice_paid": {"amount_cents", "currency"},
}


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


def validate_event_payload(payload: dict) -> None:
    encoded = json.dumps(payload)
    if len(encoded.encode("utf-8")) > settings.max_event_payload_bytes:
        raise ValidationError("payload exceeds max size", field="payload")


def validate_event_occurred_at(event_type: str, occurred_at: datetime) -> None:
    """Reject events with a client-reported timestamp too far in the future.

    We reject rather than clamp: silently clamping a bad client clock hides
    the underlying problem and can quietly corrupt an org's time series. A
    422 with the measured skew gives the customer (or our support team)
    something actionable to go on.
    """
    now = datetime.now(timezone.utc)
    skew = (occurred_at - now).total_seconds()
    tolerance = settings.event_future_skew_tolerance_seconds
    if skew > tolerance:
        raise ValidationError(
            f"occurred_at is {int(skew)}s ahead of server time "
            f"(tolerance is {tolerance}s) - check the sending client's clock",
            field="occurred_at",
        )


def validate_required_payload_fields(event_type: str, payload: dict) -> None:
    required = REQUIRED_PAYLOAD_KEYS_BY_TYPE.get(event_type)
    if not required:
        return
    missing = required - payload.keys()
    if missing:
        raise ValidationError(
            f"missing required payload fields for {event_type!r}: {sorted(missing)}",
            field="payload",
        )
