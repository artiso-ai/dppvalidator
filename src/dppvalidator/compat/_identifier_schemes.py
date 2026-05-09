"""Static lookup table between UNTP IdentifierScheme and CIRPASS scheme codes.

Phase 5 task 5.5 of [docs/plans/CIRPASS_2_MIGRATION.md] (resolves G18).
UNTP 0.7.0 carries the issuing register as a structured object —
``IdentifierScheme(id: URI, name: str)`` — whereas the CIRPASS v1.3.0
message stores the same information as a flat ``Identifier.scheme``
URI plus an optional ``schemeName`` short-form. The two are
information-equivalent but the wire-shapes differ.

This module is the single point where the translation lives. The
forward shim (``untp_0_7_to_cirpass_1_3.py``) projects an
``IdentifierScheme`` onto a ``(scheme_uri, scheme_name)`` tuple; the
reverse shim (``cirpass_1_3_to_untp_0_7.py``) lifts a CIRPASS
``Identifier`` back into an ``IdentifierScheme``. When a value is
not in the lookup table, callers emit a ``MAP003`` (unmapped)
warning and pass the raw value through.

The bundled table covers the commonly-seen scheme URIs for product /
party / facility identifiers in EU DPP scope:

- GS1 GTIN (product identifiers)
- GS1 Digital Link (alternative product URI form)
- ISO/IEC 15459 (serial-part numbering)
- GLEIF LEI (legal-entity identifiers)
- EU EORI (economic-operator registration)
- EUID (EU business register)
- DUNS (commercial supplier numbering)
- WCO HS / TARIC / CPV (commodity classification)

The table is *additive* — new entries are added as pilots surface
new schemes; removing a scheme is a breaking change because callers
pattern-match on the canonical scheme name.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdentifierSchemeMapping:
    """Two-axis lookup row for a single identifier scheme."""

    scheme_uri: str
    """Canonical URI of the issuing register (the value UNTP carries
    in ``IdentifierScheme.id`` and CIRPASS in ``Identifier.scheme``)."""

    scheme_name: str
    """Short human-readable label (the value UNTP carries in
    ``IdentifierScheme.name`` and CIRPASS in ``Identifier.schemeName``)."""

    aliases: tuple[str, ...] = ()
    """Optional alternative URIs / names that resolve to the same
    canonical scheme. Lookup is canonicalised on the first match."""


# =============================================================================
# Bundled mappings
# =============================================================================
#
# Order is alphabetical-by-scheme-name for deterministic iteration.
# Adding a new scheme: append a row, leave the existing rows untouched.

_BUNDLED: tuple[IdentifierSchemeMapping, ...] = (
    # Commercial / supply-chain
    IdentifierSchemeMapping(
        scheme_uri="https://www.dnb.com/duns-number.html",
        scheme_name="DUNS",
        aliases=("https://duns.com/", "https://www.dnb.com/"),
    ),
    IdentifierSchemeMapping(
        scheme_uri="https://ec.europa.eu/taxation_customs/dds2/eos/eori_home.jsp",
        scheme_name="EORI",
        aliases=("https://ec.europa.eu/eori/",),
    ),
    IdentifierSchemeMapping(
        scheme_uri="https://e-justice.europa.eu/topics/registers-business-insolvency-land/business-registers-search-company-eu_en",
        scheme_name="EUID",
        aliases=("https://e-justice.europa.eu/euid/",),
    ),
    # Product / commodity classification
    IdentifierSchemeMapping(
        scheme_uri="https://gs1.org/voc/",
        scheme_name="GS1 GTIN",
        aliases=("https://www.gs1.org/voc/",),
    ),
    IdentifierSchemeMapping(
        scheme_uri="https://id.gs1.org/01/",
        scheme_name="GS1 Digital Link",
        aliases=("https://gs1.org/dl/",),
    ),
    # Party / legal entity
    IdentifierSchemeMapping(
        scheme_uri="https://www.gleif.org/lei/",
        scheme_name="GLEIF LEI",
        aliases=("https://www.gleif.org/", "https://gleif.org/lei/"),
    ),
    # Item-level serial numbering
    IdentifierSchemeMapping(
        scheme_uri="https://www.iso.org/standard/82220.html",
        scheme_name="ISO/IEC 15459",
        aliases=("https://www.iso.org/standard/iec-15459",),
    ),
    # Commodity classification (HS / TARIC / CPV)
    IdentifierSchemeMapping(
        scheme_uri=(
            "https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/"
            "hs-nomenclature-2022-edition.aspx"
        ),
        scheme_name="WCO HS",
        aliases=("https://www.wcoomd.org/", "https://hs.wcoomd.org/"),
    ),
    IdentifierSchemeMapping(
        scheme_uri="https://ec.europa.eu/taxation_customs/dds2/taric/",
        scheme_name="EU TARIC",
        aliases=("https://ec.europa.eu/taric/",),
    ),
    IdentifierSchemeMapping(
        scheme_uri="https://simap.ted.europa.eu/cpv",
        scheme_name="EU CPV",
    ),
)


# =============================================================================
# Index — canonical URI / canonical name lookup
# =============================================================================
#
# Both indices share the same value (a ``IdentifierSchemeMapping``).
# Aliases populate both indices so calls don't need to canonicalise
# URIs ahead of time.


_BY_URI: dict[str, IdentifierSchemeMapping] = {}
_BY_NAME: dict[str, IdentifierSchemeMapping] = {}

for _row in _BUNDLED:
    _BY_URI[_row.scheme_uri] = _row
    for _alias in _row.aliases:
        _BY_URI.setdefault(_alias, _row)
    _BY_NAME[_row.scheme_name] = _row


# =============================================================================
# Public API
# =============================================================================


def lookup_by_uri(uri: str) -> IdentifierSchemeMapping | None:
    """Return the mapping row for a scheme URI, or ``None`` if unmapped.

    Both canonical URIs and known aliases resolve. The canonical URI
    is the one stored on the resulting :class:`IdentifierSchemeMapping`
    — call sites that want a stable round-trip should use
    ``mapping.scheme_uri`` rather than the input.
    """
    return _BY_URI.get(uri)


def lookup_by_name(name: str) -> IdentifierSchemeMapping | None:
    """Return the mapping row for a scheme short-name, or ``None``."""
    return _BY_NAME.get(name)


def all_mappings() -> tuple[IdentifierSchemeMapping, ...]:
    """Return every bundled mapping row in canonical order.

    Used by tests to assert the table covers every name a CIRPASS
    pilot fixture references; downstream consumers may iterate this
    list when building schema-aware UIs.
    """
    return _BUNDLED


def to_cirpass(
    untp_scheme_id: str | None,
    untp_scheme_name: str | None,
) -> tuple[str, str | None, IdentifierSchemeMapping | None]:
    """Project a UNTP IdentifierScheme onto a CIRPASS (scheme, schemeName) pair.

    Returns ``(scheme_uri, scheme_name, mapping)`` where:

    - ``scheme_uri`` is the URI to put on
      :class:`dppvalidator.models.cirpass.v1_3.Identifier.scheme`.
    - ``scheme_name`` is the optional short-form to put on
      :class:`Identifier.schemeName` (preserves the UNTP scheme name
      verbatim when no canonical row matches).
    - ``mapping`` is the :class:`IdentifierSchemeMapping` row when one
      was found, else ``None`` — call sites use this to decide whether
      to emit a ``MAP003`` (unmapped) warning.

    Empty / missing inputs are tolerated; the caller is expected to
    surface ``MAP004`` separately when the field was required.
    """
    if untp_scheme_id:
        mapping = _BY_URI.get(untp_scheme_id)
        if mapping is not None:
            # Canonicalise: prefer the row's canonical URI so aliases
            # converge to the same shape on the CIRPASS side.
            return mapping.scheme_uri, mapping.scheme_name, mapping
    # Fallback — pass through the raw URI + name. Caller emits MAP003.
    return (untp_scheme_id or ""), untp_scheme_name, None


def to_untp(
    cirpass_scheme: str,
    cirpass_scheme_name: str | None,
) -> tuple[str, str, IdentifierSchemeMapping | None]:
    """Lift a CIRPASS Identifier back onto a UNTP (scheme_id, scheme_name) pair.

    Returns ``(scheme_id, scheme_name, mapping)`` where the third
    element is ``None`` for unmapped schemes (callers emit ``MAP003``).
    The UNTP side requires both ``id`` and ``name`` to be non-empty;
    when the CIRPASS payload omits ``schemeName``, this helper falls
    back to the canonical name from the lookup table, or to the raw
    URI's last path segment as a final defensive fallback.
    """
    mapping = _BY_URI.get(cirpass_scheme)
    if mapping is not None:
        # Prefer the explicit CIRPASS schemeName when present (caller
        # may have a more-specific label than the canonical row);
        # otherwise fall back to the canonical row's name.
        return mapping.scheme_uri, cirpass_scheme_name or mapping.scheme_name, mapping
    if cirpass_scheme_name:
        # Try resolving by name as a fallback.
        mapping = _BY_NAME.get(cirpass_scheme_name)
        if mapping is not None:
            return cirpass_scheme, cirpass_scheme_name, mapping
    # Synthesise a short-form name from the URI when nothing matches.
    name = cirpass_scheme_name or _scheme_name_from_uri(cirpass_scheme)
    return cirpass_scheme, name, None


def _scheme_name_from_uri(uri: str) -> str:
    """Best-effort short-form synthesis from a URI.

    Used when the CIRPASS payload omits ``schemeName`` and the URI
    isn't in the lookup table. Strips trailing slashes / fragments
    and returns the last path segment, falling back to the host.
    """
    cleaned = uri.rstrip("/").rstrip("#")
    if "://" in cleaned:
        cleaned = cleaned.split("://", 1)[1]
    last = cleaned.rsplit("/", 1)[1] or cleaned if "/" in cleaned else cleaned
    return last or "unknown-scheme"


__all__ = [
    "IdentifierSchemeMapping",
    "all_mappings",
    "lookup_by_name",
    "lookup_by_uri",
    "to_cirpass",
    "to_untp",
]
