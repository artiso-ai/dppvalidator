"""Schema family + version auto-detection from DPP data.

Phase 2 of [docs/plans/CIRPASS_2_MIGRATION.md] extended this module with
:class:`SchemaFamily`-aware detection. Pre-Phase-2 callers using
:func:`detect_schema_version` and :func:`is_dpp_document` keep working
unchanged (they resolve against the UNTP family). New code should use
:func:`detect_schema_family`, :func:`detect_schema`, and the family-
specific helpers :func:`is_untp_dpp` / :func:`is_cirpass_dpp`.

Cardinal rule §3 still binds: this module is the **only** place that
decides what family or version a payload is. New URL/namespace shapes
extend the pattern tuples here, nowhere else.
"""

from __future__ import annotations

import re
from typing import Any

from dppvalidator.schemas.registry import (
    DEFAULT_SCHEMA_VERSION,
    DEFAULT_VERSIONS,
    SCHEMA_REGISTRY,
    SCHEMA_REGISTRY_BY_FAMILY,
    SchemaFamily,
)

# =============================================================================
# Error codes
# =============================================================================

# Phase 2 task 2.12 of docs/plans/CIRPASS_2_MIGRATION.md. ``DET001``
# surfaces when a payload's family/version markers are mutually
# contradictory or silently ambiguous — the engine raises this rather
# than letting the payload fall through to ``DEFAULT_SCHEMA_VERSION``.
DET_CODE_FAMILY_MISMATCH = "DET001"


# =============================================================================
# URL patterns
# =============================================================================
#
# Two URL conventions are recognised, in priority order:
#   1. UNTP legacy (0.6.x): schema basename ``untp-dpp-schema-X.Y.Z.json``
#      and context ``/untp/dpp/X.Y.Z/`` under ``test.uncefact.org``.
#   2. UNTP modern (0.7.0+): schema lives at any path containing the
#      version as a ``/X.Y.Z/`` or ``/vX.Y.Z/`` segment followed by a
#      credential-type basename (``DigitalProductPassport.json``); the
#      context lives at ``/untp/X.Y.Z/context/?`` under
#      ``vocabulary.uncefact.org``.
#   3. CIRPASS (Phase 2+): schema basename ``cirpass-reference-X.Y.Z.json``
#      (Phase 3 task 3.1 derives this) and context that contains the
#      canonical EUDPP IRI ``https://w3id.org/eudpp`` (with `/` or `#`).
#
# False positives are guarded by the ``version in SCHEMA_REGISTRY``
# membership check at the call sites, so unrelated ``/X.Y.Z/`` path
# segments cannot smuggle in unsupported versions.

_UNTP_SCHEMA_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"untp-dpp-schema-(\d+\.\d+\.\d+)\.json"),
    re.compile(r"/v?(\d+\.\d+\.\d+)/[^?#]*DigitalProductPassport[^?#]*\.json"),
)
_UNTP_CONTEXT_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/untp/dpp/(\d+\.\d+\.\d+)/?"),
    re.compile(r"/untp/(\d+\.\d+\.\d+)/(?:context/?)?"),
)

_CIRPASS_SCHEMA_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Phase 3 task 3.1 names the derived JSON Schema this way:
    re.compile(r"cirpass-reference-(\d+\.\d+\.\d+)\.json"),
    # Hub vocab listing fragment used by the CIRPASS reference structure:
    re.compile(r"#cirpass-dpp-reference-structure-v(\d+\.\d+\.\d+)\b"),
)
_CIRPASS_CONTEXT_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Hub-published context URL (when a paired context lands in Phase 1.12):
    re.compile(r"/cirpass(?:-2)?/dpp/(\d+\.\d+\.\d+)/?"),
)

# Substring fragments that, when present in a JSON-LD ``@context``, are
# strong family signals. The CIRPASS reference structure binds the
# canonical EUDPP IRI ``https://w3id.org/eudpp`` (Phase 1 / ADR 0002);
# UNTP binds ``vocabulary.uncefact.org/untp`` or
# ``test.uncefact.org/vocabulary/untp``. The two are mutually
# exclusive in the wild, but if a payload contains both,
# ``detect_schema_family`` treats UNTP as authoritative (a UNTP-VC
# carrying a downstream EUDPP-LD reference is still a UNTP-VC).
_UNTP_CONTEXT_SIGNAL = "uncefact.org"
_CIRPASS_CONTEXT_SIGNAL = "w3id.org/eudpp"

# Type-array tokens. UNTP wraps the DPP in a Verifiable Credential
# (so payloads carry both ``DigitalProductPassport`` and
# ``VerifiableCredential``). CIRPASS reference structure does not — it
# is a plain message; the type token alone is therefore not sufficient
# to disambiguate. Resolution falls through to shape signature.
_UNTP_TYPES = frozenset({"DigitalProductPassport", "VerifiableCredential"})
_CIRPASS_TYPES = frozenset({"DigitalProductPassport"})


