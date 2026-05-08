"""Compatibility shim: rewrite UNTP DPP 0.6.x payloads into 0.7.0 shape.

This module is the operational core of Phase 4 of
``docs/plans/UNTP_0.7.0_MIGRATION.md``. It takes a JSON ``dict`` whose
shape matches the UNTP DPP 0.6.x wire format and returns a new ``dict``
in 0.7.0 shape, plus a list of :class:`UpgradeWarning` entries
describing each transformation that was lossy, synthesised, or skipped.

Design principles:

- **Pure transformation, no validation.** The shim never raises on
  malformed input; it makes a best-effort upgrade and lets the caller
  validate the result against the v0.7 model. Anything that *can't* be
  upgraded faithfully is surfaced as an :class:`UpgradeWarning`.
- **Structural over semantic.** The shim rewires field names and shapes
  but never invents content. ``materialType`` cannot be guessed from
  ``name``; ``massFraction`` cannot be inferred. Missing required-in-0.7
  fields therefore produce ``UPG004`` warnings, not synthesised values.
- **Side-effect-free.** The input ``dict`` is deep-copied; callers can
  upgrade-then-keep-original without surprises.
- **Deterministic.** Two runs against the same input produce
  byte-identical output and the same warning set in the same order.

The 17 transformation steps and 4 warning codes are documented inline.
The transformation order matters: e.g. step 1 (context URL) must run
before step 3 (envelope flattening) so that detection helpers continue
to work on the partially-upgraded payload.
"""

from __future__ import annotations

import base64
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any

from dppvalidator.logging import get_logger
from dppvalidator.vocabularies.loader import get_bundled_country_codes

logger = get_logger(__name__)


# =============================================================================
# Warning codes and types
# =============================================================================


# Codes from docs/plans/UNTP_0.7.0_MIGRATION.md §Phase 4. The ``UPG`` prefix
# distinguishes them from validator codes (``CQ``, ``MDL``, ``JLD``, ``VER``).
UPG_CODE_LOSSY = "UPG001"
UPG_CODE_SYNTHESISED = "UPG002"
UPG_CODE_UNMAPPED_COUNTRY = "UPG003"
UPG_CODE_REQUIRED_FIELD_MISSING = "UPG004"


