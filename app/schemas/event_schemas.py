"""Pydantic schemas for the event ingestion API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=128)
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="api")

    @field_validator("event_type")
    @classmethod
    def event_type_must_be_snake_case(cls, value: str) -> str:
        if not value.replace("_", "").isalnum():
            raise ValueError("event_type must be alphanumeric with underscores")
        return value


class EventOut(BaseModel):
    id: int
    org_id: str
    event_type: str
    occurred_at: datetime
    received_at: datetime
    source: str

    model_config = {"from_attributes": True}
