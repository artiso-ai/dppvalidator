"""GDSO Retread v0.1 — tyre-renewal declaration.

The Retread declaration records the renewal of a previously-used
tyre by a retreader. The declaration references the upstream Birth
(by ``tyre_uuid``) and may chain through prior Retread events for
multi-cycle retreaded casings.

Status: Pre-1.0 — GDSO Retread v0.1 is in draft.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dppvalidator_tyres.models.actor import TyreActor


class RetreadProcess(str, Enum):
    """Retread process per ETRTO Recommendations.

    The two industry-standard processes are:

    - ``hot_cure`` (mould cure): old casing + uncured rubber tread,
      vulcanised in a heated mould.
    - ``cold_cure`` (pre-cured tread): old casing + already-vulcanised
      tread strip, bonded with a thin uncured layer in an autoclave.
    """

    HOT_CURE = "hot_cure"
    COLD_CURE = "cold_cure"
    OTHER = "other"


class Retread(BaseModel):
    """GDSO Retread v0.1 — retreader's renewal declaration.

    Wire shape:
        ``{"tyreUuid": "...", "retreader": {...},
           "retreadedAt": "...", "process": "cold_cure",
           "previousBirthUuid": "..."}``
    """

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, use_enum_values=True
    )

    tyre_uuid: UUID = Field(
        ...,
        alias="tyreUuid",
        description="UUID of the renewed tyre. Stays stable across retread cycles.",
    )
    retreader: TyreActor = Field(..., description="The actor performing the retread.")
    retreaded_at: datetime = Field(
        ...,
        alias="retreadedAt",
        description="ISO 8601 timestamp of the retread event (timezone-aware required).",
    )
    process: RetreadProcess = Field(
        ...,
        description="Retread process — hot_cure / cold_cure / other.",
    )
    previous_birth_uuid: UUID = Field(
        ...,
        alias="previousBirthUuid",
        description=(
            "UUID of the upstream Birth declaration. Required for chain "
            "reconstruction; the validator's TYR006 rule pins this."
        ),
    )
    cycle_number: int | None = Field(
        default=None,
        alias="cycleNumber",
        ge=1,
        le=5,
        description="Optional retread cycle (1 = first retread).",
    )

    @field_validator("retreaded_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "Retread.retreadedAt must be timezone-aware (typically UTC)."
            raise ValueError(msg)
        return value