class UpgradeSeverity(str, Enum):
    """Severity levels for :class:`UpgradeWarning`.

    ``info`` is for changes the caller can safely ignore (e.g. type
    arrays stripped from embedded objects). ``warning`` is for
    transformations that may need manual review (synthesised values,
    unknown country codes). ``error`` is for required-in-0.7 fields
    that the shim cannot synthesise — the result will not validate
    cleanly until the caller fills these in.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class UpgradeWarning:
    """A single transformation event surfaced by the upgrade shim.

    Attributes:
        code: One of the ``UPG`` codes above. Stable across releases —
            consumers may pattern-match on the code to decide whether
            to accept the upgrade.
        path: JSONPath-like locator (e.g.
            ``credentialSubject.materialProvenance[2].originCountry``)
            pointing at where the transformation was applied.
        message: Human-readable explanation. Include enough context to
            be actionable when read in isolation.
        severity: One of :class:`UpgradeSeverity`. Drives whether
            ``dppvalidator migrate`` refuses to write the upgraded JSON
            without ``--accept-warnings``.
    """

    code: str
    path: str
    message: str
    severity: UpgradeSeverity = UpgradeSeverity.WARNING


# =============================================================================
# Constants
# =============================================================================


# v0.6.x → v0.7.0 context URL substitution. The v0.6.x family stored its
# UNTP context under ``test.uncefact.org/vocabulary/untp/dpp/<version>/``;
# v0.7.0 moved to ``vocabulary.uncefact.org/untp/0.7.0/context/``. We treat
# the patch level on the v0.6 side as flexible because the same shape
# applies to 0.6.0 and 0.6.1.
_V06_CONTEXT_RE = re.compile(
    r"^https://test\.uncefact\.org/vocabulary/untp/dpp/0\.6(?:\.\d+)?/?$",
)
_V07_CONTEXT_URL = "https://vocabulary.uncefact.org/untp/0.7.0/context/"

# v0.7.0 ``Image`` requires ``name``, ``imageData``, ``mediaType``. The shim
# uses these defaults when upgrading a v0.6 ``Material.symbol`` (which was
# a bare base64 string) — image bytes carry the data, the other two
# fields are synthesised and surfaced via UPG002.
_DEFAULT_IMAGE_MEDIA_TYPE = "image/png"
_DEFAULT_IMAGE_NAME = "Material symbol"

# Embedded objects whose v0.6 wire shape carried a ``type: [...]``
# discriminator that v0.7 dropped. Stripping these keeps strict-mode
# validation against the v0.7 schema clean.
_TYPES_TO_STRIP_ON: frozenset[str] = frozenset(
    {
        # Product-level container keys whose embedded objects no longer
        # carry a ``type`` discriminator in v0.7 (Dimension, Characteristics).
        "dimensions",
        "characteristics",
        # Measure-shaped sub-fields under Dimension and Performance.metricValue.
        "weight",
        "length",
        "width",
        "height",
        "volume",
        "mass",
        "measure",
        "thresholdValue",
        "metricValue",
        # Claim-shape descriptor (we keep the top-level Claim type but drop
        # type arrays on lifted scorecard claims to match the v0.7 schema).
        "claim",
    }
)

# Fields where Material.symbol may sit. v0.6 used a single string; v0.7
# expects an Image object. Sentinel placeholders that are clearly not
# real base64 (e.g. "undefined" in our own legacy fixtures) are dropped
# rather than smuggled through as fake image bytes.
_KNOWN_SYMBOL_PLACEHOLDERS: frozenset[str] = frozenset({"undefined", "null", "none", ""})


# =============================================================================
# Public entry point
# =============================================================================


def upgrade(
    data: dict[str, Any],
    *,
    country_lookup: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], list[UpgradeWarning]]:
    """Upgrade a UNTP DPP v0.6.x payload to v0.7.0 shape.

    Args:
        data: The v0.6.x payload as a parsed JSON ``dict``. The input is
            deep-copied; the caller's object is never mutated.
        country_lookup: Optional ISO-3166-1 alpha-2 → country-name map.
            When supplied, scalar country codes (e.g. ``"DE"``) are
            wrapped as ``{countryCode: "DE", countryName: "Germany"}``
            using this mapping. When omitted, only ``countryCode`` is
            populated and a UPG002 warning fires per wrapped scalar.
            The bundled :data:`get_bundled_country_codes` set is always
            used as the validity check (UPG003 fires for unknown codes).

    Returns:
        Tuple of ``(upgraded_dict, warnings)``. The dict is ready to be
        validated against the v0.7.0 model. Warnings are ordered by
        the transformation step that emitted them, then by document
        position.

    The 17 transformation steps execute in the order documented in the
    migration plan. Each step is a private helper; the entry point is
    this thin orchestrator.
    """
    if not isinstance(data, dict):
        raise TypeError(
            f"upgrade() requires a dict, got {type(data).__name__!r}",
        )

    upgraded = deepcopy(data)
    warnings: list[UpgradeWarning] = []
    valid_codes = get_bundled_country_codes()

    # Step 1 — context URL substitution.
    _step1_replace_context(upgraded, warnings)

    # Step 3 — drop ProductPassport envelope (run before steps 2/4-13 so
    # the rest of the pipeline operates on the flattened Product). Steps
    # 4 (materialsProvenance), 5 (dueDiligenceDeclaration), 6
    # (conformityClaim), 7 (scorecards), and granularityLevel migration
    # all read from the original ProductPassport envelope and write to
    # the new credentialSubject (now a Product).
    _step3_flatten_envelope(upgraded, warnings)

    # Step 2 — envelope ``name`` / ``validFrom`` (synthesise if absent).
    # Runs after step 3 so we can synthesise ``name`` from
    # ``credentialSubject.name`` (which by now is the product's name).
    _step2_envelope_required_fields(upgraded, warnings)

    cs = upgraded.get("credentialSubject")
    if not isinstance(cs, dict):
        # No product to upgrade further — return what we have.
        return upgraded, warnings

    # Steps 10–17 act on the credentialSubject (now a Product).
    _step10_wrap_product_category(cs, warnings)
    _step11_party_to_related_party(cs, warnings)
    _step12_further_information_to_related_document(cs, warnings)
    _step13_drop_registered_id(cs, warnings)
    _step9_wrap_country_codes(cs, warnings, country_lookup, valid_codes)
    _step14_material_symbol_to_image(cs, warnings)
    _step17_material_required_fields(cs, warnings)
    _step8_wrap_claim_references(cs, warnings)
    _step16_rename_scheme_id(cs, warnings)
    _step15_strip_embedded_types(cs, warnings)

    return upgraded, warnings


# =============================================================================
# Step 1 — context URL substitution
# =============================================================================


def _step1_replace_context(
    data: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Swap the v0.6 UNTP context URL for the v0.7.0 one.

    The W3C VC v2 context entry is left untouched. Anything that doesn't
    look like a v0.6.x UNTP context URL is also left as-is — third-party
    extensions plug into the context list, and we shouldn't smuggle
    their references away.
    """
    ctx = data.get("@context")
    if not isinstance(ctx, list):
        return
    for i, entry in enumerate(ctx):
        if isinstance(entry, str) and _V06_CONTEXT_RE.match(entry):
            ctx[i] = _V07_CONTEXT_URL


