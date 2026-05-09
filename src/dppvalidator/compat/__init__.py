"""Cross-version compatibility utilities for dppvalidator.

This package houses two distinct concerns:

1. **Active-version helpers** — :func:`active_version` and
   :func:`is_version` give callers a single import-stable way to check
   "what version of UNTP DPP is the engine defaulting to right now?"
   without having to reach into :mod:`dppvalidator.schemas.registry`.

2. **Compatibility shims** — modules named ``upgrade_<from>_to_<to>``
   that take a payload in the older shape and rewrite it in place to
   match the newer one. They emit structured :class:`UpgradeWarning`
   entries when a transformation is lossy or has to synthesise a value;
   the caller decides whether to accept the result or surface the
   warnings to the end user.

The :func:`active_version` and :func:`is_version` helpers are listed in
``.claude/rules/untp-versioning.md`` (cardinal rule 1) as the
canonical alternative to literal version strings outside the
:mod:`dppvalidator.schemas.registry` and
:mod:`dppvalidator.exporters.contexts` registries.

See ``docs/plans/UNTP_0.7.0_MIGRATION.md`` §Phase 4 for the design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dppvalidator.compat._mapping_codes import (
    MAP_CODE_LOSSY,
    MAP_CODE_REQUIRED_FIELD_MISSING,
    MAP_CODE_SYNTHESISED,
    MAP_CODE_TEMPORAL_COLLAPSE,
    MAP_CODE_UNMAPPED,
    MAP_CODES,
    MappingSeverity,
    MappingWarning,
)
from dppvalidator.compat.cirpass_1_3_to_untp_0_7 import to_untp_0_7
from dppvalidator.compat.untp_0_7_to_cirpass_1_3 import to_cirpass_1_3
from dppvalidator.compat.upgrade_0_6_to_0_7 import (
    UPG_CODE_LOSSY,
    UPG_CODE_REQUIRED_FIELD_MISSING,
    UPG_CODE_SYNTHESISED,
    UPG_CODE_UNMAPPED_COUNTRY,
    UpgradeSeverity,
    UpgradeWarning,
    upgrade,
)

if TYPE_CHECKING:
    from dppvalidator.schemas.registry import SchemaFamily


def active_version(family: SchemaFamily | None = None) -> str:
    """Return the active default version for a schema family.

    This is the value of :data:`DEFAULT_VERSIONS[family]` from the
    schema registry, surfaced as a function so callers don't have to
    import the registry directly. Use this whenever you need a
    "current default" version literal in feature code — the
    no-version-literals guard test
    (``tests/unit/test_no_version_literals.py``) refuses to let you
    hardcode the string.

    Phase 2 of the CIRPASS-2 migration extended this with the
    ``family`` keyword. Pre-Phase-2 callers (``active_version()`` with
    no argument) keep getting the UNTP default, preserving the
    historical behaviour.

    Args:
        family: Schema family. ``None`` (default) is treated as
            :data:`SchemaFamily.UNTP` — same as the pre-Phase-2 API.

    Returns:
        Default version string for the requested family.
    """
    from dppvalidator.schemas.registry import DEFAULT_VERSIONS
    from dppvalidator.schemas.registry import SchemaFamily as _SF

    return DEFAULT_VERSIONS[family if family is not None else _SF.UNTP]


def is_version(version: str, family: SchemaFamily | None = None) -> bool:
    """Return ``True`` if ``version`` matches the active default version.

    Phase 2 added the ``family`` keyword (defaults to UNTP for
    back-compat).
    """
    return version == active_version(family)


__all__ = [
    # UNTP 0.6 → 0.7 upgrade
    "UPG_CODE_LOSSY",
    "UPG_CODE_REQUIRED_FIELD_MISSING",
    "UPG_CODE_SYNTHESISED",
    "UPG_CODE_UNMAPPED_COUNTRY",
    "UpgradeSeverity",
    "UpgradeWarning",
    "upgrade",
    # UNTP ↔ CIRPASS mapping (Phase 5)
    "MAP_CODES",
    "MAP_CODE_LOSSY",
    "MAP_CODE_REQUIRED_FIELD_MISSING",
    "MAP_CODE_SYNTHESISED",
    "MAP_CODE_TEMPORAL_COLLAPSE",
    "MAP_CODE_UNMAPPED",
    "MappingSeverity",
    "MappingWarning",
    "to_cirpass_1_3",
    "to_untp_0_7",
    # Active-version helpers
    "active_version",
    "is_version",
]
