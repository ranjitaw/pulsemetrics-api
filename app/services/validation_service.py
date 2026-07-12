"""Validation for inbound analytics events, expressed as a chain of rules.

Each rule is a small, independently testable unit. Rules declare an
explicit `priority` (lower runs first) rather than relying on declaration
order in this module - declaration order is easy to accidentally change
during a merge conflict, and a silent reordering here can change which
error a malformed event gets flagged with.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

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


@dataclass
class EventContext:
    event_type: str
    occurred_at: datetime
    payload: dict


class ValidationRule(Protocol):
    priority: int
    #: If True and this rule raises, later rules are skipped rather than
    #: also being evaluated against a payload we already know is invalid.
    short_circuits: bool

    def check(self, ctx: EventContext) -> None: ...


@dataclass
class PayloadSizeRule:
    priority: int = 10
    short_circuits: bool = True

    def check(self, ctx: EventContext) -> None:
        encoded = json.dumps(ctx.payload)
        if len(encoded.encode("utf-8")) > settings.max_event_payload_bytes:
            raise ValidationError("payload exceeds max size", field="payload")


@dataclass
class RequiredFieldsRule:
    priority: int = 20
    short_circuits: bool = True

    def check(self, ctx: EventContext) -> None:
        required = REQUIRED_PAYLOAD_KEYS_BY_TYPE.get(ctx.event_type)
        if not required:
            return
        missing = required - ctx.payload.keys()
        if missing:
            raise ValidationError(
                f"missing required payload fields for {ctx.event_type!r}: {sorted(missing)}",
                field="payload",
            )


@dataclass
class FutureTimestampRule:
    priority: int = 30
    short_circuits: bool = False

    def check(self, ctx: EventContext) -> None:
        now = datetime.now(timezone.utc)
        skew = (ctx.occurred_at - now).total_seconds()
        tolerance = settings.event_future_skew_tolerance_seconds
        if skew > tolerance:
            raise ValidationError(
                f"occurred_at is {int(skew)}s ahead of server time "
                f"(tolerance is {tolerance}s) - check the sending client's clock",
                field="occurred_at",
            )


DEFAULT_RULES: list[ValidationRule] = sorted(
    [PayloadSizeRule(), RequiredFieldsRule(), FutureTimestampRule()],
    key=lambda rule: rule.priority,
)


def run_validation(ctx: EventContext, rules: list[ValidationRule] | None = None) -> None:
    """Run rules in priority order.

    A rule marked ``short_circuits`` stops the chain immediately on
    failure - this matters for rules like RequiredFieldsRule, since a
    downstream rule that assumes a field is present (e.g. reading
    ``payload["amount_cents"]``) would raise a confusing TypeError instead
    of the intended ValidationError if it ran against an incomplete
    payload. Non-short-circuiting rules still stop the request, but we
    finish evaluating the remaining non-short-circuiting rules first so a
    caller only ever sees one round of 422s instead of one-error-per-retry.
    """
    deferred: ValidationError | None = None
    for rule in rules or DEFAULT_RULES:
        try:
            rule.check(ctx)
        except ValidationError as exc:
            if rule.short_circuits:
                raise
            deferred = deferred or exc
    if deferred:
        raise deferred


def validate_event_payload(payload: dict) -> None:
    """Kept for backwards compatibility with callers that only need the
    size check (e.g. the webhook path, which doesn't have an event_type)."""
    PayloadSizeRule().check(EventContext(event_type="", occurred_at=datetime.now(timezone.utc), payload=payload))
