"""Tyres pilot models — GDSO declarations.

Phase 7 task 7.5 of [docs/plans/CIRPASS_2_MIGRATION.md]. Pydantic v2
models for the four GDSO tyre-lifecycle declaration types plus the
:class:`TyreLifecycleHistory` aggregate.

The four declarations correspond to the GDSO public specs:

- :class:`Birth` (v0.9) — manufacturer's at-mould declaration.
- :class:`Collection` (v0.1) — collector's at-end-of-first-life
  declaration.
- :class:`Retread` (v0.1) — retreader's renewal declaration.
- :class:`Recycling` (v0.1) — recycler's at-end-of-life declaration.

Plus a wrapper:

- :class:`TyreLifecycleHistory` — a single Birth + chronologically-
  ordered list of subsequent events.

Status: Pre-1.0 / Experimental — the upstream GDSO Birth v0.9 and
Recycling v0.1 declarations are still moving; field names may
shift before 1.0.
"""

from __future__ import annotations

from dppvalidator_tyres.models.actor import TyreActor
from dppvalidator_tyres.models.birth import Birth, DOTMarking, TyreSize
from dppvalidator_tyres.models.collection import Collection
from dppvalidator_tyres.models.history import TyreLifecycleEvent, TyreLifecycleHistory
from dppvalidator_tyres.models.recycling import Recycling, RecyclingMethod
from dppvalidator_tyres.models.retread import Retread

__all__ = [
    "Birth",
    "Collection",
    "DOTMarking",
    "Recycling",
    "RecyclingMethod",
    "Retread",
    "TyreActor",
    "TyreLifecycleEvent",
    "TyreLifecycleHistory",
    "TyreSize",
]
