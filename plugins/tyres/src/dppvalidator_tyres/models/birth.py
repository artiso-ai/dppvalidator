"""GDSO Birth v0.9 declaration — at-mould tyre birth event.

The Birth declaration is the *canonical* identity declaration for a
manufactured tyre. Every subsequent declaration (Collection,
Retread, Recycling) references the Birth's ``tyre_uuid`` so the
lifecycle history can be reconstructed.

Status: Pre-1.0 — GDSO Birth v0.9 is the current published spec but
field names may shift before 1.0.

Wire shape (minimal, ~paraphrased from GDSO public docs):

    {
        "tyreUuid": "550e8400-e29b-41d4-a716-446655440000",
        "manufacturer": {
            "id": "https://example.com/operator/acme",
            "name": "ACME Tyres",
            "lei": "529900T8BM49AURSDO55"
        },
        "manufacturedAt": "2026-04-15T10:30:00+00:00",
        "dotMarking": {
            "plantCode": "B7",
            "sizeCode": "5K",
            "weekOfYear": 16,
            "year": 2026
        },
        "size": {
            "sectionWidth": 205,
            "aspectRatio": 55,
            "rimDiameter": 16,
            "loadIndex": 91,
            "speedRating": "V"
        }
    }
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dppvalidator_tyres.models.actor import TyreActor

# DOT plant code: 1-2 alphanumeric chars (per US DOT 49 CFR 574).
_DOT_PLANT_RE = re.compile(r"^[0-9A-Z]{1,2}$")
# DOT size code: 1-2 alphanumeric chars per the manufacturer-specific
# table (49 CFR 574 leaves the encoding to each plant).
_DOT_SIZE_RE = re.compile(r"^[0-9A-Z]{1,4}$")
# ETRTO standard speed-rating letters. Q–Y per GB-T 2977; the very
# rare W/Y/(Y) sub-letters are accepted as bare letters.
_ETRTO_SPEED_RATINGS = frozenset(
    ["L", "M", "N", "P", "Q", "R", "S", "T", "U", "H", "V", "W", "Y", "Z"]
)


class DOTMarking(BaseModel):
    """DOT marking on the tyre sidewall (US DOT 49 CFR 574).

    Wire shape:
        ``{"plantCode": "B7", "sizeCode": "5K",
           "weekOfYear": 16, "year": 2026}``
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    plant_code: str = Field(
        ..., alias="plantCode", description="DOT plant code (1-2 alphanumeric chars)."
    )
    size_code: str = Field(..., alias="sizeCode", description="Manufacturer-specific size code.")
    week_of_year: int = Field(
        ...,
        alias="weekOfYear",
        ge=1,
        le=53,
        description="ISO week number of manufacture (1-53).",
    )
    year: int = Field(
        ...,
        ge=1971,  # DOT marking system standardised in 1971.
        le=2100,
        description="Year of manufacture (4-digit).",
    )

    @field_validator("plant_code")
    @classmethod
    def _validate_plant_code(cls, value: str) -> str:
        if not _DOT_PLANT_RE.match(value):
            msg = f"DOT plant code {value!r} must be 1-2 alphanumeric uppercase chars."
            raise ValueError(msg)
        return value

    @field_validator("size_code")
    @classmethod
    def _validate_size_code(cls, value: str) -> str:
        if not _DOT_SIZE_RE.match(value):
            msg = f"DOT size code {value!r} must be 1-4 alphanumeric uppercase chars."
            raise ValueError(msg)
        return value


class TyreSize(BaseModel):
    """ETRTO tyre size designation.

    Wire shape:
        ``{"sectionWidth": 205, "aspectRatio": 55, "rimDiameter": 16,
           "loadIndex": 91, "speedRating": "V"}``
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    section_width: int = Field(
        ...,
        alias="sectionWidth",
        ge=125,
        le=445,
        description="Section width in millimetres (ETRTO standard range 125-445).",
    )
    aspect_ratio: int = Field(
        ...,
        alias="aspectRatio",
        ge=20,
        le=95,
        description="Aspect ratio as a percentage (20-95).",
    )
    rim_diameter: int = Field(
        ...,
        alias="rimDiameter",
        ge=10,
        le=24,
        description="Rim diameter in inches (10-24 covers the passenger / light-truck range).",
    )
    load_index: int = Field(
        ...,
        alias="loadIndex",
        ge=0,
        le=200,
        description="ETRTO load index (0-200 covers the passenger / light-truck range).",
    )
    speed_rating: str = Field(
        ...,
        alias="speedRating",
        description="ETRTO speed-rating letter (L, M, N, P, Q, R, S, T, U, H, V, W, Y, Z).",
    )

    @field_validator("speed_rating")
    @classmethod
    def _validate_speed_rating(cls, value: str) -> str:
        upper = value.upper()
        if upper not in _ETRTO_SPEED_RATINGS:
            msg = (
                f"Speed rating {value!r} is not in the ETRTO standard set "
                f"({sorted(_ETRTO_SPEED_RATINGS)})."
            )
            raise ValueError(msg)
        return upper


class Birth(BaseModel):
    """GDSO Birth v0.9 — manufacturer's at-mould tyre declaration.

    Wire shape (minimal):
        ``{"tyreUuid": "...", "manufacturer": {...},
           "manufacturedAt": "...", "dotMarking": {...},
           "size": {...}}``

    Cardinality:

    - ``tyre_uuid``: required (1) — globally unique tyre identifier.
    - ``manufacturer``: required (1) — the actor that produced the tyre.
    - ``manufactured_at``: required (1) — ISO 8601 timestamp.
    - ``dot_marking``: required (1) — DOT 49 CFR 574 marking.
    - ``size``: required (1) — ETRTO size + load + speed rating.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    tyre_uuid: UUID = Field(
        ...,
        alias="tyreUuid",
        description="UUID v4 identifying the physical tyre across its lifecycle.",
    )
    manufacturer: TyreActor = Field(..., description="The manufacturer (an :class:`TyreActor`).")
    manufactured_at: datetime = Field(
        ...,
        alias="manufacturedAt",
        description="ISO 8601 timestamp of manufacture (timezone-aware required).",
    )
    dot_marking: DOTMarking = Field(..., alias="dotMarking", description="DOT 49 CFR 574 marking.")
    size: TyreSize = Field(..., description="ETRTO size + load + speed rating.")

    @field_validator("manufactured_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "Birth.manufacturedAt must be timezone-aware (typically UTC)."
            raise ValueError(msg)
        return value
