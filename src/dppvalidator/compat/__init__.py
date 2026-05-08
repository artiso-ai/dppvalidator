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

from dppvalidator.compat.upgrade_0_6_to_0_7 import (
    UPG_CODE_LOSSY,
    UPG_CODE_REQUIRED_FIELD_MISSING,
    UPG_CODE_SYNTHESISED,
    UPG_CODE_UNMAPPED_COUNTRY,
    UpgradeSeverity,
    UpgradeWarning,
    upgrade,
)


def active_version() -> str:
    """Return the UNTP DPP version this build of dppvalidator targets.

    This is the value of :data:`DEFAULT_SCHEMA_VERSION` from the schema
    registry, surfaced as a function so callers don't have to import the
    registry directly. Use this whenever you need a "current default"
    version literal in feature code — the no-version-literals guard
    test (``tests/unit/test_no_version_literals.py``) refuses to let you
    hardcode the string.
    """
    from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

    return DEFAULT_SCHEMA_VERSION


def is_version(version: str) -> bool:
    """Return ``True`` if ``version`` matches the active default version."""
    return version == active_version()


__all__ = [
    "UPG_CODE_LOSSY",
    "UPG_CODE_REQUIRED_FIELD_MISSING",
    "UPG_CODE_SYNTHESISED",
    "UPG_CODE_UNMAPPED_COUNTRY",
    "UpgradeSeverity",
    "UpgradeWarning",
    "active_version",
    "is_version",
    "upgrade",
]
