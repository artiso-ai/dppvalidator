"""CIRPASS-LD exporter for the v1.3.0 reference-structure shape.

Phase 6 task 6.1 of [docs/plans/CIRPASS_2_MIGRATION.md]. Emits a
CIRPASS reference-structure v1.3.0 payload as JSON-LD with the
canonical EUDPP v1.9.1 ``@context`` attached. The exporter accepts
*either*:

- A :class:`dppvalidator.models.cirpass.v1_3.ReferencePassport`
  instance (the native shape), or
- A :class:`dppvalidator.models.passport.DigitalProductPassport`
  (UNTP envelope), which it routes through the Phase 5 forward
  shim (``compat.to_cirpass_1_3``) before serialising.

The two-input shape lets callers point ``dppvalidator export
--format cirpass-jsonld`` at a UNTP fixture without an explicit
mapping step, while still allowing native-CIRPASS callers to
serialise their own message tree directly.

Output shape
============

The JSON-LD output has:

- ``@context``: ``[W3C VC v2, https://w3id.org/eudpp#]`` plus an
  inline namespace prefix table so consumers without the W3ID
  resolver can still expand compact IRIs.
- ``type``: ``["DigitalProductPassport", "eudpp:DPP"]`` — both the
  CIRPASS message-level type and the EUDPP class IRI.
- The serialised CIRPASS reference-structure tree (camelCase
  aliases per :meth:`UNTPBaseModel.model_dump(by_alias=True)`).
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dppvalidator.logging import get_logger
from dppvalidator.vocabularies.ontology import EUDPPNamespace, get_eudpp_context

if TYPE_CHECKING:
    from dppvalidator.compat import MappingWarning
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport
    from dppvalidator.models.passport import DigitalProductPassport

logger = get_logger(__name__)


# =============================================================================
# Constants
# =============================================================================


# CIRPASS reference structure v1.3.0 default ``type`` array. The
# first entry is the CIRPASS message-level token (``DigitalProductPassport``);
# the second is the EUDPP ontology class IRI in compact form
# (``eudpp:DPP``). Consumers that resolve the @context get the full
# IRIs; those that don't see the message-level token directly.
_CIRPASS_TYPE_ARRAY = ("DigitalProductPassport", "eudpp:DPP")


# =============================================================================
# Public exporter class
# =============================================================================


class CIRPASSJsonLDExporter:
    """Export a CIRPASS reference-structure passport to JSON-LD.

    Accepts either a native CIRPASS :class:`ReferencePassport` or a
    UNTP :class:`DigitalProductPassport`; in the latter case the
    Phase 5 forward shim does the projection. Mapping warnings (when
    a UNTP source is supplied) are surfaced via
    :attr:`last_mapping_warnings` after each export call so callers
    can decide whether to accept the result.
    """

    def __init__(
        self,
        *,
        version: str | None = None,
        include_untp_namespace: bool = False,
    ) -> None:
        """Initialize the exporter.

        Args:
            version: CIRPASS reference-structure version. Defaults to
                the registry's :data:`DEFAULT_VERSIONS[SchemaFamily.CIRPASS]`
                when ``None`` — keeps the no-version-literals guard
                happy and tracks future spec bumps automatically.
            include_untp_namespace: When ``True``, the emitted
                ``@context`` array includes an extra entry binding
                the ``untp:`` prefix to the UNTP 0.7.0 vocabulary.
                Useful for round-trip exports that may be re-read by
                UNTP-aware tooling.
        """
        from dppvalidator.compat import active_version
        from dppvalidator.schemas.registry import SchemaFamily

        self.version = version or active_version(SchemaFamily.CIRPASS)
        self._include_untp_namespace = include_untp_namespace
        self._last_mapping_warnings: list[MappingWarning] = []

    @property
    def last_mapping_warnings(self) -> list[MappingWarning]:
        """Mapping warnings emitted by the most recent export call.

        Empty when the input was a native CIRPASS passport (no
        forward-shim run) or when the UNTP forward shim emitted
        nothing.
        """
        return list(self._last_mapping_warnings)

    def export(
        self,
        passport: ReferencePassport | DigitalProductPassport | dict[str, Any],
        *,
        indent: int | None = 2,
        include_type: bool = True,
        default_language: str = "en",
    ) -> str:
        """Export a passport to a JSON-LD string.

        Args:
            passport: Either a native :class:`ReferencePassport`, a
                UNTP :class:`DigitalProductPassport`, or a parsed
                JSON dict (one of the two shapes — auto-detected via
                ``dppIdentifier`` presence).
            indent: JSON indent for the output; ``None`` for compact.
            include_type: When ``True``, the output includes the
                CIRPASS / EUDPP type array.
            default_language: BCP-47 tag used by the UNTP forward
                shim to wrap UNTP scalar names as CIRPASS LocalisedText.

        Returns:
            JSON-LD formatted string.
        """
        document = self.export_dict(
            passport,
            include_type=include_type,
            default_language=default_language,
        )
        return json.dumps(document, indent=indent, ensure_ascii=False, default=str)

    def export_dict(
        self,
        passport: ReferencePassport | DigitalProductPassport | dict[str, Any],
        *,
        include_type: bool = True,
        default_language: str = "en",
    ) -> dict[str, Any]:
        """Export a passport to a JSON-LD dict.

        Same as :meth:`export` but returns the dictionary directly
        for callers that want to post-process the output (e.g.
        attach a proof, sign, or wrap in a transport envelope).
        """
        cirpass_dict = self._normalise_input(passport, default_language=default_language)
        return self._wrap_with_context(cirpass_dict, include_type=include_type)

    def export_to_file(
        self,
        passport: ReferencePassport | DigitalProductPassport | dict[str, Any],
        path: Path | str,
        *,
        indent: int | None = 2,
        default_language: str = "en",
    ) -> None:
        """Export a passport to a JSON-LD file on disk."""
        content = self.export(passport, indent=indent, default_language=default_language)
        Path(path).write_text(content, encoding="utf-8")
        logger.info("Wrote CIRPASS-LD to %s", path)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _normalise_input(
        self,
        passport: Any,
        *,
        default_language: str,
    ) -> dict[str, Any]:
        """Resolve the input to a CIRPASS-shaped dict.

        Routes UNTP envelopes through the Phase 5 forward shim;
        native CIRPASS passports / dicts are dumped/copied directly.
        Pydantic-model detection is duck-typed (``model_dump``) so
        both v0.6 and v0.7 ``DigitalProductPassport`` classes work
        transparently — we route on shape, not on Python class
        identity.
        """
        # Late imports keep the cold-start budget intact: the
        # ``dppvalidator.exporters`` package may be loaded by callers
        # who never touch CIRPASS, so we delay the CIRPASS / compat
        # imports until this method actually runs.
        from dppvalidator.compat import to_cirpass_1_3
        from dppvalidator.models.cirpass.v1_3 import ReferencePassport

        # Native CIRPASS Pydantic passport — happy path.
        if isinstance(passport, ReferencePassport):
            self._last_mapping_warnings = []
            return passport.model_dump(by_alias=True, exclude_none=True, mode="json")

        # Pydantic model with a model_dump method — UNTP envelope (v0.6
        # or v0.7) or any structurally-compatible model. Both
        # ``DigitalProductPassport`` classes carry the wire shape we
        # need, so a duck-typed ``hasattr`` check is the right move
        # here instead of pinning to a specific class identity.
        if hasattr(passport, "model_dump"):
            untp_dict = passport.model_dump(by_alias=True, exclude_none=True, mode="json")
            cirpass_dict, warnings = to_cirpass_1_3(untp_dict, default_language=default_language)
            self._last_mapping_warnings = warnings
            return cirpass_dict

        # Already-parsed dict — auto-detect shape and pass through or
        # forward-shim accordingly.
        if isinstance(passport, dict):
            if _looks_like_cirpass(passport):
                self._last_mapping_warnings = []
                return deepcopy(passport)
            cirpass_dict, warnings = to_cirpass_1_3(passport, default_language=default_language)
            self._last_mapping_warnings = warnings
            return cirpass_dict

        # Anything else — defensive fail-fast. The exporter is a
        # boundary; surfacing the type mismatch here is much cheaper
        # to debug than letting it propagate into JSON serialisation.
        msg = (
            f"CIRPASSJsonLDExporter.export() expected a ReferencePassport, "
            f"a Pydantic UNTP DigitalProductPassport, or a dict; got "
            f"{type(passport).__name__}."
        )
        raise TypeError(msg)

    def _wrap_with_context(
        self,
        document: dict[str, Any],
        *,
        include_type: bool,
    ) -> dict[str, Any]:
        """Attach the CIRPASS / EUDPP @context + type to ``document``."""
        result: dict[str, Any] = {}
        result["@context"] = list(_build_context_array(self._include_untp_namespace))
        if include_type and "type" not in document:
            result["type"] = list(_CIRPASS_TYPE_ARRAY)
        # Preserve insertion order: @context, type, then the rest.
        result.update(document)
        return result


# =============================================================================
# Helpers
# =============================================================================


def _build_context_array(include_untp_namespace: bool) -> tuple[Any, ...]:
    """Build the CIRPASS @context array.

    Always includes:

    - The W3C VC v2 context (every DPP-shaped credential's first entry).
    - An inline ``{"eudpp": "https://w3id.org/eudpp#"}`` prefix table
      with the canonical EUDPP namespace + the additional CIRPASS
      reference-structure terms (``DigitalProductPassport``,
      ``Product``, ``Identifier``, etc.).

    Optionally appends a UNTP namespace binding for round-trip
    consumers that need to re-resolve UNTP-shaped labels.
    """
    # Pull the canonical EUDPP context (already populated with the
    # eudpp / lca / soc / actor / con prefixes by Phase 1 work).
    context: list[Any] = [
        EUDPPNamespace.VC2.value,
        get_eudpp_context(),
    ]
    if include_untp_namespace:
        context.append({"untp": EUDPPNamespace.UNTP_DPP.value})
    return tuple(context)


def _looks_like_cirpass(data: dict[str, Any]) -> bool:
    """Cheap structural heuristic: is ``data`` already in CIRPASS shape?

    The reference structure v1.3.0 always carries a ``dppIdentifier``
    object at the root and a ``product`` object — UNTP carries
    ``credentialSubject`` instead. The two are mutually exclusive in
    valid payloads, so a single key check suffices.
    """
    if "dppIdentifier" in data and isinstance(data.get("dppIdentifier"), dict):
        return True
    return (
        "product" in data
        and isinstance(data.get("product"), dict)
        and "credentialSubject" not in data
    )


# =============================================================================
# Convenience functions
# =============================================================================


def export_cirpass_jsonld(
    passport: ReferencePassport | DigitalProductPassport | dict[str, Any],
    *,
    indent: int | None = 2,
    include_untp_namespace: bool = False,
    default_language: str = "en",
) -> str:
    """Convenience function: export a passport to a CIRPASS JSON-LD string.

    Mirrors :func:`dppvalidator.exporters.export_jsonld` for the UNTP
    JSON-LD shape.
    """
    exporter = CIRPASSJsonLDExporter(
        include_untp_namespace=include_untp_namespace,
    )
    return exporter.export(passport, indent=indent, default_language=default_language)


def export_cirpass_jsonld_dict(
    passport: ReferencePassport | DigitalProductPassport | dict[str, Any],
    *,
    include_untp_namespace: bool = False,
    default_language: str = "en",
) -> dict[str, Any]:
    """Same as :func:`export_cirpass_jsonld` but returns the dict directly."""
    exporter = CIRPASSJsonLDExporter(
        include_untp_namespace=include_untp_namespace,
    )
    return exporter.export_dict(passport, default_language=default_language)


__all__ = [
    "CIRPASSJsonLDExporter",
    "export_cirpass_jsonld",
    "export_cirpass_jsonld_dict",
]