# =============================================================================
# Step 2 — envelope required fields
# =============================================================================


def _step2_envelope_required_fields(data: dict[str, Any], warnings: list[UpgradeWarning]) -> None:
    """Ensure the envelope has the v0.7-required ``name`` and ``validFrom``.

    ``name`` becomes a top-level required field in v0.7 (was implicit
    via the product). ``validFrom`` was already common but the schema
    elevates it to required — defensively add a placeholder if missing
    so the result at least has a parsable shape.
    """
    if not data.get("name"):
        cs = data.get("credentialSubject")
        synthesised: str | None = None
        if isinstance(cs, dict):
            cs_name = cs.get("name")
            if isinstance(cs_name, str) and cs_name:
                synthesised = cs_name
        if synthesised:
            data["name"] = synthesised
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_SYNTHESISED,
                    path="name",
                    message=(
                        "Top-level ``name`` missing in v0.6 payload; "
                        "synthesised from credentialSubject.name."
                    ),
                ),
            )
        else:
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_REQUIRED_FIELD_MISSING,
                    path="name",
                    message=(
                        "Top-level ``name`` is required in v0.7.0 and could "
                        "not be synthesised — provide manually."
                    ),
                    severity=UpgradeSeverity.ERROR,
                ),
            )

    if not data.get("validFrom"):
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_REQUIRED_FIELD_MISSING,
                path="validFrom",
                message=(
                    "Envelope ``validFrom`` is required in v0.7.0 and was "
                    "absent in the source payload."
                ),
                severity=UpgradeSeverity.ERROR,
            ),
        )


# =============================================================================
# Step 3 — drop ProductPassport envelope
# =============================================================================


