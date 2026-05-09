"""Mapping warning codes + dataclass for UNTP ↔ CIRPASS shims.

Phase 5 task 5.1 of [docs/plans/CIRPASS_2_MIGRATION.md]. The ``MAP``
prefix distinguishes these from intra-family upgrade codes
(``UPG``) and validator codes (``CR/SUB/LCS/ACT/REL/SEM/VOC/CQ``).

Five codes are reserved (per the plan §Phase 5 table):

- ``MAP001`` — Lossy: target shape drops information that the source
  carried.
- ``MAP002`` — Synthesised: a required target field had no donor on
  the source side; the shim invented a value (typically a default
  identifier scheme, role enum, or language tag).
- ``MAP003`` — Unmapped: no rule applied to the field; the source
  value passed through unchanged. Surfaced so consumers can decide
  whether to keep extension-style passthrough.
- ``MAP004`` — Required-field-missing: the source cannot supply a
  field that the target requires. The output will fail target-side
  validation until the caller fills it in.
- ``MAP005`` — Temporal collapse: source temporal semantics
  collapsed into a less-expressive target shape (e.g. UNTP's
  ``validFrom`` + ``validUntil`` collapsed into a single
  ``EffectivePeriod``).

The :class:`MappingWarning` dataclass mirrors :class:`UpgradeWarning`
from the UNTP 0.6 → 0.7 shim — same field layout, same severity
ladder, same semantic. The two are kept distinct types so call sites
can pattern-match without conflating intra-family vs cross-family
transformation events.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# =============================================================================
# Warning codes
# =============================================================================

MAP_CODE_LOSSY = "MAP001"
MAP_CODE_SYNTHESISED = "MAP002"
MAP_CODE_UNMAPPED = "MAP003"
MAP_CODE_REQUIRED_FIELD_MISSING = "MAP004"
MAP_CODE_TEMPORAL_COLLAPSE = "MAP005"


# Tuple of all MAP codes in canonical order. Tests pin against this
# (every code must have a reproducible fixture) per the plan exit
# criteria. Keep ordered ascending so ``sorted(MAP_CODES) == MAP_CODES``.
MAP_CODES: tuple[str, ...] = (
    MAP_CODE_LOSSY,
    MAP_CODE_SYNTHESISED,
    MAP_CODE_UNMAPPED,
    MAP_CODE_REQUIRED_FIELD_MISSING,
    MAP_CODE_TEMPORAL_COLLAPSE,
)


# =============================================================================
# Severity
# =============================================================================


class MappingSeverity(str, Enum):
    """Severity ladder for :class:`MappingWarning` (mirrors UpgradeSeverity).

    - ``info`` — transformation is benign and reversible (e.g. a
      bare-string country code wrapped as a Country object).
    - ``warning`` — transformation may need manual review (lossy
      drop, synthesised value, role unmapped). Most ``MAP00X`` codes
      land here.
    - ``error`` — the result will not validate against the target
      shape until the caller fixes the input. Reserved for
      ``MAP004`` (required-field-missing).
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# Default severity per code. Call sites can override on a per-instance
# basis when context warrants (e.g. an unmapped role on a required
# field is an error, an unmapped role on an optional field is a
# warning).
DEFAULT_SEVERITY_BY_CODE: dict[str, MappingSeverity] = {
    MAP_CODE_LOSSY: MappingSeverity.WARNING,
    MAP_CODE_SYNTHESISED: MappingSeverity.WARNING,
    MAP_CODE_UNMAPPED: MappingSeverity.INFO,
    MAP_CODE_REQUIRED_FIELD_MISSING: MappingSeverity.ERROR,
    MAP_CODE_TEMPORAL_COLLAPSE: MappingSeverity.WARNING,
}


# =============================================================================
# Dataclass
# =============================================================================


@dataclass(frozen=True, slots=True)
class MappingWarning:
    """A single transformation event surfaced by a UNTP ↔ CIRPASS shim.

    Attributes mirror :class:`dppvalidator.compat.UpgradeWarning` so
    consumers can write a single dispatch over both warning kinds.

    Attributes:
        code: One of the ``MAP00X`` codes (see module-level constants).
            Stable across releases; consumers may pattern-match on it.
        path: JSONPath-like locator (e.g. ``$.credentialSubject.name``
            for the source side, or ``$.product.productName`` for the
            target). The shim populates the locator on the side the
            transformation *originated* — the side the user is
            usually trying to debug.
        message: Human-readable explanation. Should be actionable
            when read in isolation (include both source and target
            field names).
        severity: One of :class:`MappingSeverity`.
        details: Optional free-form context dictionary. Used by tests
            for stable assertions when the message text isn't
            self-describing (e.g. unmapped roles surface the original
            role string in ``details["original_role"]``).
    """

    code: str
    path: str
    message: str
    severity: MappingSeverity = MappingSeverity.WARNING
    details: tuple[tuple[str, str], ...] = ()

    @classmethod
    def lossy(cls, path: str, message: str, **details: str) -> MappingWarning:
        """Convenience factory for ``MAP001`` (lossy)."""
        return cls(
            code=MAP_CODE_LOSSY,
            path=path,
            message=message,
            severity=DEFAULT_SEVERITY_BY_CODE[MAP_CODE_LOSSY],
            details=tuple(sorted(details.items())),
        )

    @classmethod
    def synthesised(cls, path: str, message: str, **details: str) -> MappingWarning:
        """Convenience factory for ``MAP002`` (synthesised)."""
        return cls(
            code=MAP_CODE_SYNTHESISED,
            path=path,
            message=message,
            severity=DEFAULT_SEVERITY_BY_CODE[MAP_CODE_SYNTHESISED],
            details=tuple(sorted(details.items())),
        )

    @classmethod
    def unmapped(cls, path: str, message: str, **details: str) -> MappingWarning:
        """Convenience factory for ``MAP003`` (unmapped)."""
        return cls(
            code=MAP_CODE_UNMAPPED,
            path=path,
            message=message,
            severity=DEFAULT_SEVERITY_BY_CODE[MAP_CODE_UNMAPPED],
            details=tuple(sorted(details.items())),
        )

    @classmethod
    def required_missing(cls, path: str, message: str, **details: str) -> MappingWarning:
        """Convenience factory for ``MAP004`` (required-field-missing)."""
        return cls(
            code=MAP_CODE_REQUIRED_FIELD_MISSING,
            path=path,
            message=message,
            severity=DEFAULT_SEVERITY_BY_CODE[MAP_CODE_REQUIRED_FIELD_MISSING],
            details=tuple(sorted(details.items())),
        )

    @classmethod
    def temporal_collapse(cls, path: str, message: str, **details: str) -> MappingWarning:
        """Convenience factory for ``MAP005`` (temporal collapse)."""
        return cls(
            code=MAP_CODE_TEMPORAL_COLLAPSE,
            path=path,
            message=message,
            severity=DEFAULT_SEVERITY_BY_CODE[MAP_CODE_TEMPORAL_COLLAPSE],
            details=tuple(sorted(details.items())),
        )


__all__ = [
    "DEFAULT_SEVERITY_BY_CODE",
    "MAP_CODES",
    "MAP_CODE_LOSSY",
    "MAP_CODE_REQUIRED_FIELD_MISSING",
    "MAP_CODE_SYNTHESISED",
    "MAP_CODE_TEMPORAL_COLLAPSE",
    "MAP_CODE_UNMAPPED",
    "MappingSeverity",
    "MappingWarning",
]
