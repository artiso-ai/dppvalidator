"""EU DPP-aligned JSON-LD export for Digital Product Passports.

Provides optional EU DPP-aligned JSON-LD output that transforms UNTP
models to the EU DPP Core Ontology vocabulary. The UNTP models remain
unchanged; this export layer performs vocabulary mapping at export time.

Source: EU DPP Core Ontology v1.9.1 (Phase 1 CIRPASS-2 target). Emits
predicate IRIs under the canonical ``https://w3id.org/eudpp#`` W3ID
prefix (rebased from per-publisher hosts in Phase 1 — see ADR 0002).
"""

from __future__ import annotations

import json
import warnings
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION, SCHEMA_REGISTRY
from dppvalidator.vocabularies.ontology import (
    TERM_MAPPINGS,
    EUDPPNamespace,
    OntologyMapper,
    get_eudpp_context,
)

if TYPE_CHECKING:
    from dppvalidator.models.passport import DigitalProductPassport

logger = get_logger(__name__)


# =============================================================================
# EU DPP Context Definitions
# =============================================================================


# Canonical v1.9.1 namespace IRI for EU DPP terms — the W3ID-resolved
# fragment namespace declared by every bundled v1.9.x TTL. New code
# should reference this constant directly; the legacy
# :data:`EUDPP_CONTEXT_URL` remains as a deprecation-warned alias
# until Phase 10 of the migration plan.
EUDPP_CANONICAL_CONTEXT_URL = EUDPPNamespace.EUDPP.value  # https://w3id.org/eudpp#

# Legacy DPP Vocabulary Hub context URL. Phase 6 of the CIRPASS-2
# migration deprecates this in favour of the canonical W3ID URL
# above. Access goes through the module-level :func:`__getattr__`
# below so callers (including ``from … import EUDPP_CONTEXT_URL``)
# get a :class:`DeprecationWarning`. Removed in Phase 10.
_EUDPP_CONTEXT_URL_LEGACY = "https://dpp.vocabulary-hub.eu/context/v1"


