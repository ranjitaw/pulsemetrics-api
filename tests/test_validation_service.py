"""Tests for the event validation rule chain."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.services.validation_service import (
    DEFAULT_RULES,
    EventContext,
    FutureTimestampRule,
    RequiredFieldsRule,
    ValidationError,
    run_validation,
    validate_event_payload,
)


def test_validate_event_payload_accepts_small_payload():
    validate_event_payload({"button": "signup_cta"})


def test_validate_event_payload_rejects_oversized_payload():
    with pytest.raises(ValidationError):
        validate_event_payload({"blob": "x" * 40_000})


def test_default_rules_are_sorted_by_priority():
    priorities = [rule.priority for rule in DEFAULT_RULES]
    assert priorities == sorted(priorities)


def test_run_validation_passes_for_well_formed_event():
    ctx = EventContext(
        event_type="signup",
        occurred_at=datetime.now(timezone.utc),
        payload={"plan": "pro"},
    )
    run_validation(ctx)


def test_run_validation_rejects_future_timestamp():
    ctx = EventContext(
        event_type="page_view",
        occurred_at=datetime.now(timezone.utc) + timedelta(hours=1),
        payload={},
    )
    with pytest.raises(ValidationError, match="ahead of server time"):
        run_validation(ctx)


def test_required_fields_rule_short_circuits_before_downstream_rules_run():
    """RequiredFieldsRule is marked short_circuits=True specifically so a
    rule further down the chain never has to reason about a payload
    that's already known to be incomplete. This test uses a rule that
    would raise a TypeError (not ValidationError) if it ran against a
    missing field, to prove it never actually runs.
    """

    @dataclass
    class ExplodesOnMissingField:
        priority: int = 999
        short_circuits: bool = False

        def check(self, ctx: EventContext) -> None:
            # Would raise KeyError if RequiredFieldsRule hadn't already
            # stopped the chain.
            _ = ctx.payload["plan"].upper()

    rules = [RequiredFieldsRule(), ExplodesOnMissingField()]
    ctx = EventContext(event_type="signup", occurred_at=datetime.now(timezone.utc), payload={})

    with pytest.raises(ValidationError, match="missing required payload fields"):
        run_validation(ctx, rules=rules)


def test_non_short_circuiting_rule_failure_still_runs_later_rules():
    """FutureTimestampRule doesn't short-circuit, so a rule after it should
    still execute (and if it also fails, we still only see one exception,
    not a crash)."""
    calls: list[str] = []

    @dataclass
    class RecordsCall:
        priority: int = 999
        short_circuits: bool = False

        def check(self, ctx: EventContext) -> None:
            calls.append("recorded")

    ctx = EventContext(
        event_type="page_view",
        occurred_at=datetime.now(timezone.utc) + timedelta(hours=1),
        payload={},
    )
    rules = [FutureTimestampRule(), RecordsCall()]

    with pytest.raises(ValidationError):
        run_validation(ctx, rules=rules)

    assert calls == ["recorded"]
