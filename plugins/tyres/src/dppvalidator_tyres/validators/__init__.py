"""Tyres pilot validators — TYR-coded rules.

Phase 7 task 7.6 of [docs/plans/CIRPASS_2_MIGRATION.md] in the
``dppvalidator`` core. Each rule implements the ``SemanticRule``
protocol (``rule_id``, ``description``, ``severity``,
``check(passport)``) and is auto-registered via the entry-points
declared in ``plugins/tyres/pyproject.toml``.

The plugin's wire-shape contract: the tyres lifecycle data lives
under ``credentialSubject.extensions.tyreLifecycleHistory`` (a
:class:`TyreLifecycleHistory` JSON serialisation). Rules walk this
extension; passports without it are silently skipped (not every
DPP is a tyre DPP).

Rule codes (TYR001…TYR008):

- ``TYR001`` (error): DOT marking present and well-formed.
- ``TYR002`` (error): Birth declaration carries the manufacturer
  actor identifier.
- ``TYR003`` (warning): Load index in the standard ETRTO range
  (60-130 covers passenger / light-truck).
- ``TYR004`` (warning): Speed rating is a recognised letter code.
- ``TYR005`` (warning): Section width / aspect ratio / rim
  diameter look sane (light-truck range).
- ``TYR006`` (error): Retread declarations name the upstream
  Birth UUID via ``previousBirthUuid``.
- ``TYR007`` (warning): Collection declarations identify the
  collecting actor.
- ``TYR008`` (warning): Recycling declarations name the recycling
  method (mechanical / pyrolysis / devulcanisation / energy_recovery).
"""

from __future__ import annotations

from dppvalidator_tyres.validators.rules import (
    BirthChainCompletenessRule,
    CollectionActorRule,
    DOTMarkingRule,
    LoadIndexRule,
    RecyclingMethodRule,
    RetreadProvenanceRule,
    SectionWidthRule,
    SpeedRatingRule,
)

# Public dispatch — useful for callers that want to construct a
# SemanticValidator with a hand-curated rule list.
TYR_RULES = (
    DOTMarkingRule(),
    BirthChainCompletenessRule(),
    LoadIndexRule(),
    SpeedRatingRule(),
    SectionWidthRule(),
    RetreadProvenanceRule(),
    CollectionActorRule(),
    RecyclingMethodRule(),
)

__all__ = [
    "BirthChainCompletenessRule",
    "CollectionActorRule",
    "DOTMarkingRule",
    "LoadIndexRule",
    "RecyclingMethodRule",
    "RetreadProvenanceRule",
    "SectionWidthRule",
    "SpeedRatingRule",
    "TYR_RULES",
]
