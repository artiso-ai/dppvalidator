"""Cross-family pipeline isolation test.

Phase 4 of [docs/plans/CIRPASS_2_MIGRATION.md]. Asserts that:

- A UNTP-VC payload fed into the engine is *not* routed to the
  CIRPASS pipeline. The auto-detect resolves to UNTP, the schema
  layer loads the UNTP schema, and CIRPASS rules never run.
- A CIRPASS reference-structure payload is *not* routed to the
  UNTP pipeline. The auto-detect resolves to CIRPASS, and UNTP
  semantic rules never run against the CIRPASS root.
- A bare ``DigitalProductPassport`` token (family-ambiguous) falls
  back to the historical UNTP default — preserves pre-Phase-2
  behaviour for legacy callers.

The test inspects the rule-set the semantic validator picked, not
the resulting violations — that's the most direct evidence of the
dispatch table doing its job.
"""

from __future__ import annotations

import json
from pathlib import Path

from dppvalidator import ValidationEngine
from dppvalidator.schemas.registry import SchemaFamily
from dppvalidator.validators.detection import detect_schema, detect_schema_family

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _load_cirpass_full() -> dict:
    return json.loads((_FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "full.json").read_text())


def _untp_v07_payload() -> dict:
    """Construct a minimal UNTP 0.7.0 envelope shape.

    Test-fixture-free so the assertion is purely about envelope
    detection (presence of ``credentialSubject``).
    """
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ],
        "type": ["VerifiableCredential", "DigitalProductPassport"],
        "id": "https://example.com/dpp/untp",
        "issuer": {"id": "did:web:example.com", "name": "Example"},
        "validFrom": "2026-01-01T00:00:00+00:00",
        "credentialSubject": {
            "id": "https://example.com/product/1",
            "type": ["Product"],
            "name": "UNTP Test Product",
            "idGranularity": "model",
        },
    }


# =============================================================================
# Detection-layer isolation
# =============================================================================


def test_untp_payload_routes_to_untp_family() -> None:
    family = detect_schema_family(_untp_v07_payload())
    assert family is SchemaFamily.UNTP


def test_cirpass_payload_routes_to_cirpass_family() -> None:
    family = detect_schema_family(_load_cirpass_full())
    assert family is SchemaFamily.CIRPASS


def test_detect_schema_returns_correct_pair_for_untp() -> None:
    family, version = detect_schema(_untp_v07_payload())
    assert family is SchemaFamily.UNTP
    assert version == "0.7.0"


def test_detect_schema_returns_correct_pair_for_cirpass() -> None:
    family, version = detect_schema(_load_cirpass_full())
    assert family is SchemaFamily.CIRPASS
    assert version == "1.3.0"


# =============================================================================
# Engine-layer isolation
# =============================================================================


def test_untp_payload_does_not_load_cirpass_rules() -> None:
    """When the engine routes to UNTP, the semantic validator's
    ``rules`` attribute lists UNTP rules only — no CIRPASS rules."""
    engine = ValidationEngine(schema_version="auto", load_plugins=False)
    engine.validate(_untp_v07_payload())
    assert engine.family is SchemaFamily.UNTP
    assert engine._semantic_validator is not None
    rule_classes = {type(r).__name__ for r in engine._semantic_validator.rules}
    # Some UNTP rules to look for.
    assert any(name in rule_classes for name in {"MassFractionSumRule", "GTINChecksumRule"})
    # No CIRPASS rules should have leaked into the UNTP set.
    cirpass_names = {
        "DPPIdentifierUniqueRule",
        "SubstanceIdentificationRule",
        "ImpactCategoryClosureRule",
        "ActorRoleClosureRule",
        "ConnectorRelationTypeClosureRule",
    }
    assert not (rule_classes & cirpass_names), (
        f"CIRPASS rules leaked into the UNTP pipeline: {rule_classes & cirpass_names}"
    )


def test_cirpass_payload_does_not_load_untp_rules() -> None:
    """When the engine routes to CIRPASS, the semantic validator's
    ``rules`` attribute lists CIRPASS rules only — no UNTP rules."""
    engine = ValidationEngine(schema_version="auto", load_plugins=False)
    engine.validate(_load_cirpass_full())
    assert engine.family is SchemaFamily.CIRPASS
    assert engine._semantic_validator is not None
    rule_classes = {type(r).__name__ for r in engine._semantic_validator.rules}
    cirpass_names = {
        "DPPIdentifierUniqueRule",
        "SubstanceIdentificationRule",
        "ImpactCategoryClosureRule",
    }
    assert cirpass_names <= rule_classes, (
        f"Expected CIRPASS rules in the CIRPASS pipeline; got {rule_classes}"
    )
    untp_names = {
        "MassFractionSumRule",
        "GTINChecksumRule",
        "MaterialCodeRule",
        "OperationalScopeRule",
    }
    assert not (rule_classes & untp_names), (
        f"UNTP rules leaked into the CIRPASS pipeline: {rule_classes & untp_names}"
    )


def test_cirpass_payload_does_not_emit_untp_error_codes() -> None:
    """Symmetric reverse case from Phase 4 §Tests:

    Feeding a CIRPASS reference-structure payload to the engine
    must not produce cascading per-rule UNTP failures (SEM/VOC).
    The CIRPASS pipeline's rule set is the authoritative source of
    semantic violations, so all semantic-layer codes must be
    CIRPASS prefixes (CR/SUB/LCS/ACT/REL).
    """
    data = _load_cirpass_full()
    engine = ValidationEngine(schema_version="auto", load_plugins=False)
    result = engine.validate(data)
    semantic_codes = {e.code for e in (*result.errors, *result.warnings) if e.layer == "semantic"}
    untp_prefixes = ("SEM", "VOC", "CQ")
    leaks = {c for c in semantic_codes if c.startswith(untp_prefixes)}
    assert not leaks, f"UNTP semantic codes leaked on CIRPASS payload: {leaks}"


def test_untp_payload_does_not_emit_cirpass_error_codes() -> None:
    """A UNTP payload must not fire CIRPASS-prefixed rules."""
    engine = ValidationEngine(schema_version="auto", load_plugins=False)
    result = engine.validate(_untp_v07_payload())
    semantic_codes = {e.code for e in (*result.errors, *result.warnings) if e.layer == "semantic"}
    cirpass_prefixes = ("CR", "SUB", "LCS", "ACT", "REL")
    leaks = {c for c in semantic_codes if c.startswith(cirpass_prefixes)}
    assert not leaks, f"CIRPASS semantic codes leaked on UNTP payload: {leaks}"


# =============================================================================
# Bare-token fallback (pre-Phase-2 back-compat)
# =============================================================================


def test_bare_dpp_type_falls_back_to_untp() -> None:
    """A payload carrying only the ``DigitalProductPassport`` type
    token (no ``@context``, no ``$schema``, no ``credentialSubject``,
    no ``dppIdentifier`` either) is family-ambiguous. Detection falls
    back to UNTP — preserves pre-Phase-2 behaviour for legacy callers
    that historically defaulted to UNTP.
    """
    data = {"type": "DigitalProductPassport"}
    family, _version = detect_schema(data)
    assert family is SchemaFamily.UNTP
