"""Validation for inbound analytics events beyond basic schema checks."""
from __future__ import annotations

from app.config import get_settings

settings = get_settings()


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


def validate_event_payload(payload: dict) -> None:
    import json

    encoded = json.dumps(payload)
    if len(encoded.encode("utf-8")) > settings.max_event_payload_bytes:
        raise ValidationError("payload exceeds max size", field="payload")