def _step3_flatten_envelope(data: dict[str, Any], warnings: list[UpgradeWarning]) -> None:
    """Replace ``credentialSubject`` (the ProductPassport) with its product.

    The v0.6 ``ProductPassport`` carried siblings of the product
    (``conformityClaim``, scorecards, ``materialsProvenance``,
    ``dueDiligenceDeclaration``, ``granularityLevel``). v0.7 hangs all
    of those off the Product itself. We move them in this step so later
    steps can operate on a single flat object.

    ``granularityLevel`` becomes ``idGranularity`` here.
    """
    cs = data.get("credentialSubject")
    if not isinstance(cs, dict):
        return

    pp_types = cs.get("type")
    is_product_passport = (
        isinstance(pp_types, list) and "ProductPassport" in pp_types
    ) or "product" in cs

    if not is_product_passport:
        # Already flat — nothing to do.
        return

    product = cs.get("product")
    if not isinstance(product, dict):
        # ProductPassport with no product — wrap an empty product so the
        # rest of the pipeline has a target to write into.
        product = {}

    # Carry siblings from ProductPassport onto the new credentialSubject.
    granularity = cs.get("granularityLevel")
    materials_provenance = cs.get("materialsProvenance")
    conformity_claim = cs.get("conformityClaim")
    emissions_scorecard = cs.get("emissionsScorecard")
    circularity_scorecard = cs.get("circularityScorecard")
    traceability_information = cs.get("traceabilityInformation")
    due_diligence = cs.get("dueDiligenceDeclaration")
    pp_id = cs.get("id")

    new_cs: dict[str, Any] = dict(product)
    new_cs["type"] = ["Product"]
    # Field rename: ``serialNumber`` (v0.6) → ``itemNumber`` (v0.7).
    if "serialNumber" in new_cs and "itemNumber" not in new_cs:
        new_cs["itemNumber"] = new_cs.pop("serialNumber")
    if isinstance(granularity, str):
        new_cs.setdefault("idGranularity", granularity)
    if isinstance(materials_provenance, list):
        new_cs["materialProvenance"] = materials_provenance
    # Preserve the ProductPassport.id if the inner product had none — it
    # was the credential-subject identifier in v0.6.
    if pp_id and not new_cs.get("id"):
        new_cs["id"] = pp_id

    performance_claim: list[dict[str, Any]] = []
    # Step 6 — conformityClaim → performanceClaim (kept whole here; field
    # renames inside each Claim happen in step 8/16/15 below).
    if isinstance(conformity_claim, list):
        performance_claim.extend(_v06_claim_to_v07_claim(c) for c in conformity_claim)

    # Step 7 — scorecards → Claim entries.
    if isinstance(emissions_scorecard, dict):
        performance_claim.append(
            _scorecard_to_claim(
                topic="emissions",
                scorecard=emissions_scorecard,
                topic_name="Emissions",
            ),
        )
    if isinstance(circularity_scorecard, dict):
        performance_claim.append(
            _scorecard_to_claim(
                topic="circularity",
                scorecard=circularity_scorecard,
                topic_name="Circularity",
            ),
        )
    if isinstance(traceability_information, list):
        for entry in traceability_information:
            if isinstance(entry, dict):
                performance_claim.append(
                    _scorecard_to_claim(
                        topic="traceability",
                        scorecard=entry,
                        topic_name="Traceability",
                    ),
                )

    if performance_claim:
        new_cs["performanceClaim"] = performance_claim

    # Step 5 — dueDiligenceDeclaration → relatedDocument[].
    if isinstance(due_diligence, dict):
        related = list(new_cs.get("relatedDocument") or [])
        link = dict(due_diligence)
        link.setdefault("name", "Due diligence declaration")
        related.append(link)
        new_cs["relatedDocument"] = related

    data["credentialSubject"] = new_cs

    if conformity_claim or emissions_scorecard or circularity_scorecard or traceability_information:
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_LOSSY,
                path="credentialSubject.performanceClaim",
                message=(
                    "v0.6 conformityClaim and scorecard arrays were folded into "
                    "v0.7 performanceClaim. Inner field shapes were rewritten "
                    "best-effort; review for fidelity."
                ),
                severity=UpgradeSeverity.WARNING,
            ),
        )


