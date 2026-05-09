"""Declarative step table for UNTP 0.7.0 ↔ CIRPASS 1.3.0 transformations.

Phase 5 task 5.2 of [docs/plans/CIRPASS_2_MIGRATION.md]. The two
shims (forward / reverse) read from this table so the *what's-mapped-
to-what* contract lives in one place. Each step is a self-contained
record:

- ``forward_step`` / ``reverse_step`` are descriptive labels —
  they show up in MAP-warning messages so consumers can grep for
  the step that emitted them.
- ``untp_path`` and ``cirpass_path`` are JSONPath-style locators
  for the source and target fields. Used in warning ``path``
  attributes.
- ``lossless`` is True when the step has a clean reversible
  identity over the documented lossless subset; False when the
  step is one-way (e.g. UNTP scorecards → CIRPASS LCA results
  loses scorecard scoring). Round-trip property tests filter
  on ``lossless=True``.
- ``codes`` records the ``MAP00X`` codes the step *may* emit. Tests
  pin against this so accidental code drift fails CI.

The table is the source of truth for the lossless-subset reference
doc at ``docs/concepts/untp-cirpass-mapping.md``; the doc is
*derived* from this list (Phase 5 task 5.9).
"""

from __future__ import annotations

from dataclasses import dataclass

from dppvalidator.compat._mapping_codes import (
    MAP_CODE_LOSSY,
    MAP_CODE_REQUIRED_FIELD_MISSING,
    MAP_CODE_SYNTHESISED,
    MAP_CODE_TEMPORAL_COLLAPSE,
    MAP_CODE_UNMAPPED,
)


@dataclass(frozen=True, slots=True)
class MappingStep:
    """One row in the declarative UNTP ↔ CIRPASS map."""

    step_id: str
    """Stable identifier (``M01``, ``M02``, …). Stable across releases
    so MAP-warnings can reference the step that emitted them."""

    description: str
    """Short human-readable summary of the transformation."""

    untp_path: str
    """JSONPath of the source/target field on the UNTP side."""

    cirpass_path: str
    """JSONPath of the source/target field on the CIRPASS side."""

    lossless: bool
    """Whether the round-trip preserves the field bit-for-bit (over
    the documented lossless subset)."""

    codes: tuple[str, ...]
    """MAP-codes that this step may emit."""


# =============================================================================
# Step table (Phase 5)
# =============================================================================
#
# Order matters for MAP-warning ordering inside both shims: each
# shim iterates the table top-to-bottom so warnings appear in
# transformation order.