# =============================================================================
# Public detection API
# =============================================================================


def detect_schema_version(data: dict[str, Any]) -> str:
    """Detect UNTP DPP schema version from data (pre-Phase-2 API).

    Always resolves against the UNTP family. New code should call
    :func:`detect_schema` for a ``(family, version)`` pair.

    Detection priority:

    1. ``$schema`` URL (explicit schema reference, UNTP shape)
    2. ``@context`` URLs (JSON-LD context with UNTP version)
    3. ``type`` array (confirms DPP, uses default UNTP version)
    4. Falls back to :data:`DEFAULT_SCHEMA_VERSION`

    Args:
        data: Raw DPP JSON data

    Returns:
        Detected schema version string (one of
        ``SCHEMA_REGISTRY.keys()``). Falls back to
        :data:`DEFAULT_SCHEMA_VERSION` when no marker is present.
    """
    # Priority 1: Check $schema URL
    version = _detect_untp_from_schema_url(data)
    if version:
        return version

    # Priority 2: Check @context URLs
    version = _detect_untp_from_context(data)
    if version:
        return version

    # Priority 3: Check type array for DPP marker, use default
    if _is_untp_type(data):
        return DEFAULT_SCHEMA_VERSION

    # Fallback to default
    return DEFAULT_SCHEMA_VERSION


def detect_declared_version(data: dict[str, Any]) -> str | None:
    """Return the UNTP version a payload **explicitly declares**, or ``None``.

    Distinct from :func:`detect_schema_version`: this helper returns
    ``None`` when no UNTP-versioned ``$schema`` URL or UNTP-versioned
    ``@context`` URL is present, instead of falling back to a default.
    The engine uses this for the VER001 mismatch check: if a payload
    declares a version that conflicts with the engine's explicitly-
    configured version, fail fast — but if the payload declares no
    version at all, trust the user's configuration without complaint.

    Args:
        data: Raw DPP JSON data

    Returns:
        The declared version (one of ``SCHEMA_REGISTRY.keys()``), or
        ``None`` when the payload carries no version markers.
    """
    return _detect_untp_from_schema_url(data) or _detect_untp_from_context(data)


def detect_schema_family(data: dict[str, Any]) -> SchemaFamily | None:
    """Detect which schema family a payload belongs to.

    Resolution order (Phase 2 task 2.7 of the migration plan):

    1. ``@context`` URL: ``uncefact.org/untp`` ⇒ UNTP (authoritative
       even if the context array also references EUDPP, since a
       UNTP-VC may declare downstream EUDPP-LD bindings without being
       a CIRPASS payload itself); ``w3id.org/eudpp`` (without UNTP) ⇒
       CIRPASS.
    2. ``$schema`` URL: matches one of the family-specific URL pattern
       sets.
    3. Shape signature: ``credentialSubject`` present ⇒ UNTP;
       root-level ``Product`` (or other CIRPASS reference-structure
       top-level entity) ⇒ CIRPASS.

    Returns ``None`` when the payload carries no family signal at all.
    Callers that need a default should fall back to
    :data:`SchemaFamily.UNTP` (the historical pre-Phase-2 behaviour),
    or surface ``DET_CODE_FAMILY_MISMATCH`` as appropriate.
    """
    # Priority 1: @context disambiguation.
    context_signal = _family_from_context(data)
    if context_signal is not None:
        return context_signal

    # Priority 2: $schema URL.
    schema_url = data.get("$schema")
    if isinstance(schema_url, str):
        if any(p.search(schema_url) for p in _UNTP_SCHEMA_URL_PATTERNS):
            return SchemaFamily.UNTP
        if any(p.search(schema_url) for p in _CIRPASS_SCHEMA_URL_PATTERNS):
            return SchemaFamily.CIRPASS

    # Priority 3: shape signature.
    if "credentialSubject" in data:
        return SchemaFamily.UNTP
    # CIRPASS reference structure: distinctive top-level keys only the
    # v1.3.0 message tree-view exposes. ``dppIdentifier`` is the strongest
    # signal — UNTP has no envelope-level field with that name. Phase 4
    # of the migration plan added the lowercase ``product`` + ``issuedAt``
    # composite as a secondary signal so payloads that omit
    # ``dppIdentifier`` still resolve correctly.
    if "dppIdentifier" in data and isinstance(data.get("dppIdentifier"), dict):
        return SchemaFamily.CIRPASS
    if "product" in data and isinstance(data.get("product"), dict) and "issuedAt" in data:
        return SchemaFamily.CIRPASS
    # Capitalised ``Product`` was the historical CIRPASS-2 hub
    # tree-view rendering; kept for back-compat with payloads emitted
    # by upstream tooling that hadn't yet adopted lowercase keys.
    if "Product" in data and isinstance(data.get("Product"), dict):
        return SchemaFamily.CIRPASS

    return None


