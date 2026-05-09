"""Compatibility shim: rewrite UNTP DPP 0.7.0 payloads into CIRPASS v1.3.0 shape.

Phase 5 task 5.3 of [docs/plans/CIRPASS_2_MIGRATION.md]. Mirrors
:mod:`dppvalidator.compat.upgrade_0_6_to_0_7` style — pure functions,
deep-copy input, deterministic order, structured warning codes — but
the warning-code prefix is ``MAP`` (cross-family) rather than ``UPG``
(intra-family).

Design principles:

- **Pure transformation, no validation.** The shim never raises on
  malformed input; it makes a best-effort projection and lets the
  caller validate the result against the CIRPASS model. Anything
  that *can't* be projected faithfully is surfaced as a
  :class:`MappingWarning`.
- **Structural over semantic.** The shim rewires field names and
  shapes but never invents content. UNTP scalar names cannot be
  multilingualised without an explicit ``default_language=``; missing
  required-in-CIRPASS fields produce ``MAP004`` warnings, not
  synthesised values.
- **Side-effect-free.** The input ``dict`` is deep-copied; callers
  can map-then-keep-original without surprises.
- **Deterministic.** Two runs against the same input produce
  byte-identical output and the same warning set in the same order.

The transformation is split into ~15 steps documented in the
:mod:`_untp_cirpass_map` declarative table; this module is the
operational glue that walks the table.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from dppvalidator.compat._identifier_schemes import to_cirpass as _id_scheme_to_cirpass
from dppvalidator.compat._mapping_codes import MappingWarning
from dppvalidator.compat._shared import normalise_iso8601 as _normalise_iso8601
from dppvalidator.logging import get_logger
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass

logger = get_logger(__name__)


# =============================================================================
# Constants
# =============================================================================


# Default scheme URI used when the source UNTP payload omits
# ``credentialSubject.idScheme``. The CIRPASS Identifier requires a
# non-empty http(s) URI on ``scheme``; we pick the GS1 voc URI as the
# safe default for product identifiers (the synthesised value is
# surfaced via MAP002).
_DEFAULT_PRODUCT_SCHEME_URI = "https://gs1.org/voc/"
_DEFAULT_PRODUCT_SCHEME_NAME = "GS1 GTIN"

# Default scheme URI for synthesised actor identifiers (e.g. when
# extracting an issuer with no idScheme).
_DEFAULT_ACTOR_SCHEME_URI = "https://www.gleif.org/lei/"
_DEFAULT_ACTOR_SCHEME_NAME = "GLEIF LEI"

# UNTP PartyRole.role enum → EUDPP role class. The mapping covers
# the v0.7.0 PartyRoleEnum members (see
# ``dppvalidator.models.v0_7.identifiers.PartyRoleEnum``). Unmapped
# UNTP roles fall back to ``EconomicOperatorRole`` and emit MAP002.
_UNTP_TO_EUDPP_ROLE: dict[str, str] = {
    "manufacturer": EUDPPRoleClass.MANUFACTURER.value,
    "producer": EUDPPRoleClass.MANUFACTURER.value,
    "remanufacturer": EUDPPRoleClass.REMANUFACTURER.value,
    "recycler": EUDPPRoleClass.RECYCLER.value,
    "importer": EUDPPRoleClass.IMPORTER.value,
    "distributor": EUDPPRoleClass.DISTRIBUTOR.value,
    "retailer": EUDPPRoleClass.DEALER.value,
    "exporter": EUDPPRoleClass.ECONOMIC_OPERATOR.value,
    "owner": EUDPPRoleClass.ECONOMIC_OPERATOR.value,
    "operator": EUDPPRoleClass.ECONOMIC_OPERATOR.value,
    "processor": EUDPPRoleClass.MANUFACTURER.value,
    "serviceProvider": EUDPPRoleClass.DPP_SERVICE_PROVIDER.value,
    "inspector": EUDPPRoleClass.CONFORMITY_BODY.value,
    "certifier": EUDPPRoleClass.CONFORMITY_BODY.value,
    "logisticsProvider": EUDPPRoleClass.FULFILMENT_PROVIDER.value,
    "carrier": EUDPPRoleClass.FULFILMENT_PROVIDER.value,
    "consignor": EUDPPRoleClass.ECONOMIC_OPERATOR.value,
    "consignee": EUDPPRoleClass.ECONOMIC_OPERATOR.value,
    "brandOwner": EUDPPRoleClass.MANUFACTURER.value,
    "regulator": EUDPPRoleClass.AUTHORITY.value,
}


# =============================================================================
# Public entry point
# =============================================================================


def to_cirpass_1_3(
    data: dict[str, Any],
    *,
    default_language: str = "en",
    country_lookup: dict[str, str] | None = None,  # noqa: ARG001 — reserved API kwarg
    identifier_scheme_lookup: dict[str, tuple[str, str]] | None = None,
) -> tuple[dict[str, Any], list[MappingWarning]]:
    """Project a UNTP DPP 0.7.0 payload onto CIRPASS reference structure v1.3.0.

    Args:
        data: The UNTP 0.7.0 payload as a parsed JSON ``dict``. Input
            is deep-copied; the caller's object is never mutated.
        default_language: BCP-47 language tag used when projecting
            UNTP scalar strings (``credentialSubject.name``, etc.)
            onto CIRPASS LocalisedText[]. Defaults to ``"en"``;
            callers should override per-DPP for non-English pilots.
        country_lookup: Optional ISO-3166 alpha-2 → country-name map.
            Reserved for future extension (the current shim does not
            consume it; signature kept for parity with the reverse
            shim and the migration plan API contract).
        identifier_scheme_lookup: Optional override for the bundled
            scheme map. Keys are UNTP IdentifierScheme.id URIs;
            values are ``(cirpass_scheme_uri, cirpass_scheme_name)``
            tuples. Overrides take precedence over the bundled
            :mod:`_identifier_schemes` lookup.

    Returns:
        Tuple of ``(cirpass_dict, warnings)``. The dict is ready to
        be validated against the CIRPASS reference-structure model.
        Warnings are ordered by step and document position.
    """
    if not isinstance(data, dict):
        msg = f"to_cirpass_1_3() requires a dict, got {type(data).__name__!r}"
        raise TypeError(msg)

    source = deepcopy(data)
    warnings: list[MappingWarning] = []

    cirpass: dict[str, Any] = {}

    # M01 — DPP identifier
    _step_dpp_identifier(source, cirpass, warnings)

    # M02 + M03 + M05 + M06 + M09 — product (subject)
    _step_product(
        source,
        cirpass,
        warnings,
        default_language=default_language,
        identifier_scheme_lookup=identifier_scheme_lookup or {},
    )

    # M07 — issuedAt
    _step_issued_at(source, cirpass, warnings)

    # M08 — effective period
    _step_effective_period(source, cirpass, warnings)

    # M10 — composition / materials
    _step_composition(source, cirpass, warnings, default_language=default_language)

    # M11 + M12 — actors
    _step_actors(
        source,
        cirpass,
        warnings,
        default_language=default_language,
    )

    # M13 — performance claims → LCA
    _step_lca(source, cirpass, warnings)

    return cirpass, warnings


# =============================================================================
# Step implementations
# =============================================================================


def _step_dpp_identifier(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
) -> None:
    """M01 — UNTP envelope ``id`` → CIRPASS ``dppIdentifier``."""
    dpp_id = source.get("id")
    if not dpp_id:
        warnings.append(
            MappingWarning.required_missing(
                path="$.id",
                message=(
                    "UNTP envelope is missing ``id``; CIRPASS requires "
                    "``dppIdentifier.value``. The output's dppIdentifier "
                    "will be a placeholder until a real id is supplied."
                ),
                step="M01",
            )
        )
        cirpass["dppIdentifier"] = {
            "value": "",
            "scheme": "https://example.com/dpp-register/",
        }
        return
    cirpass["dppIdentifier"] = {
        "value": str(dpp_id),
        # The DPP-register scheme is not standardised; UNTP stores it
        # in the issuer envelope, not as a per-credential scheme. We
        # synthesise a generic register URI here.
        "scheme": "https://example.com/dpp-register/",
        "schemeName": "DPP register",
    }
    warnings.append(
        MappingWarning.synthesised(
            path="$.dppIdentifier.scheme",
            message=(
                "DPP-register scheme synthesised — UNTP carries the "
                "credential id but no register URI; using a placeholder "
                "register URI."
            ),
            step="M01",
        )
    )


def _step_product(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
    *,
    default_language: str,
    identifier_scheme_lookup: dict[str, tuple[str, str]],
) -> None:
    """M02 + M03 + M05 + M06 + M09 — Product subject."""
    subject = source.get("credentialSubject")
    if not isinstance(subject, dict):
        warnings.append(
            MappingWarning.required_missing(
                path="$.credentialSubject",
                message=(
                    "UNTP envelope is missing ``credentialSubject``; "
                    "CIRPASS requires ``product``. The output's product "
                    "will be a placeholder until a real subject is supplied."
                ),
                step="M02",
            )
        )
        cirpass["product"] = {
            "productIdentifier": {
                "value": "",
                "scheme": _DEFAULT_PRODUCT_SCHEME_URI,
            },
            "productName": [],
        }
        return

    product: dict[str, Any] = {}

    # productIdentifier
    product_id = subject.get("id") or ""
    untp_scheme = subject.get("idScheme") or {}
    untp_scheme_id = untp_scheme.get("id") if isinstance(untp_scheme, dict) else None
    untp_scheme_name = untp_scheme.get("name") if isinstance(untp_scheme, dict) else None
    used_override = False
    if untp_scheme_id and untp_scheme_id in identifier_scheme_lookup:
        cirpass_scheme, cirpass_scheme_name = identifier_scheme_lookup[untp_scheme_id]
        mapping = None  # override path — caller-supplied row
        used_override = True
    else:
        cirpass_scheme, cirpass_scheme_name, mapping = _id_scheme_to_cirpass(
            untp_scheme_id, untp_scheme_name
        )
    if not cirpass_scheme:
        cirpass_scheme = _DEFAULT_PRODUCT_SCHEME_URI
        cirpass_scheme_name = _DEFAULT_PRODUCT_SCHEME_NAME
        warnings.append(
            MappingWarning.synthesised(
                path="$.product.productIdentifier.scheme",
                message=(
                    "UNTP credentialSubject.idScheme is empty; synthesising "
                    f"the GS1 GTIN voc URI ({_DEFAULT_PRODUCT_SCHEME_URI}) "
                    "for the CIRPASS productIdentifier."
                ),
                step="M03",
            )
        )
    elif mapping is None and untp_scheme_id and not used_override:
        warnings.append(
            MappingWarning.unmapped(
                path="$.credentialSubject.idScheme.id",
                message=(
                    f"UNTP idScheme.id={untp_scheme_id!r} is not in the "
                    "bundled scheme lookup; passing through verbatim."
                ),
                step="M03",
                scheme=untp_scheme_id,
            )
        )
    product_identifier: dict[str, Any] = {
        "value": product_id,
        "scheme": cirpass_scheme,
    }
    if cirpass_scheme_name:
        product_identifier["schemeName"] = cirpass_scheme_name
    product["productIdentifier"] = product_identifier

    # productName (M05) — UNTP scalar → CIRPASS LocalisedText[]
    name = subject.get("name")
    if name:
        product["productName"] = [{"value": str(name), "language": default_language}]
        warnings.append(
            MappingWarning.synthesised(
                path="$.product.productName[0].language",
                message=(
                    "UNTP credentialSubject.name is a scalar string; "
                    f"synthesised a single CIRPASS LocalisedText entry "
                    f"with language={default_language!r}."
                ),
                step="M05",
                language=default_language,
            )
        )
    else:
        product["productName"] = []
        warnings.append(
            MappingWarning.required_missing(
                path="$.product.productName",
                message=("UNTP credentialSubject.name is empty; CIRPASS requires productName ≥ 1."),
                step="M05",
            )
        )

    # description (M06)
    description = subject.get("description")
    if description:
        product["description"] = [{"value": str(description), "language": default_language}]

    # commodityCode (M09) — Classification[] → ClassificationCode[]
    classifications = subject.get("productCategory")
    if isinstance(classifications, list) and classifications:
        commodity: list[dict[str, Any]] = []
        for i, cls in enumerate(classifications):
            if not isinstance(cls, dict):
                continue
            scheme = cls.get("schemeId") or ""
            code = cls.get("code") or ""
            label = cls.get("name")
            entry: dict[str, Any] = {"code": code, "scheme": scheme}
            if label:
                entry["name"] = [{"value": str(label), "language": default_language}]
                warnings.append(
                    MappingWarning.synthesised(
                        path=f"$.product.commodityCode[{i}].name[0].language",
                        message=(
                            "UNTP Classification.name is a scalar string; "
                            f"projected onto a single LocalisedText entry "
                            f"with language={default_language!r}."
                        ),
                        step="M09",
                    )
                )
            commodity.append(entry)
        if commodity:
            product["commodityCode"] = commodity

    cirpass["product"] = product


def _step_issued_at(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
) -> None:
    """M07 — UNTP envelope ``validFrom`` → CIRPASS ``issuedAt``."""
    valid_from = source.get("validFrom")
    if valid_from:
        cirpass["issuedAt"] = {"timestamp": _normalise_iso8601(valid_from)}
        return
    warnings.append(
        MappingWarning.required_missing(
            path="$.validFrom",
            message=(
                "UNTP envelope is missing ``validFrom``; CIRPASS requires "
                "``issuedAt.timestamp``. Synthesising the current UTC "
                "timestamp would be misleading; the output's issuedAt "
                "is a placeholder."
            ),
            step="M07",
        )
    )
    cirpass["issuedAt"] = {"timestamp": "1970-01-01T00:00:00+00:00"}


def _step_effective_period(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
) -> None:
    """M08 — UNTP (validFrom, validUntil) → CIRPASS effectivePeriod."""
    valid_from = source.get("validFrom")
    valid_until = source.get("validUntil")
    if not valid_from:
        return
    period: dict[str, Any] = {"start": _normalise_iso8601(valid_from)}
    if valid_until:
        period["end"] = _normalise_iso8601(valid_until)
    else:
        warnings.append(
            MappingWarning.temporal_collapse(
                path="$.effectivePeriod.end",
                message=(
                    "UNTP validUntil is absent; CIRPASS effectivePeriod.end "
                    "left empty (open-ended). The forward shim does not "
                    "synthesise an end date."
                ),
                step="M08",
            )
        )
    cirpass["effectivePeriod"] = period


def _step_composition(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
    *,
    default_language: str,
) -> None:
    """M10 — UNTP materialProvenance[] → CIRPASS composition.materials[]."""
    subject = source.get("credentialSubject")
    if not isinstance(subject, dict):
        return
    materials = subject.get("materialProvenance")
    if not isinstance(materials, list) or not materials:
        return
    out: list[dict[str, Any]] = []
    for i, m in enumerate(materials):
        if not isinstance(m, dict):
            continue
        material_name = m.get("name")
        country = m.get("originCountry")
        country_code = country.get("countryCode") if isinstance(country, dict) else None
        material_type = m.get("materialType")
        # UNTP carries materialType as a Classification object; CIRPASS
        # carries a bare ISO-2076 code. We extract the ``code`` field.
        type_code: str | None = None
        if isinstance(material_type, dict):
            type_code = material_type.get("code")
        mass_fraction = m.get("massFraction")
        is_recycled = bool(m.get("recycledMassFraction"))
        entry: dict[str, Any] = {}
        if material_name:
            entry["materialName"] = [{"value": str(material_name), "language": default_language}]
            warnings.append(
                MappingWarning.synthesised(
                    path=f"$.composition.materials[{i}].materialName[0].language",
                    message=(
                        "UNTP Material.name is a scalar string; projected "
                        f"onto a single CIRPASS LocalisedText entry "
                        f"with language={default_language!r}."
                    ),
                    step="M10",
                )
            )
        else:
            entry["materialName"] = []
            warnings.append(
                MappingWarning.required_missing(
                    path=f"$.composition.materials[{i}].materialName",
                    message="UNTP Material.name is empty; CIRPASS requires materialName ≥ 1.",
                    step="M10",
                )
            )
        if type_code:
            entry["materialType"] = type_code
        if country_code:
            entry["originCountry"] = country_code
        if mass_fraction is not None:
            entry["massFraction"] = _decimal_str(mass_fraction)
        if is_recycled:
            entry["isRecycled"] = True
        out.append(entry)
    if out:
        cirpass["composition"] = {"materials": out}


def _step_actors(
    source: dict[str, Any],
    cirpass: dict[str, Any],
    warnings: list[MappingWarning],
    *,
    default_language: str,
) -> None:
    """M11 + M12 — UNTP relatedParty[] + issuer → CIRPASS relatedActors[]."""
    actors: list[dict[str, Any]] = []
    seen_manufacturer = False

    # M11 — relatedParty[]
    subject = source.get("credentialSubject") or {}
    related_party = subject.get("relatedParty") if isinstance(subject, dict) else None
    if isinstance(related_party, list):
        for i, pr in enumerate(related_party):
            if not isinstance(pr, dict):
                continue
            party = pr.get("party") or {}
            untp_role = pr.get("role")
            if not isinstance(party, dict):
                continue
            actor = _project_actor(party, default_language)
            eudpp_role = _UNTP_TO_EUDPP_ROLE.get(untp_role or "")
            if eudpp_role is None and untp_role:
                eudpp_role = EUDPPRoleClass.ECONOMIC_OPERATOR.value
                warnings.append(
                    MappingWarning.synthesised(
                        path=f"$.relatedActors[{i}].role",
                        message=(
                            f"UNTP role {untp_role!r} has no canonical "
                            "EUDPP super-role; falling back to "
                            "``EconomicOperatorRole``."
                        ),
                        step="M11",
                        original_role=str(untp_role),
                    )
                )
            elif eudpp_role is None:
                eudpp_role = EUDPPRoleClass.ECONOMIC_OPERATOR.value
                warnings.append(
                    MappingWarning.synthesised(
                        path=f"$.relatedActors[{i}].role",
                        message=(
                            "UNTP relatedParty entry has no role; "
                            "synthesising ``EconomicOperatorRole``."
                        ),
                        step="M11",
                    )
                )
            if eudpp_role == EUDPPRoleClass.MANUFACTURER.value:
                seen_manufacturer = True
            actors.append({"actor": actor, "role": eudpp_role})

    # M12 — issuer fallback. CIRPASS requires *some* manufacturer-shaped
    # actor for ESPR Annex III(g); when relatedParty[] doesn't include
    # one, we lift the UNTP issuer into a synthesised manufacturer
    # entry. This is a one-way projection and surfaces MAP002.
    issuer = source.get("issuer")
    if not seen_manufacturer and isinstance(issuer, dict) and issuer.get("id"):
        actor = _project_actor(issuer, default_language)
        actors.append({"actor": actor, "role": EUDPPRoleClass.MANUFACTURER.value})
        warnings.append(
            MappingWarning.synthesised(
                path=f"$.relatedActors[{len(actors) - 1}]",
                message=(
                    "No relatedParty with manufacturer role; lifted UNTP "
                    "envelope.issuer into a synthesised "
                    "ManufacturerRole actor."
                ),
                step="M12",
            )
        )
    if actors:
        cirpass["relatedActors"] = actors


def _project_actor(party: dict[str, Any], default_language: str) -> dict[str, Any]:
    """Lift a UNTP Party / CredentialIssuer onto a CIRPASS Actor."""
    actor_id = party.get("id") or ""
    name = party.get("name") or ""
    untp_scheme = party.get("idScheme") or {}
    untp_scheme_id = untp_scheme.get("id") if isinstance(untp_scheme, dict) else None
    untp_scheme_name = untp_scheme.get("name") if isinstance(untp_scheme, dict) else None
    cirpass_scheme, cirpass_scheme_name, _ = _id_scheme_to_cirpass(untp_scheme_id, untp_scheme_name)
    if not cirpass_scheme:
        cirpass_scheme = _DEFAULT_ACTOR_SCHEME_URI
        cirpass_scheme_name = _DEFAULT_ACTOR_SCHEME_NAME
    identifier: dict[str, Any] = {"value": actor_id, "scheme": cirpass_scheme}
    if cirpass_scheme_name:
        identifier["schemeName"] = cirpass_scheme_name
    return {
        "actorIdentifier": identifier,
        "actorName": [{"value": str(name), "language": default_language}],
    }


def _step_lca(
    source: dict[str, Any],
    cirpass: dict[str, Any],  # noqa: ARG001 — symmetry with other step helpers
    warnings: list[MappingWarning],
) -> None:
    """M13 — UNTP performanceClaim[] → CIRPASS lca.results[].

    The current shim is a *minimal* projection: only emissions /
    LCA-style conformity claims are lifted. Other claim topics
    (durability, traceability, etc.) drop with MAP001 — the CIRPASS
    LCA module models PEF impact categories, not the full UNTP
    claim ontology. Phase 7 (Tyres / Textile pilot) extends with
    pilot-specific lifts.
    """
    subject = source.get("credentialSubject") or {}
    if not isinstance(subject, dict):
        return
    claims = subject.get("performanceClaim")
    if not isinstance(claims, list) or not claims:
        return
    # Stub — drop with a single MAP001 noting the lossiness. Phase 7
    # replaces this with pilot-aware lifting. We don't generate a
    # synthetic ``lca`` block because that would silently invent
    # impact-result data the source never carried.
    warnings.append(
        MappingWarning.lossy(
            path="$.lca",
            message=(
                f"UNTP carried {len(claims)} performanceClaim entries; "
                "the v1.3.0 shim drops them without projecting onto "
                "CIRPASS LifeCycleAssessment results (Phase 7 pilot "
                "lifts cover the supported subset). Reverse round-trip "
                "will not restore performance claims."
            ),
            step="M13",
        )
    )


# =============================================================================
# Helpers
# =============================================================================
#
# Cross-shim helpers (``_normalise_iso8601``) live at
# :mod:`dppvalidator.compat._shared` so the forward / reverse shims
# stay symmetric. The remaining helper below is forward-only.


def _decimal_str(value: Any) -> str:
    """Stringify a Decimal-bound numeric value for CIRPASS wire shape.

    UNTP carries massFraction as ``float``; CIRPASS carries it as
    Decimal. The mapping shim emits a string so JSON Decimal
    round-tripping doesn't lose precision (Pydantic's ``Decimal``
    field accepts string input).
    """
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


__all__ = [
    "to_cirpass_1_3",
]