def __getattr__(name: str) -> Any:
    """PEP 562 module-level attribute hook for deprecated names.

    Phase 6 task 6.2 of [docs/plans/CIRPASS_2_MIGRATION.md]. The
    legacy ``EUDPP_CONTEXT_URL`` constant resolves through here to a
    deprecation-warned value; consumers should switch to
    :data:`EUDPP_CANONICAL_CONTEXT_URL` (the canonical v1.9.1 W3ID
    fragment namespace).
    """
    if name == "EUDPP_CONTEXT_URL":
        warnings.warn(
            "exporters.eudpp_jsonld.EUDPP_CONTEXT_URL is deprecated; "
            "use EUDPP_CANONICAL_CONTEXT_URL "
            f"({EUDPP_CANONICAL_CONTEXT_URL!r}) — the canonical v1.9.1 "
            "W3ID fragment namespace. The legacy hub URL "
            f"({_EUDPP_CONTEXT_URL_LEGACY!r}) is kept resolvable "
            "through Phase 10 for back-compat.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _EUDPP_CONTEXT_URL_LEGACY
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def get_eudpp_jsonld_context() -> list[Any]:
    """Get the EU DPP JSON-LD @context array.

    Returns a context that includes:
    - W3C Verifiable Credentials v2
    - EU DPP Core Ontology namespaces
    - Term mappings for UNTP → EU DPP

    Returns:
        List of context definitions for JSON-LD @context
    """
    return [
        EUDPPNamespace.VC2.value,
        get_eudpp_context(),
    ]


# =============================================================================
# Term Mapping
# =============================================================================


class EUDPPTermMapper:
    """Map UNTP terms to EU DPP Core Ontology terms.

    Phase 3c of docs/plans/UNTP_0.7.0_MIGRATION.md added a ``schema_version``
    parameter so the mapper picks the right column out of
    :data:`TERM_MAPPINGS`. The default value (:data:`DEFAULT_SCHEMA_VERSION`)
    preserves the pre-Phase-3c behaviour for callers that don't pass an
    explicit version. Note: the dispatch is purely a forward-mapping concern
    — the EU DPP target URI is the same across UNTP versions; only the
    source-side spelling (e.g. ``itemNumber`` vs ``serialNumber``) shifts.

    Terms removed in a given version (carrying the :data:`TERM_REMOVED`
    sentinel for that column) are excluded from that version's mapper —
    e.g. ``gtin`` does not appear in a v0.7 mapper's index because v0.7
    has no ``gtin`` field on the wire.
    """

    def __init__(self, schema_version: str = DEFAULT_SCHEMA_VERSION) -> None:
        """Initialize term mapper.

        Args:
            schema_version: UNTP version whose source-side spellings to
                index. Defaults to :data:`DEFAULT_SCHEMA_VERSION` for
                backward compatibility with the Phase 3c-pre API.
        """
        self.schema_version = schema_version
        self._mapper = OntologyMapper()
        self._untp_to_eudpp: dict[str, str] = {}
        self._eudpp_to_untp: dict[str, str] = {}

        for mapping in TERM_MAPPINGS:
            term = mapping.term_for(schema_version)
            if term is None:
                # Skip rows whose ``untp_v0_X`` is TERM_REMOVED for this
                # version — there's no source-side spelling to map from.
                continue
            # Extract local name from compact URI (e.g. ``eudpp:Product`` →
            # ``Product``).
            eudpp_local = (
                mapping.cirpass_uri.split(":")[-1]
                if ":" in mapping.cirpass_uri
                else mapping.cirpass_uri
            )
            self._untp_to_eudpp[term] = eudpp_local
            # The reverse index is "last write wins" — multiple UNTP
            # spellings can resolve to the same eudpp_local across the
            # canonical and per-version columns; this matches the v0.6
            # default-mapper behaviour pre-Phase-3c.
            self._eudpp_to_untp[eudpp_local] = term

    def map_key(self, untp_key: str) -> str:
        """Map a UNTP key to EU DPP equivalent.

        Args:
            untp_key: UNTP vocabulary key

        Returns:
            EU DPP key (or original if no mapping exists)
        """
        return self._untp_to_eudpp.get(untp_key, untp_key)

    def map_type(self, untp_type: str) -> str:
        """Map a UNTP type to EU DPP equivalent.

        Args:
            untp_type: UNTP type name

        Returns:
            EU DPP type with namespace prefix
        """
        mapped = self._untp_to_eudpp.get(untp_type)
        if mapped:
            return f"eudpp:{mapped}"
        return untp_type

    def get_eudpp_key(self, untp_key: str) -> str | None:
        """Get EU DPP key for UNTP key if mapped.

        Args:
            untp_key: UNTP vocabulary key

        Returns:
            EU DPP key or None if not mapped
        """
        return self._untp_to_eudpp.get(untp_key)

    @property
    def mapped_keys(self) -> list[str]:
        """List of UNTP keys that have EU DPP mappings."""
        return list(self._untp_to_eudpp.keys())


# =============================================================================
# EU DPP JSON-LD Exporter
# =============================================================================


class EUDPPJsonLDExporter:
    """Export UNTP models as EU DPP-aligned JSON-LD.

    This exporter transforms UNTP DPP models to use EU DPP Core Ontology
    vocabulary while preserving the original data structure. The UNTP
    models remain unchanged; only the export representation uses EU DPP terms.

    Phase 3c of docs/plans/UNTP_0.7.0_MIGRATION.md added a
    ``schema_version`` argument so the exporter dispatches to the right
    column of :data:`TERM_MAPPINGS`. When omitted, it picks a sensible
    default by inspecting the source passport class — v0.7 passports get
    the v0.7 mapper, v0.6 passports get the v0.6 mapper. Callers that
    pin an explicit version override that auto-detection.

    Example:
        >>> exporter = EUDPPJsonLDExporter()
        >>> jsonld = exporter.export(passport)
        >>> # Result uses EU DPP vocabulary with @context

    Attributes:
        include_untp_context: Include UNTP context alongside EU DPP
        map_terms: Apply term mapping (UNTP → EU DPP)
        schema_version: UNTP source version. When ``None``, auto-detected
            from the passport's module path the first time
            :meth:`export_dict` is called.
    """

    def __init__(
        self,
        *,
        include_untp_context: bool = False,
        map_terms: bool = True,
        schema_version: str | None = None,
    ) -> None:
        """Initialize EU DPP exporter.

        Args:
            include_untp_context: Include UNTP context in output
            map_terms: Map UNTP terms to EU DPP equivalents
            schema_version: UNTP source version, e.g. v0.7.0 written as a
                SemVer string. When ``None``, the version is detected from
                the passport class at export time. Pass an explicit version
                when you need deterministic dispatch (e.g. when the exporter
                is reused across calls with mixed-version inputs).
        """
        self._include_untp = include_untp_context
        self._map_terms = map_terms
        self._explicit_version = schema_version
        # Cache of EUDPPTermMapper instances keyed on the resolved version.
        # We don't build a default mapper eagerly because the version may
        # only become known when ``export`` is called.
        self._term_mapper_cache: dict[str, EUDPPTermMapper] = {}
        # Eagerly populate the cache when the caller pinned a version.
        if schema_version is not None:
            self._term_mapper_cache[schema_version] = EUDPPTermMapper(
                schema_version=schema_version,
            )

    @property
    def schema_version(self) -> str | None:
        """Return the explicitly-configured version, or ``None`` for auto-detect."""
        return self._explicit_version

    @property
    def _term_mapper(self) -> EUDPPTermMapper:
        """Backward-compat alias.

        Pre-Phase-3c the exporter exposed a single ``self._term_mapper`` and
        external code (notably the existing test suite) reaches in to read
        it. Resolving on access keeps the lookup deterministic when the
        caller pinned ``schema_version`` and falls back to the global
        default otherwise.
        """
        version = self._explicit_version or DEFAULT_SCHEMA_VERSION
        return self._mapper_for(version)

    def _mapper_for(self, version: str) -> EUDPPTermMapper:
        """Return (and cache) the term mapper for ``version``."""
        cached = self._term_mapper_cache.get(version)
        if cached is None:
            cached = EUDPPTermMapper(schema_version=version)
            self._term_mapper_cache[version] = cached
        return cached

    @staticmethod
    def _detect_version_from_passport(
        passport: DigitalProductPassport,
    ) -> str:
        """Best-effort detection of the source UNTP version.

        Looks at the passport class's module path (``v0_6`` or ``v0_7``)
        against :data:`SCHEMA_REGISTRY`. Each registered version's
        ``major.minor`` becomes a ``vMAJOR_MINOR`` namespace key — the
        resolver picks the registered version whose namespace appears in
        the module path. When two registry entries share the same module
        namespace (e.g. 0.6.0 and 0.6.1 both live under ``v0_6``) the
        highest-patch version wins; that matches the package-canonical
        spelling for the namespace.

        Falls back to :data:`DEFAULT_SCHEMA_VERSION` for unrecognised
        layouts (e.g. third-party subclasses outside the in-tree
        version-namespaced packages).
        """
        module = type(passport).__module__
        candidates: list[str] = []
        for version in SCHEMA_REGISTRY:
            major_minor = ".".join(version.split(".")[:2])
            ns_dotted = f".v{major_minor.replace('.', '_')}"
            if f"{ns_dotted}." in module or module.endswith(ns_dotted):
                candidates.append(version)
        if not candidates:
            return DEFAULT_SCHEMA_VERSION
        return max(candidates, key=lambda v: tuple(int(p) for p in v.split(".")))

    def export(
        self,
        passport: DigitalProductPassport,
        *,
        indent: int | None = 2,
    ) -> str:
        """Export passport to EU DPP JSON-LD string.

        Args:
            passport: Validated DigitalProductPassport
            indent: JSON indentation (None for compact)

        Returns:
            EU DPP JSON-LD formatted string
        """
        data = self.export_dict(passport)
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)

    def export_dict(
        self,
        passport: DigitalProductPassport,
    ) -> dict[str, Any]:
        """Export passport to EU DPP JSON-LD dictionary.

        Args:
            passport: Validated DigitalProductPassport

        Returns:
            EU DPP JSON-LD formatted dictionary
        """
        # Resolve which version's mapper to use. Explicit ``schema_version``
        # passed to the constructor wins; otherwise we auto-detect from the
        # passport class's module path. This is what lets a single exporter
        # instance serve mixed v0.6/v0.7 input without configuration.
        version = self._explicit_version or self._detect_version_from_passport(passport)
        mapper = self._mapper_for(version)

        # Get base UNTP JSON-LD representation
        base = passport.model_dump(mode="json", by_alias=True, exclude_none=True)

        # Apply EU DPP context
        data = self._apply_eudpp_context(base)

        # Map terms if enabled
        if self._map_terms:
            data = self._map_document_terms(data, mapper)

        # Add EU DPP-specific metadata
        data = self._add_eudpp_metadata(data, passport)

        logger.debug("Exported DPP to EU DPP JSON-LD format (version=%s)", version)
        return data

    def export_to_file(
        self,
        passport: DigitalProductPassport,
        path: Path | str,
        *,
        indent: int | None = 2,
    ) -> None:
        """Export passport to EU DPP JSON-LD file.

        Args:
            passport: Validated DigitalProductPassport
            path: Output file path
            indent: JSON indentation
        """
        content = self.export(passport, indent=indent)
        Path(path).write_text(content, encoding="utf-8")
        logger.info("Exported EU DPP JSON-LD to %s", path)

    def _apply_eudpp_context(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply EU DPP @context to the document.

        Args:
            data: JSON-LD dictionary

        Returns:
            Dictionary with EU DPP @context
        """
        result = deepcopy(data)

        # Build context array
        context: list[Any] = [EUDPPNamespace.VC2.value]

        # Add EU DPP namespace context
        context.append(get_eudpp_context())

        # Optionally include UNTP context
        if self._include_untp:
            context.append({"untp": EUDPPNamespace.UNTP_DPP.value})

        result["@context"] = context
        return result

    def _map_document_terms(
        self,
        data: dict[str, Any],
        mapper: EUDPPTermMapper | None = None,
    ) -> dict[str, Any]:
        """Recursively map UNTP terms to EU DPP equivalents.

        Args:
            data: JSON-LD dictionary
            mapper: The version-specific term mapper to use. Defaults to
                the exporter's resolved mapper (Phase 3c added the
                ``mapper`` parameter so :meth:`export_dict` can thread the
                version it picked into the recursive walk).

        Returns:
            Dictionary with mapped terms
        """
        if not isinstance(data, dict):
            return data

        if mapper is None:
            mapper = self._term_mapper

        result: dict[str, Any] = {}

        for key, value in data.items():
            # Don't map special JSON-LD keys
            if key.startswith("@"):
                result[key] = value
                continue

            # Map the key
            mapped_key = mapper.map_key(key)

            # Recursively process values
            if isinstance(value, dict):
                result[mapped_key] = self._map_document_terms(value, mapper)
            elif isinstance(value, list):
                result[mapped_key] = [
                    self._map_document_terms(item, mapper) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[mapped_key] = value

        # Map type values
        if "type" in result:
            result["type"] = self._map_type_value(result["type"], mapper)

        return result

    def _map_type_value(
        self,
        type_value: Any,
        mapper: EUDPPTermMapper | None = None,
    ) -> Any:
        """Map type values to EU DPP equivalents.

        Args:
            type_value: Type string or list
            mapper: Term mapper to use; defaults to the exporter's resolved
                mapper for backward compatibility with pre-Phase-3c calls.

        Returns:
            Mapped type value(s)
        """
        if mapper is None:
            mapper = self._term_mapper
        if isinstance(type_value, str):
            return mapper.map_type(type_value)
        elif isinstance(type_value, list):
            return [mapper.map_type(t) if isinstance(t, str) else t for t in type_value]
        return type_value

    def _add_eudpp_metadata(
        self, data: dict[str, Any], passport: DigitalProductPassport
    ) -> dict[str, Any]:
        """Add EU DPP-specific metadata to the document.

        Args:
            data: JSON-LD dictionary
            passport: Source passport

        Returns:
            Dictionary with EU DPP metadata
        """
        # Add schema reference
        if "schemaVersion" not in data:
            data["schemaVersion"] = "CIRPASS-2 v1.3.0"

        # Surface granularity at the document root with the EU DPP key.
        # In v0.6.x this lived at ``credentialSubject.granularity_level``;
        # in v0.7 it's ``credentialSubject.id_granularity`` (Product is
        # the credential subject directly). Both attributes are checked so
        # the metadata line works for either envelope without a version
        # branch — see the ``term_for`` mapping in ontology.py.
        cs = getattr(passport, "credential_subject", None)
        if cs is not None:
            granularity = getattr(cs, "granularity_level", None) or getattr(
                cs, "id_granularity", None
            )
            if granularity:
                data["granularity"] = granularity

        return data


# =============================================================================
# Convenience Functions
# =============================================================================


def export_eudpp_jsonld(
    passport: DigitalProductPassport,
    *,
    indent: int = 2,
    map_terms: bool = True,
    schema_version: str | None = None,
) -> str:
    """Export a DPP to EU DPP-aligned JSON-LD format.

    Convenience function for simple exports. For more control,
    use EUDPPJsonLDExporter directly.

    Args:
        passport: Validated DigitalProductPassport
        indent: JSON indentation
        map_terms: Map UNTP terms to EU DPP equivalents
        schema_version: UNTP source version. When ``None``, auto-detected
            from the passport's class (Phase 3c).

    Returns:
        EU DPP JSON-LD formatted string
    """
    exporter = EUDPPJsonLDExporter(map_terms=map_terms, schema_version=schema_version)
    return exporter.export(passport, indent=indent)


def export_eudpp_jsonld_dict(
    passport: DigitalProductPassport,
    *,
    map_terms: bool = True,
    schema_version: str | None = None,
) -> dict[str, Any]:
    """Export a DPP to EU DPP-aligned JSON-LD dictionary.

    Convenience function for dictionary output.

    Args:
        passport: Validated DigitalProductPassport
        map_terms: Map UNTP terms to EU DPP equivalents
        schema_version: UNTP source version. When ``None``, auto-detected
            from the passport's class (Phase 3c).

    Returns:
        EU DPP JSON-LD dictionary
    """
    exporter = EUDPPJsonLDExporter(map_terms=map_terms, schema_version=schema_version)
    return exporter.export_dict(passport)


def validate_eudpp_export(data: dict[str, Any]) -> list[str]:
    """Validate EU DPP JSON-LD export structure.

    Checks that the export contains required EU DPP elements.

    Args:
        data: Exported JSON-LD dictionary

    Returns:
        List of validation issues (empty if valid)
    """
    issues: list[str] = []

    # Check @context
    if "@context" not in data:
        issues.append("Missing @context")
    else:
        context = data["@context"]
        if not isinstance(context, list):
            issues.append("@context should be a list")
        else:
            # Check for VC2 context
            if EUDPPNamespace.VC2.value not in context:
                issues.append("Missing W3C VC2 context")

            # Check for EU DPP namespace
            has_eudpp = any(isinstance(c, dict) and "eudpp" in c for c in context)
            if not has_eudpp:
                issues.append("Missing EU DPP namespace in context")

    # Check for type
    if "type" not in data:
        issues.append("Missing type")

    return issues


def get_term_mapping_summary(
    schema_version: str = DEFAULT_SCHEMA_VERSION,
) -> dict[str, str]:
    """Get a summary of UNTP to EU DPP term mappings.

    Args:
        schema_version: UNTP version to summarise (Phase 3c). Defaults to
            :data:`DEFAULT_SCHEMA_VERSION` to preserve the pre-Phase-3c
            output for callers that don't specify.

    Returns:
        Dictionary mapping UNTP terms to EU DPP terms for ``schema_version``.
    """
    mapper = EUDPPTermMapper(schema_version=schema_version)
    return {term: mapper.map_key(term) for term in mapper.mapped_keys}
