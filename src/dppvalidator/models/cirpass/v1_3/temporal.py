"""Temporal types for CIRPASS DPP reference structure v1.3.0.

Phase 3 task 3.12 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G17).
UNTP's `validFrom`/`validUntil` and `issuanceDate` map onto CIRPASS's
`EffectivePeriod` and `IssuedAt` here; the Phase 5 mapping shim
(``compat/untp_0_7_to_cirpass_1_3.py``) translates between them.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field, field_validator, model_validator

from dppvalidator.models.base import UNTPBaseModel


class EffectivePeriod(UNTPBaseModel):
    """The validity window during which a CIRPASS DPP applies.

    Wire shape:
        ``{"start": "2026-01-01T00:00:00Z", "end": "2031-12-31T23:59:59Z"}``

    Both endpoints are ISO 8601 datetimes with UTC offset. ``start``
    is required; ``end`` is optional (a DPP with no end date is
    effective indefinitely until superseded). When both are present,
    ``start <= end`` is enforced via a :func:`@model_validator`.

    Maps to UNTP 0.7's ``validFrom`` / ``validUntil`` envelope fields
    via the Phase 5 compat shim.
    """

    _jsonld_type: ClassVar[list[str]] = ["EffectivePeriod"]

    start: datetime = Field(
        ...,
        description="UTC datetime from which the DPP is effective.",
    )
    end: datetime | None = Field(
        default=None,
        description=(
            "UTC datetime after which the DPP is no longer effective. "
            "Absent ⇒ effective indefinitely."
        ),
    )

    @model_validator(mode="after")
    def _start_before_end(self) -> EffectivePeriod:
        if self.end is not None and self.start > self.end:
            msg = (
                f"EffectivePeriod.start={self.start.isoformat()} is later "
                f"than .end={self.end.isoformat()}; the period is empty. "
                f"If the DPP is no longer effective, drop ``end`` and "
                f"supersede with a new DPP instead."
            )
            raise ValueError(msg)
        return self


class IssuedAt(UNTPBaseModel):
    """Timestamp at which a CIRPASS DPP was issued.

    Wire shape: ``{"timestamp": "2026-01-15T09:30:00Z"}``.

    Maps to UNTP 0.7's ``issuanceDate`` envelope field via the Phase 5
    compat shim. Carries an explicit type-wrapper rather than a bare
    datetime so that downstream LD payloads can attach
    ``IssuedAt``-scoped metadata (e.g. issuing-software, signature) on
    the same node.
    """

    _jsonld_type: ClassVar[list[str]] = ["IssuedAt"]

    timestamp: datetime = Field(
        ...,
        description="UTC datetime of issuance.",
    )

    @field_validator("timestamp")
    @classmethod
    def _require_tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            msg = (
                "IssuedAt.timestamp must be timezone-aware (typically UTC). "
                "Naïve datetimes risk ambiguous interpretation across "
                "issuer / consumer locales."
            )
            raise ValueError(msg)
        return value