MAPPING_STEPS: tuple[MappingStep, ...] = (
    # -------------------------------------------------------------------
    # Identifiers — DPP / Product / Party / Facility (G18)
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M01",
        description="DPP credential identifier ↔ DPP identifier object",
        untp_path="$.id",
        cirpass_path="$.dppIdentifier.value",
        lossless=True,
        codes=(MAP_CODE_SYNTHESISED, MAP_CODE_REQUIRED_FIELD_MISSING),
    ),
    MappingStep(
        step_id="M02",
        description="Product credential subject ↔ root product",
        untp_path="$.credentialSubject",
        cirpass_path="$.product",
        lossless=True,
        codes=(MAP_CODE_REQUIRED_FIELD_MISSING,),
    ),
    MappingStep(
        step_id="M03",
        description=(
            "Product identifier scheme: UNTP IdentifierScheme(id, name) "
            "↔ CIRPASS Identifier(scheme, schemeName)"
        ),
        untp_path="$.credentialSubject.idScheme",
        cirpass_path="$.product.productIdentifier.scheme",
        lossless=True,
        codes=(MAP_CODE_UNMAPPED,),
    ),
    # -------------------------------------------------------------------
    # Names / labels (G16 — i18n)
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M04",
        description=(
            "DPP envelope name (UNTP scalar string) ↔ a synthesised "
            "single-language LocalisedText is *not* part of the CIRPASS "
            "tree-view; UNTP `name` is informational only and is "
            "passed through to the reverse shim if present"
        ),
        untp_path="$.name",
        cirpass_path="(not mapped — see notes)",
        lossless=False,
        codes=(MAP_CODE_LOSSY,),
    ),
    MappingStep(
        step_id="M05",
        description=(
            "Product name: UNTP scalar string ↔ CIRPASS LocalisedText[]; "
            "forward synthesises a single-entry list with the caller-"
            "supplied default language. Reverse drops all but the first"
            " language entry — additional languages emit MAP001."
        ),
        untp_path="$.credentialSubject.name",
        cirpass_path="$.product.productName",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_SYNTHESISED),
    ),
    MappingStep(
        step_id="M06",
        description=(
            "Product description: UNTP scalar string ↔ CIRPASS "
            "LocalisedText[]; same lossy rule as M05 in reverse."
        ),
        untp_path="$.credentialSubject.description",
        cirpass_path="$.product.description",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_SYNTHESISED),
    ),
    # -------------------------------------------------------------------
    # Temporal (G17)
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M07",
        description=(
            "Issuance: UNTP `validFrom` (envelope) ↔ CIRPASS `issuedAt.timestamp`. "
            "Forward copies validFrom into issuedAt (the DPP issued at the "
            "moment it became valid). Reverse re-emits the same datetime."
        ),
        untp_path="$.validFrom",
        cirpass_path="$.issuedAt.timestamp",
        lossless=True,
        codes=(MAP_CODE_REQUIRED_FIELD_MISSING,),
    ),
    MappingStep(
        step_id="M08",
        description=(
            "Effective period: UNTP (validFrom, validUntil) ↔ "
            "CIRPASS EffectivePeriod(start, end). Lossless when both "
            "endpoints are present; MAP005 emitted on the forward side "
            "when validUntil is absent and the caller still wants an "
            "EffectivePeriod attached."
        ),
        untp_path="$.validFrom + $.validUntil",
        cirpass_path="$.effectivePeriod",
        lossless=True,
        codes=(MAP_CODE_TEMPORAL_COLLAPSE,),
    ),
    # -------------------------------------------------------------------
    # Commodity classification
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M09",
        description=(
            "Product category list: UNTP Classification[] ↔ CIRPASS "
            "ClassificationCode[]. Both carry (code, scheme) pairs; "
            "name-i18n flattens via M05's lossy rule."
        ),
        untp_path="$.credentialSubject.productCategory",
        cirpass_path="$.product.commodityCode",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_UNMAPPED),
    ),
    # -------------------------------------------------------------------
    # Materials
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M10",
        description=(
            "Material composition: UNTP Material[] ↔ CIRPASS "
            "Composition.materials[]. mass_fraction / origin_country / "
            "is_recycled all carry one-to-one. Material names flatten "
            "via M05's lossy rule (UNTP carries a scalar name; CIRPASS "
            "carries a localised list)."
        ),
        untp_path="$.credentialSubject.materialProvenance",
        cirpass_path="$.composition.materials",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_SYNTHESISED),
    ),
    # -------------------------------------------------------------------
    # Actors / parties
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M11",
        description=(
            "Related parties: UNTP PartyRole[] ↔ CIRPASS "
            "ActorRole[]. Role enums map through "
            "EUDPPRoleClass; unmapped UNTP roles synthesise "
            "EUDPPRoleClass.ECONOMIC_OPERATOR with a MAP002 warning."
        ),
        untp_path="$.credentialSubject.relatedParty",
        cirpass_path="$.relatedActors",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_SYNTHESISED, MAP_CODE_UNMAPPED),
    ),
    # -------------------------------------------------------------------
    # Issuer
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M12",
        description=(
            "Issuer (UNTP envelope) ↔ CIRPASS related-actor with "
            "ManufacturerRole. Forward synthesises a related-actor "
            "from the issuer when no manufacturer party is present "
            "(emits MAP002). Reverse extracts the manufacturer "
            "actor and re-emits it as the issuer."
        ),
        untp_path="$.issuer",
        cirpass_path="$.relatedActors[?(@.role=='eudpp:ManufacturerRole')]",
        lossless=False,
        codes=(MAP_CODE_SYNTHESISED, MAP_CODE_LOSSY),
    ),
    # -------------------------------------------------------------------
    # Performance / scorecards / LCA
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M13",
        description=(
            "Performance claims: UNTP performanceClaim[] (scoped by "
            "conformityTopic) ↔ CIRPASS LifeCycleAssessment results "
            "for ESPR Annex impact categories. The full v0.7 claim "
            "shape (assessor, evidence, claimedBenchmark) does not "
            "round-trip — forward emits MAP001 for dropped fields."
        ),
        untp_path="$.credentialSubject.performanceClaim",
        cirpass_path="$.lca",
        lossless=False,
        codes=(MAP_CODE_LOSSY, MAP_CODE_UNMAPPED),
    ),
    # -------------------------------------------------------------------
    # Substances of concern (UNTP has no first-class equivalent)
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M14",
        description=(
            "CIRPASS substancesOfConcern has no UNTP equivalent in "
            "the v0.7 base schema (the textile pilot extends with "
            "substances; the base schema doesn't). Forward → CIRPASS "
            "leaves the field empty; reverse drops the array with "
            "MAP001."
        ),
        untp_path="(no source field)",
        cirpass_path="$.substancesOfConcern",
        lossless=False,
        codes=(MAP_CODE_LOSSY,),
    ),
    # -------------------------------------------------------------------
    # Cross-module connector relations (CIRPASS-only)
    # -------------------------------------------------------------------
    MappingStep(
        step_id="M15",
        description=(
            "CIRPASS connectorRelations are a CIRPASS-only construct "
            "(no UNTP equivalent). Reverse drops with MAP001; forward "
            "leaves empty."
        ),
        untp_path="(no source field)",
        cirpass_path="$.connectorRelations",
        lossless=False,
        codes=(MAP_CODE_LOSSY,),
    ),
)


# =============================================================================
# Public helpers
# =============================================================================


def step(step_id: str) -> MappingStep:
    """Return the :class:`MappingStep` row with the given ID.

    Raises ``KeyError`` if no row matches — the shims pattern-match
    on stable IDs, so a missing one is a programming error.
    """
    for row in MAPPING_STEPS:
        if row.step_id == step_id:
            return row
    msg = f"Unknown mapping step ID: {step_id!r}"
    raise KeyError(msg)


def lossless_step_ids() -> tuple[str, ...]:
    """Return IDs of every step on the documented lossless subset."""
    return tuple(s.step_id for s in MAPPING_STEPS if s.lossless)


def codes_for_step(step_id: str) -> tuple[str, ...]:
    """Return the MAP codes that ``step_id`` may emit."""
    return step(step_id).codes


def all_codes_in_use() -> set[str]:
    """Set of every MAP code referenced by at least one step.

    Used by ``test_mapping_codes_have_step_coverage`` to assert
    every code in :data:`MAP_CODES` is exercised by at least one
    declared transformation.
    """
    codes: set[str] = set()
    for row in MAPPING_STEPS:
        codes.update(row.codes)
    return codes


__all__ = [
    "MAPPING_STEPS",
    "MappingStep",
    "all_codes_in_use",
    "codes_for_step",
    "lossless_step_ids",
    "step",
]