def _v06_claim_to_v07_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Rewire a single v0.6 ``Claim`` into v0.7 shape.

    Field renames (handled here, not in shared helpers, because they're
    Claim-specific):

    - ``assessmentDate`` → ``claimDate``
    - ``assessmentCriteria`` (list[Criterion]) → ``referenceCriteria`` (list[dict])
    - ``declaredValue`` (list[Metric]) → ``claimedPerformance`` (list[Performance])
    - ``conformityTopic`` (str) → ``conformityTopic`` (list[ConformityTopic])
    - ``conformityEvidence`` (SecureLink) → ``evidence`` ([Link])
    - ``referenceStandard`` (Standard) → ``referenceStandard`` (list[dict])
    - ``referenceRegulation`` (Regulation) → ``referenceRegulation`` (list[dict])
    - ``conformance`` (bool) — dropped (no v0.7 equivalent at top level)

    The shape rewrite is best-effort: ``Performance`` requires a
    ``metric`` plus at least one of ``measure``/``score``, so v0.6
    ``Metric`` rows get split (``metricName`` → ``metric.name``,
    ``metricValue`` → ``measure``, ``score`` → ``score.code``).
    """
    out: dict[str, Any] = {"type": ["Claim"]}

    # Pass-through fields.
    for k in ("id", "description"):
        if k in claim:
            out[k] = claim[k]
    # ``name`` is required in v0.7 Claim — fall back to description if absent.
    name = claim.get("name") or claim.get("description")
    if name:
        out["name"] = name

    # Date rename.
    if "assessmentDate" in claim:
        out["claimDate"] = claim["assessmentDate"]

    # Criteria rename.
    criteria = claim.get("assessmentCriteria")
    if isinstance(criteria, list):
        out["referenceCriteria"] = [_clean_v06_object(c) for c in criteria if isinstance(c, dict)]

    # Standard / Regulation: scalar → single-element list (step 8).
    if isinstance(claim.get("referenceStandard"), dict):
        out["referenceStandard"] = [claim["referenceStandard"]]
    elif isinstance(claim.get("referenceStandard"), list):
        out["referenceStandard"] = claim["referenceStandard"]
    if isinstance(claim.get("referenceRegulation"), dict):
        out["referenceRegulation"] = [claim["referenceRegulation"]]
    elif isinstance(claim.get("referenceRegulation"), list):
        out["referenceRegulation"] = claim["referenceRegulation"]

    # Performance readings.
    declared = claim.get("declaredValue")
    if isinstance(declared, list):
        perf = [_v06_metric_to_v07_performance(m) for m in declared if isinstance(m, dict)]
        if perf:
            out["claimedPerformance"] = perf

    # Conformity topic.
    topic = claim.get("conformityTopic")
    if isinstance(topic, str) and topic:
        out["conformityTopic"] = [{"type": ["ConformityTopic"], "name": topic, "id": topic}]
    elif isinstance(topic, list):
        out["conformityTopic"] = topic

    # Evidence link.
    evidence = claim.get("conformityEvidence")
    if isinstance(evidence, dict):
        out["evidence"] = [evidence]

    return out


def _v06_metric_to_v07_performance(metric: dict[str, Any]) -> dict[str, Any]:
    """Turn a v0.6 ``Metric`` into a v0.7 ``Performance``."""
    perf: dict[str, Any] = {
        "metric": {
            "type": ["PerformanceMetric"],
            "name": metric.get("metricName") or "",
        },
    }
    metric_value = metric.get("metricValue")
    if isinstance(metric_value, dict):
        perf["measure"] = metric_value
    score = metric.get("score")
    if score:
        perf["score"] = {"code": str(score)}
    return perf


def _scorecard_to_claim(
    *, topic: str, scorecard: dict[str, Any], topic_name: str
) -> dict[str, Any]:
    """Materialise a v0.6 scorecard as a v0.7 ``Claim``.

    The conversion is structural: each numeric field on the scorecard
    becomes a ``Performance`` entry with the field name as the metric
    label. Free-form Link fields (e.g. ``recyclingInformation``) are
    promoted to ``evidence`` entries.
    """
    perfs: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for k, v in scorecard.items():
        if k in {"type", "reportingStandard"}:
            continue
        if isinstance(v, (int, float)):
            # Carbon footprints, recyclable-content fractions, MCI, etc.
            perfs.append(
                {
                    "metric": {"type": ["PerformanceMetric"], "name": k},
                    "measure": {"value": float(v), "unit": "C62"},  # dimensionless
                },
            )
        elif isinstance(v, dict) and ("linkURL" in v or "href" in v):
            link = dict(v)
            link.setdefault("name", k)
            evidence.append(link)

    claim: dict[str, Any] = {
        "type": ["Claim"],
        "id": f"urn:dppvalidator:upgrade:{topic}-claim",
        "name": f"{topic_name} (upgraded from v0.6 scorecard)",
        "description": (
            f"Synthesised from the v0.6 {topic} scorecard. Field-by-field "
            "fidelity is best-effort; review before publishing."
        ),
        "conformityTopic": [
            {
                "type": ["ConformityTopic"],
                "id": f"https://vocabulary.uncefact.org/conformity-topic/{topic}",
                "name": topic_name,
            },
        ],
    }
    if perfs:
        claim["claimedPerformance"] = perfs
    if evidence:
        claim["evidence"] = evidence
    reporting_standard = scorecard.get("reportingStandard")
    if isinstance(reporting_standard, dict):
        claim["referenceStandard"] = [reporting_standard]
    return claim


def _clean_v06_object(obj: dict[str, Any]) -> dict[str, Any]:
    """Pass through a v0.6 reference object largely untouched.

    Steps 15 (strip type) and 16 (rename schemeID) walk the whole tree
    later, so we don't need to recurse here. The reason this helper
    exists at all is to ensure we get a *new* dict reference (not a
    shared mutable from the input), which keeps the deep-copy
    invariant tight.
    """
    return dict(obj)


# =============================================================================
# Step 8 — wrap scalar Standard / Regulation into single-element lists
# =============================================================================


def _step8_wrap_claim_references(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Ensure ``referenceStandard`` / ``referenceRegulation`` are lists.

    Step 6 already wrapped scalars during the conformityClaim → performanceClaim
    rewrite. This step is the safety net for performanceClaim entries
    that *originated* in 0.7 shape (e.g. mixed payloads or already
    upgraded data run through the shim a second time).
    """
    claims = cs.get("performanceClaim")
    if not isinstance(claims, list):
        return
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        for key in ("referenceStandard", "referenceRegulation"):
            value = claim.get(key)
            if isinstance(value, dict):
                claim[key] = [value]


