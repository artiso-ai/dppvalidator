"""EU DPP Core Ontology alignment and namespace mapping.

Provides term mappings between UNTP vocabulary and the official EU DPP Core
Ontology from CIRPASS-2.

Source: EU DPP Core Ontology v1.7.1 (Product and DPP module)
Namespace: http://dpp.taltech.ee/EUDPP#
DOI: 10.5281/zenodo.15270342
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class EUDPPNamespace(str, Enum):
    """EU DPP Core Ontology and related namespaces.

    Based on official CIRPASS-2 ontology v1.7.1.
    """

    # Official EU DPP Core Ontology namespace (TalTech)
    EUDPP = "http://dpp.taltech.ee/EUDPP#"

    # LCA module namespace (CEA France) - different origin
    LCA = "http://dpp.cea.fr/EUDPP/LCA#"

    # SI Digital Framework (measurement units)
    SI = "https://si-digital-framework.org/SI#"

    # QUDT Quantities, Units, Dimensions and Types
    QUDT = "http://qudt.org/schema/qudt#"

    # W3C SHACL namespace
    SH = "http://www.w3.org/ns/shacl#"

    # EU DPP Vocabulary Hub
    DPP_HUB = "https://dpp.vocabulary-hub.eu/"

    # W3C Verifiable Credentials v2
    VC2 = "https://www.w3.org/ns/credentials/v2"

    # UNTP DPP vocabulary
    UNTP_DPP = "https://test.uncefact.org/vocabulary/untp/dpp/"

    # Schema.org
    SCHEMA = "https://schema.org/"

    # GS1 vocabulary
    GS1 = "https://gs1.org/voc/"


# Backward compatibility alias
CIRPASSNamespace = EUDPPNamespace


class DPPStatus(str, Enum):
    """DPP instance status per EU DPP Core Ontology.

    The status of the DPP instance as a digital resource.
    """

    ACTIVE = "Active"
    ARCHIVED = "Archived"


class DPPGranularity(str, Enum):
    """DPP granularity level per ESPR and SR5423.

    The level of granularity of the ProductID as per ESPR.
    Values from official EU DPP Core Ontology.
    """

    MODEL = "model"  # All units of a product version
    BATCH = "batch"  # Subset from specific plant/time
    PRODUCT = "product"  # Single unit (official term, not 'item')


# Sentinel that signals "this term has no equivalent in the given UNTP version"
# (e.g. v0.6's ``gtin`` field is gone in v0.7 — encoded as ``Product.id`` plus
# ``idScheme`` on a GS1 scheme). Using a sentinel rather than ``None`` keeps
# the dataclass slots type-clean (``str``) and makes "intentionally absent"
# explicit when reading the table.
TERM_REMOVED: str = "<removed-in-this-version>"


@dataclass(frozen=True, slots=True)
class TermMapping:
    """Mapping between UNTP term(s) and a CIRPASS / EU DPP ontology URI.

    Phase 3c of docs/plans/UNTP_0.7.0_MIGRATION.md added per-version columns
    so a single mapping row can carry both UNTP v0.6.x and v0.7.x term
    names without duplicating the ESPR reference and description.

    Attributes:
        untp_term: The "canonical" UNTP term — historically the v0.6 field
            name, kept as the row's primary key so backward-compat callers
            and existing tests continue to work without modification.
        cirpass_uri: EU DPP Core Ontology URI in compact form
            (e.g. ``eudpp:Product``).
        description: Human-readable summary of the mapping.
        espr_reference: ESPR / SR5423 / ISO citation for traceability.
        untp_v0_6: The term spelling used by UNTP 0.6.x. Defaults to
            :attr:`untp_term` so unchanged rows don't need to repeat themselves.
        untp_v0_7: The term spelling used by UNTP 0.7.0. Defaults to
            :attr:`untp_term` (i.e. unchanged across versions). Set
            explicitly for renames, or to :data:`TERM_REMOVED` for fields
            that no longer exist in v0.7 (e.g. ``gtin``).
    """

    untp_term: str
    cirpass_uri: str
    description: str
    espr_reference: str | None = None
    untp_v0_6: str | None = None
    untp_v0_7: str | None = None

    def term_for(self, version: str) -> str | None:
        """Return the UNTP term for a given version, or ``None`` if removed.

        Resolution rules (in order):

        1. If a per-version column is set explicitly, use it.
        2. Otherwise fall back to :attr:`untp_term` (the canonical v0.6 spelling).
        3. If the per-version column is :data:`TERM_REMOVED`, return ``None``
           — the field has no equivalent in this UNTP version.

        Unknown version strings (anything that's not a 0.6.x / 0.7.x prefix)
        fall back to :attr:`untp_term` so the table is forward-compatible.
        """
        explicit: str | None
        if version.startswith("0.6"):
            explicit = self.untp_v0_6
        elif version.startswith("0.7"):
            explicit = self.untp_v0_7
        else:
            explicit = None

        chosen = explicit if explicit is not None else self.untp_term
        return None if chosen == TERM_REMOVED else chosen


# Term mappings from UNTP to EU DPP Core Ontology
# Based on official CIRPASS-2 ontology v1.7.1
#
# Mapping rows are written so the row's primary ``untp_term`` is the v0.6
# spelling — this keeps the OntologyMapper's existing semantics. Rows that
# rename in v0.7 carry an explicit ``untp_v0_7`` column. Rows that remove
# in v0.7 use :data:`TERM_REMOVED`. See Phase 3c of
# docs/plans/UNTP_0.7.0_MIGRATION.md.
TERM_MAPPINGS: tuple[TermMapping, ...] = (
    # Core DPP and Product classes (unchanged across versions).
    TermMapping(
        untp_term="DigitalProductPassport",
        cirpass_uri="eudpp:DPP",
        description="Digital Product Passport",
        espr_reference="ESPR Art 2(28)",
    ),
    TermMapping(
        untp_term="Product",
        cirpass_uri="eudpp:Product",
        description="Physical product placed on market",
        espr_reference="ESPR Art 2(1)",
    ),
    # Product identification
    TermMapping(
        untp_term="id",
        cirpass_uri="eudpp:uniqueDPPID",
        description="Unique DPP identifier (URI)",
        espr_reference="ESPR Art 9(1)",
    ),
    # ``serialNumber`` (v0.6) → ``itemNumber`` (v0.7); same EU DPP target.
    TermMapping(
        untp_term="serialNumber",
        cirpass_uri="eudpp:uniqueProductID",
        description="Unique product identifier (item-level)",
        espr_reference="ESPR Art 2(30)",
        untp_v0_7="itemNumber",
    ),
    TermMapping(
        untp_term="name",
        cirpass_uri="eudpp:productName",
        description="Product name",
        espr_reference="ESPR Annex III",
    ),
    TermMapping(
        untp_term="description",
        cirpass_uri="eudpp:description",
        description="Product description",
        espr_reference="ESPR Annex III",
    ),
    TermMapping(
        untp_term="productImage",
        cirpass_uri="eudpp:productImage",
        description="Product image URI",
        espr_reference="ESPR Annex III",
    ),
    # ``gtin`` is removed in v0.7. v0.7 encodes GS1 GTINs by combining
    # ``Product.id`` with an ``idScheme`` whose URI points at the GS1
    # register — so there's no single field to re-map onto eudpp:GTIN.
    TermMapping(
        untp_term="gtin",
        cirpass_uri="eudpp:GTIN",
        description="Global Trade Identification Number",
        espr_reference="ISO/IEC 15459-6",
        untp_v0_7=TERM_REMOVED,
    ),
    TermMapping(
        untp_term="productCategory",
        cirpass_uri="eudpp:commodityCode",
        description="TARIC or commodity code",
        espr_reference="Council Regulation (EEC) No 2658/87",
    ),
    # Actor identification
    TermMapping(
        untp_term="issuer",
        cirpass_uri="eudpp:hasIssuer",
        description="DPP issuer (economic operator)",
        espr_reference="ESPR Annex III (g)",
    ),
    # ``producedByParty: Party`` (v0.6) → ``relatedParty: list[PartyRole]``
    # (v0.7). The v0.7 field is structurally different (typed list of
    # role/party pairs) but the EU DPP target ``hasManufacturer`` is the
    # same when the role is "manufacturer" — the exporter handles the
    # role filtering separately.
    TermMapping(
        untp_term="producedByParty",
        cirpass_uri="eudpp:hasManufacturer",
        description="Product manufacturer",
        espr_reference="ESPR Annex III (g)",
        untp_v0_7="relatedParty",
    ),
    TermMapping(
        untp_term="producedAtFacility",
        cirpass_uri="eudpp:facilityID",
        description="Unique facility identifier",
        espr_reference="ESPR Art 2(33)",
    ),
    # Substances of concern
    TermMapping(
        untp_term="hazardous",
        cirpass_uri="eudpp:containsSubstanceOfConcern",
        description="Product contains substance of concern",
        espr_reference="ESPR Art 7(5)",
    ),
    # Validity and lifecycle (envelope-level fields — same in both versions).
    TermMapping(
        untp_term="validFrom",
        cirpass_uri="eudpp:validFrom",
        description="DPP valid from date",
        espr_reference="ESPR Art 9(2i)",
    ),
    TermMapping(
        untp_term="validUntil",
        cirpass_uri="eudpp:validUntil",
        description="DPP valid until date",
        espr_reference="ESPR Art 9(2i)",
    ),
    TermMapping(
        untp_term="lastUpdate",
        cirpass_uri="eudpp:lastUpdate",
        description="Last DPP update timestamp",
        espr_reference="ESPR Art 11",
    ),
    TermMapping(
        untp_term="schemaVersion",
        cirpass_uri="eudpp:schemaVersion",
        description="Reference standard version",
        espr_reference="ESPR Art 9",
    ),
    TermMapping(
        untp_term="previousDPP",
        cirpass_uri="eudpp:linkToPreviousDPP",
        description="Link to previous DPP",
        espr_reference="ESPR Art 11(d)",
    ),
    # Granularity: ``granularityLevel`` (v0.6) → ``idGranularity`` (v0.7).
    TermMapping(
        untp_term="granularityLevel",
        cirpass_uri="eudpp:granularity",
        description="DPP granularity (model/batch/product)",
        espr_reference="SR5423 Annex II Part B 1.1",
        untp_v0_7="idGranularity",
    ),
    # Product properties
    TermMapping(
        untp_term="characteristics",
        cirpass_uri="eudpp:hasProperty",
        description="Product property",
        espr_reference="ESPR Annex I",
    ),
    TermMapping(
        untp_term="isEnergyRelated",
        cirpass_uri="eudpp:isEnergyRelated",
        description="Energy-related product indicator",
        espr_reference="ESPR Art 2(4)",
    ),
    # Product relations
    TermMapping(
        untp_term="isComponentOf",
        cirpass_uri="eudpp:isComponentOf",
        description="Product is component of another",
        espr_reference="ESPR Art 2",
    ),
    TermMapping(
        untp_term="isSparePartOf",
        cirpass_uri="eudpp:isSparePartOf",
        description="Product is spare part of another",
        espr_reference="ESPR Art 2",
    ),
    # ---- v0.7-only mappings ----------------------------------------------
    # ``materialsProvenance`` (v0.6) → ``materialProvenance`` (v0.7,
    # singular noun). Both spellings need to map to the same EU DPP
    # predicate — we add a row whose canonical ``untp_term`` is the v0.6
    # name and whose v0.7 column carries the new spelling.
    TermMapping(
        untp_term="materialsProvenance",
        cirpass_uri="eudpp:hasMaterialProvenance",
        description="Material origin and mass-fraction information",
        espr_reference="ESPR Art 7(5)",
        untp_v0_7="materialProvenance",
    ),
    # ``conformityClaim`` (v0.6) collapses with the three scorecard
    # classes into ``performanceClaim`` (v0.7). For ontology-mapping
    # purposes both target the EU DPP performance/claim predicate.
    TermMapping(
        untp_term="conformityClaim",
        cirpass_uri="eudpp:hasPerformanceClaim",
        description="Performance / conformity claim attached to a product",
        espr_reference="ESPR Annex III",
        untp_v0_7="performanceClaim",
    ),
)


class OntologyMapper:
    """Maps UNTP terms to CIRPASS / EU DPP ontology URIs.

    Phase 3c added per-version awareness: callers that pass a UNTP
    ``schema_version`` get the right column out of :data:`TERM_MAPPINGS`.
    Callers that don't (the pre-Phase-3c API) keep the v0.6 behaviour —
    the ``untp_term`` column remains the canonical key, so existing
    forward and reverse lookups work unchanged.
    """

    def __init__(self) -> None:
        """Initialize mapper with term mappings."""
        # Forward lookup is keyed on the row's canonical ``untp_term``
        # (v0.6 spelling). v0.7-specific spellings are reachable via
        # ``find_mapping_for_term(term, version)``.
        self._untp_to_cirpass: dict[str, TermMapping] = {m.untp_term: m for m in TERM_MAPPINGS}
        self._cirpass_to_untp: dict[str, TermMapping] = {m.cirpass_uri: m for m in TERM_MAPPINGS}

        # Per-version forward index — populated lazily when needed via
        # :meth:`_index_for_version`. Keys are e.g. ``"itemNumber"`` for
        # v0.7 lookups.
        self._index_cache: dict[str, dict[str, TermMapping]] = {}

        # Secondary index of every non-canonical, non-removed term spelling
        # across all per-version columns (e.g. ``itemNumber`` for v0.7).
        # This lets ``get_mapping`` and the no-version
        # ``find_mapping_for_term`` resolve renamed-only terms without
        # branching on a specific UNTP version literal.
        secondary: dict[str, TermMapping] = {}
        for mapping in TERM_MAPPINGS:
            for alt in (mapping.untp_v0_6, mapping.untp_v0_7):
                if alt is None or alt == TERM_REMOVED:
                    continue
                if alt == mapping.untp_term:
                    continue
                # Last write wins on collision, matching the per-version
                # index behaviour below.
                secondary[alt] = mapping
        self._secondary_index: dict[str, TermMapping] = secondary

    def to_cirpass(self, untp_term: str) -> str | None:
        """Get CIRPASS URI for a UNTP term.

        Args:
            untp_term: UNTP vocabulary term (canonical / v0.6 spelling).

        Returns:
            CIRPASS ontology URI or None if not mapped
        """
        mapping = self._untp_to_cirpass.get(untp_term)
        return mapping.cirpass_uri if mapping else None

    def to_untp(self, cirpass_uri: str, version: str | None = None) -> str | None:
        """Get UNTP term for a CIRPASS URI, optionally version-aware.

        Args:
            cirpass_uri: CIRPASS ontology URI
            version: UNTP version SemVer string (e.g. for v0.7.0). If
                supplied, the returned term reflects the spelling that
                version uses (e.g. ``itemNumber`` for v0.7 instead of
                ``serialNumber``). If the term is removed in that version,
                returns ``None``. When ``version`` is ``None`` the canonical
                (v0.6) spelling is returned — pre-Phase-3c behaviour.

        Returns:
            UNTP term or None if not mapped (or removed in this version).
        """
        mapping = self._cirpass_to_untp.get(cirpass_uri)
        if mapping is None:
            return None
        if version is None:
            return mapping.untp_term
        return mapping.term_for(version)

    def get_mapping(self, term: str) -> TermMapping | None:
        """Get full mapping for a term (UNTP or CIRPASS).

        Recognises the canonical (v0.6) spelling, every per-version
        spelling registered in :data:`TERM_MAPPINGS`, and the EU DPP URI
        as keys. Returns ``None`` if no row matches.
        """
        return (
            self._untp_to_cirpass.get(term)
            or self._cirpass_to_untp.get(term)
            or self._secondary_index.get(term)
        )

    def get_espr_reference(self, untp_term: str) -> str | None:
        """Get ESPR reference for a UNTP term."""
        mapping = self._untp_to_cirpass.get(untp_term)
        return mapping.espr_reference if mapping else None

    def iter_mappings(self) -> Iterator[TermMapping]:
        """Iterate over all term mappings."""
        yield from TERM_MAPPINGS

    def find_mapping_for_term(self, term: str, version: str | None = None) -> TermMapping | None:
        """Look up a mapping by the version-specific spelling of a term.

        Phase 3c helper: callers that observe a v0.7 field name on the wire
        (e.g. ``itemNumber`` or ``materialProvenance``) can resolve it to
        the same :class:`TermMapping` row as the v0.6 spelling. When
        ``version`` is ``None`` the canonical-key index is consulted first
        and the secondary index of all per-version spellings is used as
        a fallback.
        """
        if version is None:
            return self._untp_to_cirpass.get(term) or self._secondary_index.get(term)
        return self._index_for_version(version).get(term)

    def _index_for_version(self, version: str) -> dict[str, TermMapping]:
        """Build (and cache) the version-keyed forward index."""
        cached = self._index_cache.get(version)
        if cached is not None:
            return cached
        index: dict[str, TermMapping] = {}
        for mapping in TERM_MAPPINGS:
            term = mapping.term_for(version)
            if term is None:
                continue
            # Last write wins on collision — rows ordered later in
            # TERM_MAPPINGS take precedence, which matches Python dict
            # initialisation semantics elsewhere in this module.
            index[term] = mapping
        self._index_cache[version] = index
        return index

    @property
    def mapped_terms(self) -> list[str]:
        """List of all mapped UNTP terms (v0.6 canonical spellings)."""
        return list(self._untp_to_cirpass.keys())

    def mapped_terms_for(self, version: str) -> list[str]:
        """List of UNTP terms for a specific version (Phase 3c)."""
        return list(self._index_for_version(version).keys())

    @property
    def mapping_count(self) -> int:
        """Number of term mappings."""
        return len(TERM_MAPPINGS)


def get_eudpp_context() -> dict[str, str]:
    """Get JSON-LD context with EU DPP Core Ontology namespace prefixes.

    Returns:
        Dictionary of namespace prefixes for JSON-LD @context
    """
    return {
        "eudpp": EUDPPNamespace.EUDPP.value,
        "lca": EUDPPNamespace.LCA.value,
        "si": EUDPPNamespace.SI.value,
        "qudt": EUDPPNamespace.QUDT.value,
        "sh": EUDPPNamespace.SH.value,
        "dpp": EUDPPNamespace.DPP_HUB.value,
        "untp": EUDPPNamespace.UNTP_DPP.value,
        "schema": EUDPPNamespace.SCHEMA.value,
        "gs1": EUDPPNamespace.GS1.value,
    }


# Backward compatibility alias
def get_cirpass_context() -> dict[str, str]:
    """Deprecated: Use get_eudpp_context instead."""
    return get_eudpp_context()


def expand_eudpp_uri(compact_uri: str) -> str:
    """Expand a compact EU DPP URI to full form.

    Args:
        compact_uri: URI like "eudpp:Product"

    Returns:
        Full URI like "http://dpp.taltech.ee/EUDPP#Product"
    """
    if ":" not in compact_uri:
        return compact_uri

    prefix, local = compact_uri.split(":", 1)
    namespaces = {ns.name.lower(): ns.value for ns in EUDPPNamespace}

    base = namespaces.get(prefix.lower())
    if base:
        return f"{base}{local}"

    return compact_uri


def compact_eudpp_uri(full_uri: str) -> str:
    """Compact a full EU DPP URI to prefixed form.

    Args:
        full_uri: Full URI

    Returns:
        Compact URI with namespace prefix
    """
    for ns in EUDPPNamespace:
        if full_uri.startswith(ns.value):
            local = full_uri[len(ns.value) :]
            return f"{ns.name.lower()}:{local}"

    return full_uri


# Backward compatibility aliases
def expand_cirpass_uri(compact_uri: str) -> str:
    """Deprecated: Use expand_eudpp_uri instead."""
    return expand_eudpp_uri(compact_uri)


def compact_cirpass_uri(full_uri: str) -> str:
    """Deprecated: Use compact_eudpp_uri instead."""
    return compact_eudpp_uri(full_uri)
