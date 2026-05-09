"""Phase 2 task 2.7 / 2.8 — fixtures route to the right ``(family, version)``.

Each test below presents a payload with one or more characteristic
markers (``$schema`` URL, ``@context`` URL, type-array tokens, shape
signature) and asserts that :func:`detect_schema_family` and
:func:`detect_schema` resolve it to the expected family. Cardinal
rule §3 (single source of detection truth) means these tests are the
contract: any change to family routing surfaces here first.
"""

from __future__ import annotations

import pytest

from dppvalidator.schemas.registry import DEFAULT_VERSIONS, SchemaFamily
from dppvalidator.validators.detection import (
    detect_schema,
    detect_schema_family,
    detect_schema_version,
    is_cirpass_dpp,
    is_dpp_document,
    is_untp_dpp,
    looks_like_dpp,
)

# =============================================================================
# Fixtures: minimal-but-distinctive payloads per family / signal kind
# =============================================================================


def _untp_v07_via_schema_url() -> dict:
    return {
        "$schema": (
            "https://untp.unece.org/artefacts/schema/v0.7.0/dpp/DigitalProductPassport.json"
        ),
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "credentialSubject": {"name": "X"},
    }


def _untp_v06_via_context() -> dict:
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "credentialSubject": {"name": "X"},
    }


def _untp_via_envelope_only() -> dict:
    """No URL hints, only the VC envelope shape — Priority-3 UNTP signal."""
    return {
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "credentialSubject": {"name": "X"},
    }


def _cirpass_via_context() -> dict:
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2", "https://w3id.org/eudpp/"],
        "type": ["DigitalProductPassport"],
        "Product": {"name": "X"},
    }


def _cirpass_via_schema_url() -> dict:
    return {
        "$schema": "https://example.com/schemas/cirpass-reference-1.3.0.json",
        "type": ["DigitalProductPassport"],
        "Product": {"name": "X"},
    }


def _cirpass_via_shape_only() -> dict:
    """No URL hints, only the CIRPASS reference-structure shape — Priority-3 signal."""
    return {
        "type": ["DigitalProductPassport"],
        "Product": {"name": "X"},
    }


def _payload_no_signals() -> dict:
    """No family signal at all — fallback to UNTP per pre-Phase-2 behaviour."""
    return {"id": "https://example.com/dpp/123"}


# =============================================================================
# detect_schema_family
# =============================================================================


@pytest.mark.parametrize(
    ("name", "data", "expected"),
    [
        ("untp v0.7 via $schema", _untp_v07_via_schema_url(), SchemaFamily.UNTP),
        ("untp v0.6 via @context", _untp_v06_via_context(), SchemaFamily.UNTP),
        ("untp via VC envelope", _untp_via_envelope_only(), SchemaFamily.UNTP),
        ("cirpass via @context (w3id eudpp)", _cirpass_via_context(), SchemaFamily.CIRPASS),
        ("cirpass via $schema", _cirpass_via_schema_url(), SchemaFamily.CIRPASS),
        ("cirpass via root-level Product", _cirpass_via_shape_only(), SchemaFamily.CIRPASS),
    ],
)
def test_detect_schema_family_routes_correctly(
    name: str, data: dict, expected: SchemaFamily
) -> None:
    """Each characteristic marker resolves to the right family."""
    assert detect_schema_family(data) is expected, name


def test_detect_schema_family_returns_none_when_no_signals() -> None:
    """No family signal at all returns ``None`` (caller decides fallback)."""
    assert detect_schema_family(_payload_no_signals()) is None


# =============================================================================
# detect_schema (family + version tuple)
# =============================================================================


def test_detect_schema_returns_untp_with_explicit_version() -> None:
    family, version = detect_schema(_untp_v06_via_context())
    assert family is SchemaFamily.UNTP
    assert version == "0.6.1"


def test_detect_schema_returns_untp_with_v07_via_schema_url() -> None:
    family, version = detect_schema(_untp_v07_via_schema_url())
    assert family is SchemaFamily.UNTP
    assert version == "0.7.0"


def test_detect_schema_returns_cirpass_with_default_version_when_only_signal_is_family() -> None:
    """A CIRPASS payload with no version pointer falls back to the registered default."""
    family, version = detect_schema(_cirpass_via_shape_only())
    assert family is SchemaFamily.CIRPASS
    assert version == DEFAULT_VERSIONS[SchemaFamily.CIRPASS]