# =============================================================================
# Step 9 — wrap scalar country codes
# =============================================================================


def _step9_wrap_country_codes(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],
    country_lookup: Mapping[str, str] | None,
    valid_codes: frozenset[str],
) -> None:
    """Wrap ISO-2 strings into ``{countryCode, countryName}`` objects.

    Walks ``credentialSubject.countryOfProduction`` (Product-level) and
    every ``Material.originCountry`` under ``materialProvenance``.

    - If the code is not in :data:`get_bundled_country_codes`, emit
      ``UPG003`` and still wrap (the v0.7 model regex will catch it
      downstream, but the structural shape is at least correct).
    - If the caller supplied a ``country_lookup`` map and the code
      resolves, populate ``countryName``. Otherwise leave it unset and
      emit ``UPG002`` so the caller can fill it in manually.
    """
    _wrap_country_at(
        cs, "countryOfProduction", "credentialSubject", warnings, country_lookup, valid_codes
    )
    materials = cs.get("materialProvenance")
    if isinstance(materials, list):
        for i, m in enumerate(materials):
            if isinstance(m, dict):
                _wrap_country_at(
                    m,
                    "originCountry",
                    f"credentialSubject.materialProvenance[{i}]",
                    warnings,
                    country_lookup,
                    valid_codes,
                )


def _wrap_country_at(
    obj: dict[str, Any],
    field: str,
    path: str,
    warnings: list[UpgradeWarning],
    country_lookup: Mapping[str, str] | None,
    valid_codes: frozenset[str],
) -> None:
    """Wrap a scalar at ``obj[field]`` into a Country object in place."""
    value = obj.get(field)
    if not isinstance(value, str):
        # Already an object, missing, or a list — nothing to do.
        return
    code = value.strip().upper()
    out: dict[str, Any] = {"countryCode": code}
    if code not in valid_codes:
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_UNMAPPED_COUNTRY,
                path=f"{path}.{field}",
                message=(
                    f"Country code {code!r} is not in the bundled ISO-3166-1 "
                    "alpha-2 list — wrapped structurally but the value will "
                    "fail v0.7 validation."
                ),
            ),
        )
    elif country_lookup is not None and code in country_lookup:
        out["countryName"] = country_lookup[code]
    else:
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_SYNTHESISED,
                path=f"{path}.{field}.countryName",
                message=(
                    "Country wrapped without ``countryName`` — pass a "
                    "country_lookup mapping to populate it."
                ),
                severity=UpgradeSeverity.INFO,
            ),
        )
    obj[field] = out


