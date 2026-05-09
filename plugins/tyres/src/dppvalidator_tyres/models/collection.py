"""GDSO Collection v0.1 — at-end-of-first-life collection declaration.

The Collection declaration records the moment a tyre is removed
from a vehicle and enters the recovered-materials stream. The
collector identifies itself, the upstream Birth (by ``tyre_uuid``),
and the disposition routing (e.g. ``retread``, ``recycle``,
``landfill``).

Status: Pre-1.0 — GDSO Collection v0.1 is in draft; field names
may shift before 1.0.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dppvalidator_tyres.models.actor import TyreActor


class CollectionDisposition(str, Enum):
    """Where the tyre is routed after collection."""

    RETREAD = "retread"
    RECYCLE = "recycle"
    REUSE = "reuse"
    ENERGY_RECOVERY = "energy_recovery"
    LANDFILL = "landfill"
    UNKNOWN = "unknown"


class Collection(BaseModel):
    """GDSO Collection v0.1 — collector's at-end-of-first-life declaration.

    Wire shape:
        ``{"tyreUuid": "...", "collector": {...},
           "collectedAt": "...", "disposition": "retread",
           "facilityId": "https://example.com/facility/X"}``
    """

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, use_enum_values=True
    )

    tyre_uuid: UUID = Field(
        ...,
        alias="tyreUuid",
        description="UUID of the tyre being collected (matches Birth.tyreUuid).",
    )
    collector: TyreActor = Field(..., description="The actor collecting the tyre.")
    collected_at: datetime = Field(
        ...,
        alias="collectedAt",
        description="ISO 8601 timestamp of collection (timezone-aware required).",
    )
    disposition: CollectionDisposition = Field(
        ...,
        description=(
            "Where the tyre is routed: retread / recycle / reuse / "
            "energy_recovery / landfill / unknown."
        ),
    )
    facility_id: str | None = Field(
        default=None,
        alias="facilityId",
        description="Optional URI / DID of the collection facility.",
    )

    @field_validator("collected_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "Collection.collectedAt must be timezone-aware (typically UTC)."
            raise ValueError(msg)
        return value
