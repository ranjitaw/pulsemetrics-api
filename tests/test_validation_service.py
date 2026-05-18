"""Tests for event payload validation."""
import pytest

from app.services.validation_service import ValidationError, validate_event_payload


def test_validate_event_payload_accepts_small_payload():
    validate_event_payload({"button": "signup_cta"})


def test_validate_event_payload_rejects_oversized_payload():
    huge_payload = {"blob": "x" * 40_000}

    with pytest.raises(ValidationError):
        validate_event_payload(huge_payload)