# =============================================================================
# Step 10 — wrap Product.productCategory: Classification into a list
# =============================================================================


def _step10_wrap_product_category(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """``productCategory`` was scalar in 0.6, list in 0.7."""
    pc = cs.get("productCategory")
    if isinstance(pc, dict):
        cs["productCategory"] = [pc]


# =============================================================================
# Step 11 — Product.producedByParty → relatedParty[]
# =============================================================================


def _step11_party_to_related_party(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Wrap ``producedByParty: Party`` into ``relatedParty: [PartyRole]``.

    The role is fixed to ``"manufacturer"`` because that's the implied
    relationship of a producedByParty in v0.6. We append rather than
    overwrite ``relatedParty`` to be safe with mixed-source payloads.
    """
    party = cs.pop("producedByParty", None)
    if not isinstance(party, dict):
        return
    related = list(cs.get("relatedParty") or [])
    related.append({"role": "manufacturer", "party": party})
    cs["relatedParty"] = related


# =============================================================================
# Step 12 — Product.furtherInformation → relatedDocument[]
# =============================================================================


def _step12_further_information_to_related_document(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Append ``furtherInformation`` links to ``relatedDocument``."""
    further = cs.pop("furtherInformation", None)
    if not further:
        return
    related = list(cs.get("relatedDocument") or [])
    if isinstance(further, list):
        related.extend(further)
    elif isinstance(further, dict):
        related.append(further)
    cs["relatedDocument"] = related


# =============================================================================
# Step 13 — drop Product.registeredId
# =============================================================================


def _step13_drop_registered_id(cs: dict[str, Any], warnings: list[UpgradeWarning]) -> None:
    """``registeredId`` moves from Product to Party in v0.7."""
    if "registeredId" in cs:
        cs.pop("registeredId")
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_LOSSY,
                path="credentialSubject.registeredId",
                message=(
                    "v0.6 Product.registeredId has no v0.7 equivalent on "
                    "Product — the field has moved to Party. The value was "
                    "dropped; if required, re-attach it to "
                    "Product.relatedParty[*].party.registeredId manually."
                ),
            ),
        )


# =============================================================================
# Step 14 — Material.symbol base64 string → Image object
# =============================================================================


def _step14_material_symbol_to_image(cs: dict[str, Any], warnings: list[UpgradeWarning]) -> None:
    """Convert the inline base64 ``symbol`` string to a v0.7 ``Image``.

    Sentinel placeholders (``"undefined"`` and friends) are dropped —
    smuggling them through as fake image bytes would just trip the v0.7
    schema downstream.
    """
    materials = cs.get("materialProvenance")
    if not isinstance(materials, list):
        return
    for i, m in enumerate(materials):
        if not isinstance(m, dict):
            continue
        symbol = m.get("symbol")
        if not isinstance(symbol, str):
            continue
        if symbol.lower() in _KNOWN_SYMBOL_PLACEHOLDERS:
            m.pop("symbol", None)
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_LOSSY,
                    path=f"credentialSubject.materialProvenance[{i}].symbol",
                    message=(
                        f"Material.symbol placeholder {symbol!r} dropped during "
                        "upgrade — provide a real Image object if needed."
                    ),
                    severity=UpgradeSeverity.INFO,
                ),
            )
            continue
        if not _looks_like_base64(symbol):
            m.pop("symbol", None)
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_LOSSY,
                    path=f"credentialSubject.materialProvenance[{i}].symbol",
                    message=(
                        "Material.symbol value did not look like base64 — "
                        "dropped during upgrade. Provide a v0.7 Image object."
                    ),
                ),
            )
            continue
        m["symbol"] = {
            "type": ["Image"],
            "name": _DEFAULT_IMAGE_NAME,
            "imageData": symbol,
            "mediaType": _DEFAULT_IMAGE_MEDIA_TYPE,
        }
        warnings.append(
            UpgradeWarning(
                code=UPG_CODE_SYNTHESISED,
                path=f"credentialSubject.materialProvenance[{i}].symbol",
                message=(
                    "Material.symbol upgraded to v0.7 Image with synthesised "
                    f"name={_DEFAULT_IMAGE_NAME!r} and "
                    f"mediaType={_DEFAULT_IMAGE_MEDIA_TYPE!r}."
                ),
            ),
        )


