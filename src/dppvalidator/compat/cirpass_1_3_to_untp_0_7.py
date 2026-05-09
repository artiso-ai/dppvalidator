"""Compatibility shim: rewrite CIRPASS v1.3.0 payloads into UNTP DPP 0.7.0 shape.

Phase 5 task 5.4 of [docs/plans/CIRPASS_2_MIGRATION.md]. Reverse
direction of :mod:`untp_0_7_to_cirpass_1_3`. Together the two shims
form the round-trip identity over the documented lossless subset
(see ``docs/concepts/untp-cirpass-mapping.md`` for the field-by-
field table).

Lossy transformations on the reverse side:

- CIRPASS LocalisedText[] → UNTP scalar string. Forward picks the
  first entry; additional languages are dropped with one ``MAP001``
  per language.
- CIRPASS substancesOfConcern / connectorRelations / lca have no
  v0.7 base equivalent. The reverse drops them with ``MAP001`` per
  array.
- Multi-actor relationships beyond the manufacturer / single-issuer
  pair flatten into the UNTP relatedParty[] list, with role enum
  remapped through :data:`_EUDPP_TO_UNTP_ROLE`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from dppvalidator.compat._identifier_schemes import to_untp as _id_scheme_to_untp
from dppvalidator.compat._mapping_codes import MappingWarning
from dppvalidator.compat._shared import (
    normalise_iso8601 as _normalise_iso8601,
)
from dppvalidator.compat._shared import (
    pick_localised as _pick_localised,
)
from dppvalidator.logging import get_logger
from dppvalidator.vocabularies.eudpp_actors import EUDPPRoleClass

logger = get_logger(__name__)


# =============================================================================
# Constants
# =============================================================================


# UNTP context URLs and fixed envelope shape. We pin the v0.7.0
# context and W3C VC v2 context here.
_UNTP_CONTEXT_URLS = (
    "https://www.w3.org/ns/credentials/v2",
    "https://vocabulary.uncefact.org/untp/0.7.0/context/",
)

# Default UNTP envelope name. CIRPASS does not carry an envelope-level
# name (the CIRPASS message is the credential subject directly).
# Reverse shim uses the product's first localised name as the envelope
# name, falling back to a generic placeholder.
_DEFAULT_ENVELOPE_NAME = "Digital Product Passport"

# EUDPP role IRI → UNTP PartyRoleEnum value. The forward shim used a
# many-to-many mapping (e.g. ``recycler`` and ``remanufacturer`` both
# project to ``RecyclerRole`` super-category in some cases); reversing
# is therefore lossy. We pick the most-specific UNTP role that the
# v0.7.0 PartyRoleEnum exposes.
_EUDPP_TO_UNTP_ROLE: dict[str, str] = {
    EUDPPRoleClass.MANUFACTURER.value: "manufacturer",
    EUDPPRoleClass.IMPORTER.value: "importer",
    EUDPPRoleClass.DISTRIBUTOR.value: "distributor",
    EUDPPRoleClass.DEALER.value: "retailer",
    EUDPPRoleClass.FULFILMENT_PROVIDER.value: "logisticsProvider",
    EUDPPRoleClass.AUTHORISED_REP.value: "operator",
    EUDPPRoleClass.RECYCLER.value: "recycler",
    EUDPPRoleClass.REFURBISHER.value: "remanufacturer",
    EUDPPRoleClass.REMANUFACTURER.value: "remanufacturer",
    EUDPPRoleClass.CIRCULAR_ECONOMY_ROLE.value: "recycler",
    EUDPPRoleClass.AUTHORITY.value: "regulator",
    EUDPPRoleClass.MARKET_SURVEILLANCE.value: "regulator",
    EUDPPRoleClass.CUSTOMS.value: "regulator",
    EUDPPRoleClass.CUSTOMER.value: "owner",
    EUDPPRoleClass.CONSUMER.value: "owner",
    EUDPPRoleClass.END_USER.value: "owner",
    EUDPPRoleClass.INDEPENDENT_OPERATOR.value: "serviceProvider",
    EUDPPRoleClass.PROFESSIONAL_REPAIRER.value: "serviceProvider",
    EUDPPRoleClass.DPP_SERVICE_PROVIDER.value: "serviceProvider",
    EUDPPRoleClass.CONFORMITY_BODY.value: "certifier",
    EUDPPRoleClass.CONFORMITY_ASSESSMENT_ROLE.value: "certifier",
    EUDPPRoleClass.NOTIFIED_BODY.value: "certifier",
    EUDPPRoleClass.CREDENTIAL_AGENCY.value: "serviceProvider",
    EUDPPRoleClass.ISSUING_AGENCY.value: "serviceProvider",
    EUDPPRoleClass.ECONOMIC_OPERATOR.value: "manufacturer",
    EUDPPRoleClass.ROLE.value: "manufacturer",
}


# =============================================================================
# Public entry point
# =============================================================================


def to_untp_0_7(
    data: dict[str, Any],
    *,
    default_language: str = "en",
    issuer_did: str = "did:web:example.com",
    issuer_name: str = "Unknown Issuer",
    untp_id_granularity: str = "model",
    country_lookup: dict[str, str] | None = None,
    identifier_scheme_lookup: dict[str, tuple[str, str]] | None = None,
) -> tuple[dict[str, Any], list[MappingWarning]]:
    """Project a CIRPASS reference structure v1.3.0 onto UNTP DPP 0.7.0.

    Args:
        data: The CIRPASS payload as a parsed JSON ``dict``. Input is
            deep-copied; the caller's object is never mutated.
        default_language: Preferred BCP-47 tag when picking the
            single-language UNTP scalar from a CIRPASS multilingual
            list. Falls back to the first list entry if no match.
        issuer_did: DID / URI to use as the synthesised UNTP envelope
            issuer ``id`` when CIRPASS carries no manufacturer-role
            actor. Defaults to ``did:web:example.com`` (deliberately
            obviously-fake).
        issuer_name: Human-readable issuer name fallback.
        untp_id_granularity: ``"item"`` / ``"batch"`` / ``"model"``.
            CIRPASS doesn't carry granularity; the caller picks one.
            Defaults to ``"model"`` (the safest choice — doesn't
            require itemNumber / batchNumber).
        country_lookup: Optional ISO-3166 alpha-2 → country-name map.
            Used to populate ``Country.countryName`` from a bare
            ``Material.originCountry`` code.
        identifier_scheme_lookup: Optional override for the bundled
            scheme map. Keys are CIRPASS ``Identifier.scheme`` URIs;
            values are ``(untp_id_scheme_id, untp_id_scheme_name)``.

    Returns:
        Tuple of ``(untp_dict, warnings)``. The dict is ready to be
        validated against the UNTP 0.7.0 envelope.
    """
    if not isinstance(data, dict):
        msg = f"to_untp_0_7() requires a dict, got {type(data).__name__!r}"
        raise TypeError(msg)

    source = deepcopy(data)
    warnings: list[MappingWarning] = []
    country_lookup = country_lookup or {}
    identifier_scheme_lookup = identifier_scheme_lookup or {}

    untp: dict[str, Any] = {
        "@context": list(_UNTP_CONTEXT_URLS),
        "type": ["DigitalProductPassport", "VerifiableCredential"],
    }

    # M01 — DPP identifier
    _step_dpp_id(source, untp, warnings)

    # M02 + M03 + M05 + M06 + M09 — credentialSubject
    _step_credential_subject(
        source,
        untp,
        warnings,
        default_language=default_language,
        identifier_scheme_lookup=identifier_scheme_lookup,
        untp_id_granularity=untp_id_granularity,
        country_lookup=country_lookup,
    )

    # M07 + M08 — temporal envelope
    _step_temporal(source, untp, warnings)

    # M11 + M12 — actors → relatedParty[] + envelope.issuer
    _step_actors(
        source,
        untp,
        warnings,
        default_language=default_language,
        issuer_did=issuer_did,
        issuer_name=issuer_name,
    )

    # M13 + M14 + M15 — drop fields with no UNTP equivalent.
    _step_drop_unmappable(source, untp, warnings)

    # Synthesise the envelope ``name`` field (UNTP requires it) from
    # the credentialSubject.name.
    if "name" not in untp:
        untp_subject = untp.get("credentialSubject") or {}
        untp["name"] = (
            untp_subject.get("name") if isinstance(untp_subject, dict) else None
        ) or _DEFAULT_ENVELOPE_NAME

    return untp, warnings


# =============================================================================
# Step implementations
# =============================================================================


def _step_dpp_id(
    source: dict[str, Any],
    untp: dict[str, Any],
    warnings: list[MappingWarning],
) -> None:
    """M01 — CIRPASS dppIdentifier.value → UNTP envelope.id."""
    dpp = source.get("dppIdentifier")
    if not isinstance(dpp, dict):
        warnings.append(
            MappingWarning.required_missing(
                path="$.id",
                message=("CIRPASS dppIdentifier missing; UNTP envelope.id left empty placeholder."),
                step="M01",
            )
        )
        untp["id"] = ""
        return
    untp["id"] = dpp.get("value") or ""


def _step_credential_subject(
    source: dict[str, Any],
    untp: dict[str, Any],
    warnings: list[MappingWarning],
    *,
    default_language: str,
    identifier_scheme_lookup: dict[str, tuple[str, str]],
    untp_id_granularity: str,
    country_lookup: dict[str, str],
) -> None:
    """M02 + M03 + M05 + M06 + M09 — Product credentialSubject."""
    product = source.get("product")
    if not isinstance(product, dict):
        warnings.append(
            MappingWarning.required_missing(
                path="$.credentialSubject",
                message=(
                    "CIRPASS payload is missing ``product``; UNTP requires "
                    "credentialSubject. Synthesising an empty subject."
                ),
                step="M02",
            )
        )
        untp["credentialSubject"] = {}
        return

    subject: dict[str, Any] = {"type": ["Product"]}

    # M03 — productIdentifier → id + idScheme
    pid = product.get("productIdentifier") or {}
    pid_value = pid.get("value") if isinstance(pid, dict) else None
    pid_scheme = pid.get("scheme") if isinstance(pid, dict) else None
    pid_scheme_name = pid.get("schemeName") if isinstance(pid, dict) else None
    if pid_scheme and pid_scheme in identifier_scheme_lookup:
        scheme_id, scheme_name = identifier_scheme_lookup[pid_scheme]
        mapping = None
    else:
        scheme_id, scheme_name, mapping = _id_scheme_to_untp(pid_scheme or "", pid_scheme_name)
    subject["id"] = pid_value or ""
    subject["idScheme"] = {"id": scheme_id, "name": scheme_name}
    if pid_scheme and mapping is None:
        warnings.append(
            MappingWarning.unmapped(
                path="$.product.productIdentifier.scheme",
                message=(
                    f"CIRPASS scheme {pid_scheme!r} is not in the bundled "
                    "lookup; passing through verbatim."
                ),
                step="M03",
                scheme=pid_scheme,
            )
        )

    # M05 — productName[] → scalar name
    name_list = product.get("productName")
    name, dropped_languages = _pick_localised(name_list, default_language)
    subject["name"] = name or ""
    for lang in dropped_languages:
        warnings.append(
            MappingWarning.lossy(
                path="$.credentialSubject.name",
                message=(
                    f"Dropped CIRPASS productName entry with language="
                    f"{lang!r} when projecting onto UNTP scalar name "
                    "(UNTP 0.7.0 has no envelope-level multilingual "
                    "structure for product name)."
                ),
                step="M05",
                language=lang,
            )
        )

    # M06 — description[] → scalar
    desc_list = product.get("description")
    desc, dropped_desc_langs = _pick_localised(desc_list, default_language)
    if desc:
        subject["description"] = desc
    for lang in dropped_desc_langs:
        warnings.append(
            MappingWarning.lossy(
                path="$.credentialSubject.description",
                message=(
                    f"Dropped CIRPASS description entry with language="
                    f"{lang!r} when projecting onto UNTP scalar string."
                ),
                step="M06",
                language=lang,
            )
        )

    # M09 — commodityCode[] → productCategory[]
    commodity = product.get("commodityCode")
    if isinstance(commodity, list) and commodity:
        categories: list[dict[str, Any]] = []
        for i, cc in enumerate(commodity):
            if not isinstance(cc, dict):
                continue
            scheme_uri = cc.get("scheme") or ""
            cls_scheme_id, cls_scheme_name, _ = _id_scheme_to_untp(scheme_uri, None)
            label_list = cc.get("name")
            label, dropped_label_langs = _pick_localised(label_list, default_language)
            if not label:
                # UNTP Classification.name is required; synthesise a
                # placeholder from the code.
                label = cc.get("code") or "(unknown)"
                warnings.append(
                    MappingWarning.synthesised(
                        path=f"$.credentialSubject.productCategory[{i}].name",
                        message=(
                            "CIRPASS commodityCode entry has no name[]; "
                            "synthesised UNTP Classification.name from "
                            "the code."
                        ),
                        step="M09",
                    )
                )
            for lang in dropped_label_langs:
                warnings.append(
                    MappingWarning.lossy(
                        path=f"$.credentialSubject.productCategory[{i}].name",
                        message=(
                            f"Dropped commodityCode name entry with "
                            f"language={lang!r} during UNTP projection."
                        ),
                        step="M09",
                        language=lang,
                    )
                )
            categories.append(
                {
                    "schemeId": scheme_uri,
                    "schemeName": cls_scheme_name,
                    "code": cc.get("code") or "",
                    "name": label,
                }
            )
        if categories:
            subject["productCategory"] = categories

    # UNTP requires productCategory ≥ 1; synthesise a placeholder when
    # CIRPASS carries no commodityCode. Unspecified is the safest
    # fallback — downstream consumers can detect the placeholder via
    # the ``ZZ-unspecified`` code value.
    if "productCategory" not in subject:
        subject["productCategory"] = [
            {
                "schemeId": "https://w3id.org/eudpp#CommodityCode",
                "schemeName": "EUDPP CommodityCode",
                "code": "unspecified",
                "name": "Unspecified",
            }
        ]
        warnings.append(
            MappingWarning.synthesised(
                path="$.credentialSubject.productCategory",
                message=(
                    "CIRPASS payload has no commodityCode; UNTP requires "
                    "productCategory ≥ 1. Synthesised an unspecified "
                    "placeholder Classification."
                ),
                step="M09",
            )
        )

    # M02 fields the UNTP schema requires but CIRPASS doesn't carry
    # (idGranularity, producedAtFacility, countryOfProduction). The
    # caller can override countryOfProduction via the manufacturer's
    # actor address; we synthesise sensible defaults.
    subject["idGranularity"] = untp_id_granularity
    if "producedAtFacility" not in subject:
        subject["producedAtFacility"] = {
            "id": "https://example.com/facility/unspecified",
            "type": ["Facility"],
            "name": "Unspecified Facility",
        }
        warnings.append(
            MappingWarning.synthesised(
                path="$.credentialSubject.producedAtFacility",
                message=(
                    "UNTP requires producedAtFacility but CIRPASS does "
                    "not carry an equivalent root-level field; "
                    "synthesised a placeholder facility."
                ),
                step="M02",
            )
        )
    if "countryOfProduction" not in subject:
        # Best-effort: the first material's originCountry.
        composition = source.get("composition") or {}
        materials = composition.get("materials") if isinstance(composition, dict) else None
        first_country: str | None = None
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict) and m.get("originCountry"):
                    first_country = m["originCountry"]
                    break
        if first_country:
            country_obj: dict[str, Any] = {"countryCode": first_country}
            if first_country in country_lookup:
                country_obj["countryName"] = country_lookup[first_country]
            subject["countryOfProduction"] = country_obj
        else:
            subject["countryOfProduction"] = {"countryCode": "ZZ"}
            warnings.append(
                MappingWarning.synthesised(
                    path="$.credentialSubject.countryOfProduction",
                    message=(
                        "UNTP requires countryOfProduction; CIRPASS "
                        "carries no root-level country. Synthesised "
                        "ISO ``ZZ`` (unknown) — the caller should "
                        "supply a real country."
                    ),
                    step="M02",
                )
            )

    # M10 — composition.materials[] → materialProvenance[]
    composition = source.get("composition") or {}
    materials = composition.get("materials") if isinstance(composition, dict) else None
    if isinstance(materials, list) and materials:
        provenance = []
        for i, m in enumerate(materials):
            if not isinstance(m, dict):
                continue
            mname_list = m.get("materialName")
            mname, dropped_mname_langs = _pick_localised(mname_list, default_language)
            for lang in dropped_mname_langs:
                warnings.append(
                    MappingWarning.lossy(
                        path=f"$.credentialSubject.materialProvenance[{i}].name",
                        message=(
                            f"Dropped material name entry with language="
                            f"{lang!r} during UNTP projection."
                        ),
                        step="M10",
                        language=lang,
                    )
                )
            country_code = m.get("originCountry")
            country_obj: dict[str, Any] | None = None
            if country_code:
                country_obj = {"countryCode": country_code}
                if country_code in country_lookup:
                    country_obj["countryName"] = country_lookup[country_code]
            material_type_code = m.get("materialType")
            material_type_obj: dict[str, Any] | None = None
            if material_type_code:
                # CIRPASS bare ISO 2076 code → UNTP Classification.
                # The scheme URI is synthesised; consumers can swap in
                # a more-specific scheme via Phase 6's CLI override.
                material_type_obj = {
                    "schemeId": "https://w3id.org/eudpp#MaterialType",
                    "schemeName": "ISO 2076 / EUDPP MaterialType",
                    "code": material_type_code,
                    "name": material_type_code,
                }
            mass_fraction = m.get("massFraction")
            entry: dict[str, Any] = {"name": mname or ""}
            if country_obj is not None:
                entry["originCountry"] = country_obj
            else:
                # UNTP Material requires originCountry; synthesise.
                entry["originCountry"] = {"countryCode": "ZZ"}
                warnings.append(
                    MappingWarning.synthesised(
                        path=(f"$.credentialSubject.materialProvenance[{i}].originCountry"),
                        message=(
                            "CIRPASS material has no originCountry; "
                            "synthesised ISO ``ZZ`` (unknown)."
                        ),
                        step="M10",
                    )
                )
            if material_type_obj is not None:
                entry["materialType"] = material_type_obj
            else:
                # UNTP requires materialType; synthesise a minimal
                # placeholder Classification.
                entry["materialType"] = {
                    "schemeId": "https://w3id.org/eudpp#MaterialType",
                    "schemeName": "ISO 2076 / EUDPP MaterialType",
                    "code": "unspecified",
                    "name": "Unspecified",
                }
                warnings.append(
                    MappingWarning.synthesised(
                        path=(f"$.credentialSubject.materialProvenance[{i}].materialType"),
                        message=(
                            "CIRPASS material has no materialType; synthesised an UNTP placeholder."
                        ),
                        step="M10",
                    )
                )
            if mass_fraction is not None:
                entry["massFraction"] = float(mass_fraction)
            else:
                # UNTP requires massFraction; synthesise zero (the
                # validator will mark it as incomplete via SEM001).
                entry["massFraction"] = 0.0
                warnings.append(
                    MappingWarning.synthesised(
                        path=(f"$.credentialSubject.materialProvenance[{i}].massFraction"),
                        message=(
                            "CIRPASS material has no massFraction; UNTP "
                            "requires it. Synthesised 0.0 (caller must "
                            "supply real values)."
                        ),
                        step="M10",
                    )
                )
            if m.get("isRecycled"):
                # UNTP carries recycledMassFraction (a number); CIRPASS
                # carries a boolean. The semantic mapping is "100% of
                # this material's mass is recycled" — emit massFraction.
                entry["recycledMassFraction"] = float(mass_fraction or 1.0)
            provenance.append(entry)
        if provenance:
            subject["materialProvenance"] = provenance

    untp["credentialSubject"] = subject


def _step_temporal(
    source: dict[str, Any],
    untp: dict[str, Any],
    warnings: list[MappingWarning],
) -> None:
    """M07 + M08 — CIRPASS temporal → UNTP envelope.validFrom / validUntil."""
    issued_at = source.get("issuedAt") or {}
    issued_ts = issued_at.get("timestamp") if isinstance(issued_at, dict) else None
    period = source.get("effectivePeriod") or {}
    start = period.get("start") if isinstance(period, dict) else None
    end = period.get("end") if isinstance(period, dict) else None
    valid_from = start or issued_ts
    if not valid_from:
        warnings.append(
            MappingWarning.required_missing(
                path="$.validFrom",
                message=(
                    "CIRPASS issuedAt.timestamp and effectivePeriod.start "
                    "are both missing; UNTP requires validFrom. Output "
                    "validFrom is empty."
                ),
                step="M07",
            )
        )
        valid_from = ""
    untp["validFrom"] = _normalise_iso8601(valid_from) if valid_from else ""
    if end:
        untp["validUntil"] = _normalise_iso8601(end)


def _step_actors(
    source: dict[str, Any],
    untp: dict[str, Any],
    warnings: list[MappingWarning],
    *,
    default_language: str,
    issuer_did: str,
    issuer_name: str,
) -> None:
    """M11 + M12 — CIRPASS relatedActors[] → UNTP relatedParty[] + issuer."""
    actors = source.get("relatedActors")
    if not isinstance(actors, list):
        actors = []
    related_party: list[dict[str, Any]] = []
    issuer: dict[str, Any] | None = None

    for i, ar in enumerate(actors):
        if not isinstance(ar, dict):
            continue
        actor = ar.get("actor")
        role = ar.get("role")
        if not isinstance(actor, dict):
            continue
        party = _project_party(actor, default_language)
        untp_role = _EUDPP_TO_UNTP_ROLE.get(role or "")
        if untp_role is None:
            untp_role = "manufacturer"
            warnings.append(
                MappingWarning.synthesised(
                    path=f"$.credentialSubject.relatedParty[{i}].role",
                    message=(
                        f"CIRPASS role {role!r} has no canonical UNTP "
                        "PartyRole; falling back to ``manufacturer``."
                    ),
                    step="M11",
                    original_role=str(role),
                )
            )
        # First manufacturer role becomes the envelope issuer
        # (matches the M12 forward-shim invariant: forward synthesises
        # a manufacturer from the issuer when relatedParty has none).
        if untp_role == "manufacturer" and issuer is None:
            issuer = {
                "id": party["id"] or issuer_did,
                "name": party["name"] or issuer_name,
                "type": ["CredentialIssuer"],
            }
        related_party.append({"role": untp_role, "party": party})

    subject = untp.get("credentialSubject")
    if isinstance(subject, dict) and related_party:
        subject["relatedParty"] = related_party

    if issuer is None:
        # Synthesise an issuer from the first actor entry (or a fully
        # placeholder when there are no actors at all).
        if related_party:
            first = related_party[0]["party"]
            issuer = {
                "id": first.get("id") or issuer_did,
                "name": first.get("name") or issuer_name,
                "type": ["CredentialIssuer"],
            }
            warnings.append(
                MappingWarning.synthesised(
                    path="$.issuer",
                    message=(
                        "No CIRPASS actor with ManufacturerRole; UNTP "
                        "envelope.issuer synthesised from the first "
                        "related-actor entry."
                    ),
                    step="M12",
                )
            )
        else:
            issuer = {
                "id": issuer_did,
                "name": issuer_name,
                "type": ["CredentialIssuer"],
            }
            warnings.append(
                MappingWarning.synthesised(
                    path="$.issuer",
                    message=(
                        "CIRPASS payload carried no related actors; UNTP "
                        f"envelope.issuer synthesised from caller-"
                        f"supplied issuer_did={issuer_did!r} / "
                        f"issuer_name={issuer_name!r}."
                    ),
                    step="M12",
                )
            )
    untp["issuer"] = issuer


def _project_party(actor: dict[str, Any], default_language: str) -> dict[str, Any]:
    """Lift a CIRPASS Actor onto a UNTP Party."""
    identifier = actor.get("actorIdentifier") or {}
    actor_id = identifier.get("value") if isinstance(identifier, dict) else None
    scheme_uri = identifier.get("scheme") if isinstance(identifier, dict) else None
    scheme_name = identifier.get("schemeName") if isinstance(identifier, dict) else None
    untp_scheme_id, untp_scheme_name, _ = _id_scheme_to_untp(scheme_uri or "", scheme_name)
    name_list = actor.get("actorName")
    name, _ = _pick_localised(name_list, default_language)
    party: dict[str, Any] = {
        "id": actor_id or "",
        "name": name or "",
        "type": ["Party"],
        "idScheme": {"id": untp_scheme_id, "name": untp_scheme_name},
    }
    return party


def _step_drop_unmappable(
    source: dict[str, Any],
    untp: dict[str, Any],  # noqa: ARG001 — symmetry with the other step helpers
    warnings: list[MappingWarning],
) -> None:
    """M13 + M14 + M15 — drop CIRPASS-only fields with MAP001."""
    if source.get("substancesOfConcern"):
        warnings.append(
            MappingWarning.lossy(
                path="$.credentialSubject.materialProvenance",
                message=(
                    f"CIRPASS substancesOfConcern (count="
                    f"{len(source['substancesOfConcern'])}) has no UNTP "
                    "0.7.0 base equivalent; dropped during reverse mapping."
                ),
                step="M14",
            )
        )
    if source.get("connectorRelations"):
        warnings.append(
            MappingWarning.lossy(
                path="(no target field)",
                message=(
                    f"CIRPASS connectorRelations (count="
                    f"{len(source['connectorRelations'])}) is a CIRPASS-"
                    "only construct; dropped during reverse mapping."
                ),
                step="M15",
            )
        )
    if source.get("lca"):
        results = source["lca"].get("results") if isinstance(source["lca"], dict) else None
        count = len(results) if isinstance(results, list) else 0
        warnings.append(
            MappingWarning.lossy(
                path="$.credentialSubject.performanceClaim",
                message=(
                    f"CIRPASS LifeCycleAssessment (results="
                    f"{count}) is dropped during reverse mapping. Phase 7 "
                    "pilot lifts cover the supported subset."
                ),
                step="M13",
            )
        )


# =============================================================================
# Helpers
# =============================================================================
#
# Cross-shim helpers (``_pick_localised``, ``_normalise_iso8601``) live at
# :mod:`dppvalidator.compat._shared` so the forward / reverse shims stay
# symmetric.


__all__ = [
    "to_untp_0_7",
]