def detect_schema(data: dict[str, Any]) -> tuple[SchemaFamily, str]:
    """Detect ``(family, version)`` for a payload (Phase 2 task 2.8).

    Combines :func:`detect_schema_family` with family-specific version
    detection. Falls back to ``(SchemaFamily.UNTP, DEFAULT_SCHEMA_VERSION)``
    when no signals are present — preserves pre-Phase-2 behaviour for
    payloads with no markers (the historical "default to UNTP latest").

    Returns:
        Tuple of (family, version) where the version belongs to the
        detected family's registered set.
    """
    family = detect_schema_family(data)
    if family is SchemaFamily.CIRPASS:
        version = _detect_cirpass_from_schema_url(data) or _detect_cirpass_from_context(data)
        if version is None:
            version = DEFAULT_VERSIONS[SchemaFamily.CIRPASS]
        return SchemaFamily.CIRPASS, version
    # UNTP path — covers explicit UNTP signal AND the no-signal
    # fallback (cardinal rule: pre-Phase-2 default-to-UNTP behaviour
    # is preserved).
    return SchemaFamily.UNTP, detect_schema_version(data)


# =============================================================================
# Family-aware document predicates (Phase 2 task 2.10)
# =============================================================================


def looks_like_dpp(data: dict[str, Any]) -> bool:
    """True if ``data`` looks like *any* DPP payload (UNTP or CIRPASS).

    Phase 2 rename of the historical :func:`is_dpp_document` —
    family-neutral. Recognises the family-specific signals from
    :func:`is_untp_dpp` and :func:`is_cirpass_dpp`, plus a bare
    ``DigitalProductPassport`` type token (ambiguous between families
    but still a positive DPP marker — preserves the pre-Phase-2 back-
    compat behaviour where ``is_dpp_document(type='DigitalProductPassport')``
    returned True). The :func:`is_dpp_document` alias is removed in
    Phase 10.
    """
    if not isinstance(data, dict):
        return False
    if is_untp_dpp(data) or is_cirpass_dpp(data):
        return True
    # Bare ``DigitalProductPassport`` token — family-ambiguous but
    # still a positive DPP signal.
    return _has_type(data, "DigitalProductPassport")