def test_detect_schema_returns_cirpass_with_version_from_schema_url() -> None:
    family, version = detect_schema(_cirpass_via_schema_url())
    assert family is SchemaFamily.CIRPASS
    assert version == "1.3.0"


def test_detect_schema_no_signals_falls_back_to_untp_default() -> None:
    """Pre-Phase-2 default-to-UNTP behaviour preserved for marker-less payloads."""
    family, version = detect_schema(_payload_no_signals())
    assert family is SchemaFamily.UNTP
    assert version == DEFAULT_VERSIONS[SchemaFamily.UNTP]


# =============================================================================
# Pre-Phase-2 detect_schema_version is unchanged for UNTP payloads
# =============================================================================


def test_detect_schema_version_back_compat_for_untp_payloads() -> None:
    """The pre-Phase-2 :func:`detect_schema_version` keeps returning UNTP versions."""
    assert detect_schema_version(_untp_v06_via_context()) == "0.6.1"
    assert detect_schema_version(_untp_v07_via_schema_url()) == "0.7.0"


def test_detect_schema_version_returns_default_for_cirpass_payloads() -> None:
    """Pre-Phase-2 API: CIRPASS-only payloads still resolve to UNTP default
    (the function's contract is UNTP-only — callers wanting CIRPASS must
    use :func:`detect_schema`).
    """
    assert detect_schema_version(_cirpass_via_shape_only()) == DEFAULT_VERSIONS[SchemaFamily.UNTP]


# =============================================================================
# Family-aware predicates: looks_like_dpp / is_untp_dpp / is_cirpass_dpp
# =============================================================================


def test_looks_like_dpp_true_for_both_families() -> None:
    """Phase 2 task 2.10 exit criterion: ``looks_like_dpp`` covers both families."""
    assert looks_like_dpp(_untp_via_envelope_only())
    assert looks_like_dpp(_cirpass_via_shape_only())
    assert looks_like_dpp(_untp_v07_via_schema_url())
    assert looks_like_dpp(_cirpass_via_context())


def test_is_untp_dpp_only_true_for_untp() -> None:
    assert is_untp_dpp(_untp_via_envelope_only())
    assert is_untp_dpp(_untp_v06_via_context())
    assert not is_untp_dpp(_cirpass_via_shape_only())
    assert not is_untp_dpp(_cirpass_via_context())


def test_is_cirpass_dpp_only_true_for_cirpass() -> None:
    assert is_cirpass_dpp(_cirpass_via_shape_only())
    assert is_cirpass_dpp(_cirpass_via_context())
    assert is_cirpass_dpp(_cirpass_via_schema_url())
    assert not is_cirpass_dpp(_untp_via_envelope_only())
    assert not is_cirpass_dpp(_untp_v06_via_context())


def test_is_dpp_document_alias_preserves_back_compat() -> None:
    """Pre-Phase-2 :func:`is_dpp_document` is now an alias for
    :func:`looks_like_dpp` — same return for all family fixtures.

    Phase 9 task 9.4 (dppvalidator 0.5.0) added a
    ``DeprecationWarning`` to the alias; we suppress it here
    because the test is asserting the back-compat *value*, not the
    warning behaviour (which has its own dedicated test below).
    """
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        for fixture in (
            _untp_via_envelope_only(),
            _cirpass_via_shape_only(),
            _untp_v06_via_context(),
            _cirpass_via_context(),
        ):
            assert is_dpp_document(fixture) == looks_like_dpp(fixture)


def test_is_dpp_document_emits_deprecation_warning_in_0_5_0() -> None:
    """Phase 9 task 9.4: the alias must emit a DeprecationWarning."""
    import warnings

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        is_dpp_document(_untp_via_envelope_only())
    deprecation = [w for w in captured if issubclass(w.category, DeprecationWarning)]
    assert len(deprecation) == 1
    assert "is_dpp_document" in str(deprecation[0].message)
    assert "looks_like_dpp" in str(deprecation[0].message)


def test_no_signals_payload_not_a_dpp() -> None:
    """A payload with no DPP markers returns False from :func:`looks_like_dpp`."""
    assert not looks_like_dpp(_payload_no_signals())
    assert not is_untp_dpp(_payload_no_signals())
    assert not is_cirpass_dpp(_payload_no_signals())
