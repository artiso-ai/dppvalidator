"""CIRPASS DPP reference structure v1.3.0 — Pydantic models.

Phase 3 of [docs/plans/CIRPASS_2_MIGRATION.md] introduced this module.
The package is the source of truth for the message-level shape; the
JSON Schema bundled at
``src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json`` is
*derived* from these models via
``tools/codegen/cirpass/derive_schema.py`` (Phase 3 task 3.1) and
SHA-pinned in ``schemas/data/MANIFEST.json``.

Importing the package eagerly imports every submodule. ``import
dppvalidator`` does *not* eagerly import this package — see
``models/__init__.py`` for the lazy-import wiring.

Public surface:

- :class:`ReferencePassport` (root)
- :class:`Product`, :class:`Identifier`, :class:`ClassificationCode`
- :class:`Actor`, :class:`Facility`, :class:`ActorRole`,
  :class:`ActorRoleAssignment`
- :class:`Material`, :class:`Composition`
- :class:`SubstanceOfConcern`, :class:`Concentration`,
  :class:`HazardClassification`
- :class:`LifeCycleAssessment`, :class:`ImpactResult`,
  :class:`ImpactCategoryReference`
- :class:`ConnectorRelation`, :class:`RelationType`
- :class:`LocalisedText` (i18n)
- :class:`EffectivePeriod`, :class:`IssuedAt` (temporal)
"""

from __future__ import annotations

from dppvalidator.models.cirpass.v1_3.actor import (
    Actor,
    ActorRole,
    ActorRoleAssignment,
    Facility,
)
from dppvalidator.models.cirpass.v1_3.connector import (
    ConnectorRelation,
    RelationType,
)
from dppvalidator.models.cirpass.v1_3.i18n import LocalisedText, is_valid_bcp47
from dppvalidator.models.cirpass.v1_3.lca import (
    ImpactCategoryReference,
    ImpactResult,
    LifeCycleAssessment,
)
from dppvalidator.models.cirpass.v1_3.material import Composition, Material
from dppvalidator.models.cirpass.v1_3.passport import ReferencePassport
from dppvalidator.models.cirpass.v1_3.product import (
    ClassificationCode,
    Identifier,
    Product,
    looks_like_gtin,
)
from dppvalidator.models.cirpass.v1_3.substances import (
    Concentration,
    HazardClassification,
    SubstanceOfConcern,
)
from dppvalidator.models.cirpass.v1_3.temporal import EffectivePeriod, IssuedAt

__all__ = [
    "Actor",
    "ActorRole",
    "ActorRoleAssignment",
    "ClassificationCode",
    "Composition",
    "Concentration",
    "ConnectorRelation",
    "EffectivePeriod",
    "Facility",
    "HazardClassification",
    "Identifier",
    "ImpactCategoryReference",
    "ImpactResult",
    "IssuedAt",
    "LifeCycleAssessment",
    "LocalisedText",
    "Material",
    "Product",
    "ReferencePassport",
    "RelationType",
    "SubstanceOfConcern",
    "is_valid_bcp47",
    "looks_like_gtin",
]