def is_dpp_document(data: dict[str, Any]) -> bool:
    """Alias for :func:`looks_like_dpp` (pre-Phase-2 API).

    .. deprecated:: 0.5.0
        Use :func:`looks_like_dpp` instead. This alias will be removed
        in dppvalidator 0.6.0 (Phase 10 of
        ``docs/plans/CIRPASS_2_MIGRATION.md``).
    """
    import warnings

    warnings.warn(
        "is_dpp_document() is deprecated since dppvalidator 0.5.0; use "
        "looks_like_dpp() instead. The alias will be removed in 0.6.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return looks_like_dpp(data)


def is_untp_dpp(data: dict[str, Any]) -> bool:
    """True if ``data`` looks like a UNTP DPP / VC payload.

    A bare ``DigitalProductPassport`` type token is ambiguous (both
    UNTP and CIRPASS use it; see R10 in the migration plan), so this
    predicate requires a *strictly UNTP-only* signal:

    - ``type`` array contains ``VerifiableCredential`` (VC marker —
      CIRPASS reference structure does not use this), OR
    - ``credentialSubject`` field present (VC envelope shape — CIRPASS
      reference structure has root-level entities, no envelope), OR
    - ``@context`` carries a UNTP IRI fragment.
    """
    if not isinstance(data, dict):
        return False
    if _has_type(data, "VerifiableCredential"):
        return True
    if "credentialSubject" in data:
        return True
    return _context_contains(data, _UNTP_CONTEXT_SIGNAL)


def is_cirpass_dpp(data: dict[str, Any]) -> bool:
    """True if ``data`` looks like a CIRPASS DPP reference-structure payload.

    Signals (any of):
    - ``$schema`` matches a CIRPASS URL pattern.
    - ``@context`` carries a canonical EUDPP IRI fragment AND no UNTP
      fragment (a UNTP payload that *also* references EUDPP via context
      remains UNTP).
    - Root-level ``Product`` object plus ``DigitalProductPassport``
      type token (CIRPASS reference shape) AND no UNTP envelope marker.
    """
    if not isinstance(data, dict):
        return False
    schema_url = data.get("$schema")
    if isinstance(schema_url, str) and any(
        p.search(schema_url) for p in _CIRPASS_SCHEMA_URL_PATTERNS
    ):
        return True
    if _context_contains(data, _CIRPASS_CONTEXT_SIGNAL) and not _context_contains(
        data, _UNTP_CONTEXT_SIGNAL
    ):
        return True
    has_vc_envelope = "credentialSubject" in data
    if has_vc_envelope:
        return False
    # Strong CIRPASS-message signals (v1.3.0 tree-view shape).
    if "dppIdentifier" in data and isinstance(data.get("dppIdentifier"), dict):
        return True
    if "product" in data and isinstance(data.get("product"), dict) and "issuedAt" in data:
        return True
    has_root_product = "Product" in data and isinstance(data.get("Product"), dict)
    has_dpp_type = _has_type(data, "DigitalProductPassport")
    return has_root_product and has_dpp_type


# =============================================================================
# Internal helpers
# =============================================================================


def _detect_untp_from_schema_url(data: dict[str, Any]) -> str | None:
    """Extract a UNTP-registered version from a ``$schema`` URL."""
    schema_url = data.get("$schema")
    if not isinstance(schema_url, str):
        return None

    for pattern in _UNTP_SCHEMA_URL_PATTERNS:
        match = pattern.search(schema_url)
        if match and match.group(1) in SCHEMA_REGISTRY:
            return match.group(1)

    return None


def _detect_untp_from_context(data: dict[str, Any]) -> str | None:
    """Extract a UNTP-registered version from the ``@context`` URLs."""
    urls = _context_urls(data)
    for url in urls:
        for pattern in _UNTP_CONTEXT_URL_PATTERNS:
            match = pattern.search(url)
            if match and match.group(1) in SCHEMA_REGISTRY:
                return match.group(1)
    return None


def _detect_cirpass_from_schema_url(data: dict[str, Any]) -> str | None:
    """Extract a CIRPASS-registered version from a ``$schema`` URL."""
    schema_url = data.get("$schema")
    if not isinstance(schema_url, str):
        return None
    for pattern in _CIRPASS_SCHEMA_URL_PATTERNS:
        match = pattern.search(schema_url)
        version = match.group(1) if match else None
        if version and (SchemaFamily.CIRPASS, version) in SCHEMA_REGISTRY_BY_FAMILY:
            return version
    return None


def _detect_cirpass_from_context(data: dict[str, Any]) -> str | None:
    """Extract a CIRPASS-registered version from the ``@context`` URLs."""
    urls = _context_urls(data)
    for url in urls:
        for pattern in _CIRPASS_CONTEXT_URL_PATTERNS:
            match = pattern.search(url)
            version = match.group(1) if match else None
            if version and (SchemaFamily.CIRPASS, version) in SCHEMA_REGISTRY_BY_FAMILY:
                return version
    return None


def _family_from_context(data: dict[str, Any]) -> SchemaFamily | None:
    """Pick a family from ``@context`` substring signals.

    UNTP is checked first: a payload that mentions both UNTP and EUDPP
    in its context array is *still* UNTP (the EUDPP IRI is a downstream
    binding the UNTP-VC declares, not a family override).
    """
    if _context_contains(data, _UNTP_CONTEXT_SIGNAL):
        return SchemaFamily.UNTP
    if _context_contains(data, _CIRPASS_CONTEXT_SIGNAL):
        return SchemaFamily.CIRPASS
    return None


def _context_urls(data: dict[str, Any]) -> list[str]:
    """Return the flat list of URL strings referenced in ``@context``."""
    context = data.get("@context")
    if context is None:
        return []
    if isinstance(context, str):
        return [context]
    if isinstance(context, list):
        return [u for u in context if isinstance(u, str)]
    return []


def _context_contains(data: dict[str, Any], substring: str) -> bool:
    """True if any ``@context`` URL or value contains ``substring``."""
    context = data.get("@context")
    if context is None:
        return False
    return substring in str(context)


def _has_type(data: dict[str, Any], type_token: str) -> bool:
    """True if ``data['type']`` (string or list of strings) contains ``type_token``."""
    type_value = data.get("type")
    if type_value is None:
        return False
    if isinstance(type_value, str):
        return type_value == type_token
    if isinstance(type_value, list):
        return any(t == type_token for t in type_value if isinstance(t, str))
    return False


def _is_untp_type(data: dict[str, Any]) -> bool:
    """True if the type array carries a UNTP token (DPP or VC)."""
    type_value = data.get("type")
    if type_value is None:
        return False
    if isinstance(type_value, str):
        return type_value in _UNTP_TYPES
    if isinstance(type_value, list):
        return any(t in _UNTP_TYPES for t in type_value if isinstance(t, str))
    return False
