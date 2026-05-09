"""GDSO Recycling v0.1 — at-end-of-life recycling declaration.

The Recycling declaration is the *terminal* event in a tyre's
lifecycle: the tyre is shredded, devulcanised, pyrolysed, or
otherwise broken down into recovered materials. The declaration
identifies the recycler, the method, and the recovered-mass
fraction routed to each downstream stream.

Status: Pre-1.0 — GDSO Recycling v0.1 is in draft.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from dppvalidator_tyres.models.actor import TyreActor


class RecyclingMethod(str, Enum):
    """Recycling method per the GDSO Recycling v0.1 enumeration.

    The four canonical industry methods plus ``other`` for emerging
    technologies (e.g. cryogenic shred, microwave devulcanisation):

    - ``mechanical`` — shred → granulate → crumb rubber.
    - ``pyrolysis`` — thermal decomposition into oil, gas, char, steel.
    - ``devulcanisation`` — chemical / thermomechanical de-cross-linking.
    - ``energy_recovery`` — combustion in a cement kiln or power plant.
    """

    MECHANICAL = "mechanical"
    PYROLYSIS = "pyrolysis"
    DEVULCANISATION = "devulcanisation"
    ENERGY_RECOVERY = "energy_recovery"
    OTHER = "other"


class RecoveryFraction(BaseModel):
    """Recovery fraction for one downstream material stream.

    Wire shape:
        ``{"materialName": "Steel wire", "massFractionRecovered": 0.12}``
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    material_name: str = Field(
        ...,
        alias="materialName",
        min_length=1,
        description="Name of the recovered material stream.",
    )
    mass_fraction_recovered: Decimal = Field(
        ...,
        alias="massFractionRecovered",
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Fraction (0..1) of the input tyre's mass routed to this stream.",
    )


class Recycling(BaseModel):
    """GDSO Recycling v0.1 — recycler's at-end-of-life declaration.

    Wire shape:
        ``{"tyreUuid": "...", "recycler": {...},
           "recycledAt": "...", "method": "mechanical",
           "recoveryFractions": [...]}``
    """

    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, use_enum_values=True
    )

    tyre_uuid: UUID = Field(
        ...,
        alias="tyreUuid",
        description="UUID of the tyre being recycled.",
    )
    recycler: TyreActor = Field(..., description="The actor performing the recycling.")
    recycled_at: datetime = Field(
        ...,
        alias="recycledAt",
        description="ISO 8601 timestamp of the recycling event (timezone-aware required).",
    )
    method: RecyclingMethod = Field(
        ...,
        description="Recycling method (mechanical / pyrolysis / devulcanisation / energy_recovery / other).",
    )
    recovery_fractions: list[RecoveryFraction] | None = Field(
        default=None,
        alias="recoveryFractions",
        description=(
            "Optional per-stream recovery fractions. When present, the sum "
            "of mass_fraction_recovered values must be ≤ 1.0."
        ),
    )

    @field_validator("recycled_at")
    @classmethod
    def _require_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = "Recycling.recycledAt must be timezone-aware (typically UTC)."
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _recovery_fractions_sum_within_one(self) -> Recycling:
        if not self.recovery_fractions:
            return self
        total = sum(
            (f.mass_fraction_recovered for f in self.recovery_fractions),
            start=Decimal("0"),
        )
        if total > Decimal("1.0001"):
            msg = (
                f"Recycling.recoveryFractions sum {total} exceeds 1.0 — "
                "recovered mass cannot exceed input mass."
            )
            raise ValueError(msg)
        return self