def _looks_like_base64(value: str) -> bool:
    """Heuristic: would this string decode as base64?

    We tolerate URL-safe variants and strip whitespace before checking.
    Anything under 16 characters is treated as not-an-image to weed out
    short sentinels. This is intentionally conservative — false negatives
    just route the value into the lossy-drop path with a UPG001 warning.
    """
    s = value.strip()
    if len(s) < 16:
        return False
    try:
        base64.b64decode(s, validate=True)
    except (ValueError, base64.binascii.Error):  # type: ignore[attr-defined]
        return False
    return True


# =============================================================================
# Step 15 — strip type arrays on embedded objects
# =============================================================================


def _step15_strip_embedded_types(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Strip ``type`` from embedded objects whose v0.7 schema dropped it.

    Walks the credential subject tree and removes the ``type`` field on
    any sub-object whose key matches :data:`_TYPES_TO_STRIP_ON`. The
    Product-level ``type`` (``["Product"]``) is preserved.
    """
    _strip_types_recursive(cs, parent_key=None)


def _strip_types_recursive(node: Any, parent_key: str | None) -> None:
    if isinstance(node, dict):
        if parent_key in _TYPES_TO_STRIP_ON and "type" in node:
            node.pop("type", None)
        for k, v in node.items():
            _strip_types_recursive(v, k)
    elif isinstance(node, list):
        for item in node:
            _strip_types_recursive(item, parent_key)


# =============================================================================
# Step 16 — rename Classification.schemeID → schemeId
# =============================================================================


def _step16_rename_scheme_id(
    cs: dict[str, Any],
    warnings: list[UpgradeWarning],  # noqa: ARG001 — uniform signature; no warnings emitted
) -> None:
    """Rename ``schemeID`` (v0.6) to ``schemeId`` (v0.7) everywhere.

    Walks the credential subject tree without restriction — Classification
    objects can hide under ``materialType``, ``productCategory[*]``,
    ``performanceClaim[*].referenceCriteria[*].category[*]``, and so on.
    A blind rename is correct because no other v0.6 schema uses the
    uppercase spelling.
    """
    _rename_key_recursive(cs, "schemeID", "schemeId")


def _rename_key_recursive(node: Any, old: str, new: str) -> None:
    if isinstance(node, dict):
        if old in node:
            node[new] = node.pop(old)
        for v in node.values():
            _rename_key_recursive(v, old, new)
    elif isinstance(node, list):
        for item in node:
            _rename_key_recursive(item, old, new)


# =============================================================================
# Step 17 — Material required-field detection
# =============================================================================


def _step17_material_required_fields(cs: dict[str, Any], warnings: list[UpgradeWarning]) -> None:
    """Emit UPG004 per Material missing ``materialType`` or ``massFraction``.

    These were optional in v0.6 and are required in v0.7. We don't
    fabricate them — the caller has to supply real values before the
    upgraded payload can validate.
    """
    materials = cs.get("materialProvenance")
    if not isinstance(materials, list):
        return
    for i, m in enumerate(materials):
        if not isinstance(m, dict):
            continue
        if not m.get("materialType"):
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_REQUIRED_FIELD_MISSING,
                    path=f"credentialSubject.materialProvenance[{i}].materialType",
                    message=(
                        "Material.materialType is required in v0.7.0. The "
                        "v0.6 source did not supply one; provide a "
                        "Classification object before validating."
                    ),
                    severity=UpgradeSeverity.ERROR,
                ),
            )
        if "massFraction" not in m or m.get("massFraction") is None:
            warnings.append(
                UpgradeWarning(
                    code=UPG_CODE_REQUIRED_FIELD_MISSING,
                    path=f"credentialSubject.materialProvenance[{i}].massFraction",
                    message=(
                        "Material.massFraction is required in v0.7.0. The "
                        "v0.6 source did not supply one; provide a numeric "
                        "value before validating."
                    ),
                    severity=UpgradeSeverity.ERROR,
                ),
            )
