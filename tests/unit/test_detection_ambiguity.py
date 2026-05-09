"""Phase 2 task 2.7 — disambiguation when family signals overlap or are absent.

The migration plan's R10 risk row: ``DigitalProductPassport`` as a
type token is shared between UNTP and CIRPASS. A payload carrying the
bare token with no other signal is genuinely ambiguous — the
detection code falls through to a deterministic resolution rather
than picking silently. This test pins the resolution rules so future
edits to the type-array set or the priority order surface here first.

Specific resolution invariants:

1. UNTP ``@context`` + EUDPP ``@context`` co-occurrence resolves to
   UNTP (a UNTP-VC may declare downstream EUDPP-LD bindings without
   becoming a CIRPASS payload).
2. ``credentialSubject`` shape is a UNTP signal; root-level
   ``Product`` is a CIRPASS signal.
3. Bare ``DigitalProductPassport`` type with no other signal:
   :func:`detect_schema_family` returns ``None`` (caller decides
   fallback), :func:`detect_schema` falls back to UNTP/default per
   pre-Phase-2 behaviour, :func:`looks_like_dpp` still returns True.
4. The :data:`DET_CODE_FAMILY_MISMATCH` constant exists for engine
   callers that want to surface ambiguity rather than fall through
   silently.
"""

from __future__ import annotations

from dppvalidator.schemas.registry import DEFAULT_VERSIONS, SchemaFamily
from dppvalidator.validators.detection import (
    DET_CODE_FAMILY_MISMATCH,
    detect_schema,
    detect_schema_family,
    looks_like_dpp,
)


def test_untp_context_authoritative_when_eudpp_also_referenced() -> None:
    """A UNTP-VC that *also* references EUDPP in its context is still UNTP.

    The EUDPP IRI in a UNTP-VC's context array is a downstream binding
    declaration, not a family override.
    """
    payload = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            "https://w3id.org/eudpp/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "credentialSubject": {"name": "X"},
    }
    assert detect_schema_family(payload) is SchemaFamily.UNTP


def test_credential_subject_disambiguates_to_untp() -> None:
    """``credentialSubject`` is a UNTP signal even if no @context/$schema."""
    payload = {
        "type": ["DigitalProductPassport"],
        "credentialSubject": {"name": "X"},
    }
    assert detect_schema_family(payload) is SchemaFamily.UNTP


def test_root_level_product_disambiguates_to_cirpass() -> None:
    """Root-level ``Product`` is a CIRPASS signal even with bare DPP type."""
    payload = {
        "type": ["DigitalProductPassport"],
        "Product": {"name": "X"},
    }
    assert detect_schema_family(payload) is SchemaFamily.CIRPASS


def test_bare_dpp_type_returns_none_family() -> None:
    """A payload with only the ambiguous DPP type token returns ``None``."""
    payload = {"type": ["DigitalProductPassport"]}
    assert detect_schema_family(payload) is None


def test_bare_dpp_type_falls_back_to_untp_default_via_detect_schema() -> None:
    """When ``detect_schema_family`` returns None, ``detect_schema`` falls
    back to UNTP/default (pre-Phase-2 default-to-UNTP behaviour preserved).
    """
    payload = {"type": ["DigitalProductPassport"]}
    family, version = detect_schema(payload)
    assert family is SchemaFamily.UNTP
    assert version == DEFAULT_VERSIONS[SchemaFamily.UNTP]


def test_bare_dpp_type_still_a_dpp_per_looks_like_dpp() -> None:
    """The ambiguous bare token is still a DPP (pre-Phase-2 back-compat)."""
    payload = {"type": ["DigitalProductPassport"]}
    assert looks_like_dpp(payload)


def test_det001_constant_exists_and_has_stable_value() -> None:
    """The error-code constant is part of the public detection surface.

    The engine surfaces it as ``DET001`` per Phase 2 task 2.12.
    """
    assert DET_CODE_FAMILY_MISMATCH == "DET001"


def test_no_signals_payload_resolves_deterministically_to_untp_default() -> None:
    """A payload with no DPP markers at all still gets a deterministic
    ``(family, version)`` from :func:`detect_schema` — UNTP at default
    version. ``detect_schema_family`` returns ``None``;
    :func:`looks_like_dpp` returns False (it's not a DPP).
    """
    payload: dict = {}
    assert detect_schema_family(payload) is None
    assert not looks_like_dpp(payload)
    family, version = detect_schema(payload)
    assert family is SchemaFamily.UNTP
    assert version == DEFAULT_VERSIONS[SchemaFamily.UNTP]


def test_conflicting_schema_url_and_context_resolves_per_priority() -> None:
    """When ``@context`` and ``$schema`` disagree, ``@context`` wins.

    Resolution priority for :func:`detect_schema_family` is documented:
    ``@context`` > ``$schema`` > shape signature. A pathological
    payload with a UNTP ``@context`` but a CIRPASS-shaped ``$schema``
    URL resolves to UNTP. This is the expected resolution per the
    migration plan's §4.3 cardinal-rule extension on family dispatch.
    """
    payload = {
        "$schema": "https://example.com/schemas/cirpass-reference-1.3.0.json",
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.7.0/",
        ],
        "type": ["DigitalProductPassport"],
    }
    assert detect_schema_family(payload) is SchemaFamily.UNTP
