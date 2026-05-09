"""TyreLifecycleHistory v1 — aggregate of one tyre's full lifecycle.

The history wraps one :class:`Birth` declaration plus a chronologically-
ordered list of subsequent events (Collection, Retread, Recycling).
Every event must reference the Birth's ``tyre_uuid``; the
:func:`_chain_consistent` validator enforces this.

Status: Pre-1.0 — depends on Birth v0.9 / Recycling v0.1 which are
themselves moving.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, model_validator

from dppvalidator_tyres.models.birth import Birth
from dppvalidator_tyres.models.collection import Collection
from dppvalidator_tyres.models.recycling import Recycling
from dppvalidator_tyres.models.retread import Retread


class _CollectionEvent(BaseModel):
    """Discriminated wrapper for a Collection event."""

    model_config = ConfigDict(populate_by_name=True)
    type: Literal["collection"] = "collection"
    declaration: Collection


class _RetreadEvent(BaseModel):
    """Discriminated wrapper for a Retread event."""

    model_config = ConfigDict(populate_by_name=True)
    type: Literal["retread"] = "retread"
    declaration: Retread


class _RecyclingEvent(BaseModel):
    """Discriminated wrapper for a Recycling event."""

    model_config = ConfigDict(populate_by_name=True)
    type: Literal["recycling"] = "recycling"
    declaration: Recycling


def _event_discriminator(value: Any) -> str | None:
    """Pick the event subclass based on the ``type`` field.

    Pydantic v2 calls this with either a parsed model instance or a
    raw dict (depending on whether the input had already been
    pre-validated). We accept :class:`Any` because the discriminator
    runs ahead of model validation and the narrowing behaviour
    differs between input shapes.
    """
    if isinstance(value, dict):
        type_value = value.get("type")
        if isinstance(type_value, str):
            return type_value
        return None
    return getattr(value, "type", None)


TyreLifecycleEvent = Annotated[
    Annotated[_CollectionEvent, Tag("collection")]
    | Annotated[_RetreadEvent, Tag("retread")]
    | Annotated[_RecyclingEvent, Tag("recycling")],
    Discriminator(_event_discriminator),
]


class TyreLifecycleHistory(BaseModel):
    """Aggregate of one tyre's lifecycle (Birth + chronological events).

    Wire shape:
        ``{"birth": {...},
           "events": [{"type": "collection", "declaration": {...}}, ...]}``

    Cardinality:

    - ``birth``: required (1).
    - ``events``: optional list, may be empty.

    Cross-event invariants:

    - Every event's ``tyre_uuid`` matches the birth's.
    - Events are chronologically ordered (each event's timestamp is
      ≥ the previous one).
    - At most one Recycling event (the lifecycle's terminator).
    - No events after a Recycling event.
    """

    model_config = ConfigDict(populate_by_name=True)

    birth: Birth = Field(..., description="The tyre's at-mould Birth declaration.")
    events: list[TyreLifecycleEvent] = Field(
        default_factory=list,
        description="Chronologically-ordered subsequent events.",
    )

    @model_validator(mode="after")
    def _chain_consistent(self) -> TyreLifecycleHistory:
        birth_uuid = self.birth.tyre_uuid
        last_ts: datetime | None = self.birth.manufactured_at
        recycling_seen = False
        for i, event in enumerate(self.events):
            decl = event.declaration
            if decl.tyre_uuid != birth_uuid:
                msg = (
                    f"TyreLifecycleHistory.events[{i}] references tyre_uuid="
                    f"{decl.tyre_uuid!r} which does not match the Birth "
                    f"({birth_uuid!r})."
                )
                raise ValueError(msg)
            event_ts = _event_timestamp(decl)
            if last_ts is not None and event_ts < last_ts:
                msg = (
                    f"TyreLifecycleHistory.events[{i}] timestamp "
                    f"{event_ts.isoformat()} predates the previous event / "
                    f"Birth ({last_ts.isoformat()}). Events must be in "
                    "chronological order."
                )
                raise ValueError(msg)
            last_ts = event_ts
            if event.type == "recycling":
                if recycling_seen:
                    msg = (
                        "TyreLifecycleHistory: only one Recycling event "
                        "permitted (the lifecycle terminator)."
                    )
                    raise ValueError(msg)
                recycling_seen = True
            elif recycling_seen:
                msg = (
                    f"TyreLifecycleHistory.events[{i}] follows a Recycling "
                    "event; nothing may happen after end-of-life."
                )
                raise ValueError(msg)
        return self


def _event_timestamp(decl: Collection | Retread | Recycling) -> datetime:
    """Return the canonical timestamp for an event declaration."""
    if isinstance(decl, Collection):
        return decl.collected_at
    if isinstance(decl, Retread):
        return decl.retreaded_at
    return decl.recycled_at
