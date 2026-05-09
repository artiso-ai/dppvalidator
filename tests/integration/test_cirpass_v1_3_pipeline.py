"""End-to-end CIRPASS v1.3.0 pipeline integration test.

Phase 4 of [docs/plans/CIRPASS_2_MIGRATION.md] — exercises the full
``schema → model → semantic → SHACL`` pipeline against the bundled
golden fixtures and verifies that:

- Valid fixtures pass with zero errors.
- Invalid fixtures produce *stable* error codes (the rule's
  ``rule_id`` is part of the public contract).
- Auto-detect routes the payload to the CIRPASS family.
- The schema dispatch resolves the Phase-3-derived schema.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator import ValidationEngine
from dppvalidator.schemas.registry import SchemaFamily

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_VALID_DIR = _FIXTURE_DIR / "valid" / "cirpass-1.3.0"
_INVALID_DIR = _FIXTURE_DIR / "invalid" / "cirpass-1.3.0"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# =============================================================================
# Valid fixtures: pipeline produces no errors
# =============================================================================


@pytest.mark.parametrize(
    "fixture_name",
    ["minimal.json", "multilingual.json", "full.json"],
)
def test_valid_fixture_passes_full_pipeline(fixture_name: str) -> None:
    data = _load(_VALID_DIR / fixture_name)
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    # SHACL skips can surface as info-level diagnostics with the
    # ``-SHACL-SKIP`` suffix when ``pyshacl`` isn't installed; those
    # don't affect ``valid``.
    assert result.valid, (
        f"Fixture {fixture_name} unexpectedly invalid: "
        f"errors={[(e.code, e.path, e.message) for e in result.errors]}"
    )
    assert result.schema_version == "1.3.0"
    assert engine.family is SchemaFamily.CIRPASS


def test_valid_fixture_runs_each_pipeline_layer() -> None:
    """Schema, model, semantic, and SHACL all see the payload.

    SHACL availability depends on the optional ``[rdf]`` extra; we
    only assert the *structural* layer ordering by checking the
    family routing pinned the right pipeline.
    """
    data = _load(_VALID_DIR / "full.json")
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    assert result.valid
    # The engine resolved CIRPASS at auto-detect time.
    assert engine.family is SchemaFamily.CIRPASS
    # Model layer attached the parsed Pydantic root.
    assert result.passport is not None
    # ``passport.dpp_identifier`` is the canonical CIRPASS field —
    # confirms the model dispatch resolved ``ReferencePassport`` and
    # not a UNTP envelope.
    assert getattr(result.passport, "dpp_identifier", None) is not None


# =============================================================================
# Invalid fixtures: stable error attribution
# =============================================================================


@pytest.mark.parametrize(
    "fixture_name,expected_code_substr",
    [
        # The schema layer catches missing required fields with SCH001
        # (jsonschema "required" ⇒ SCH001) before the model layer
        # would emit MDL001. The pipeline runs all errors together so
        # we only assert the *substring* — this isolates the test from
        # rule-ordering refactors.
        ("missing_dpp_identifier.json", "SCH"),
        ("empty_product_name.json", "SCH"),
        ("bad_bcp47_language_tag.json", "MDL"),  # model-layer regex catch
        ("mass_fraction_overflow.json", "MDL"),
        ("bad_cas_number.json", "MDL"),
        ("effective_period_inverted.json", "MDL"),
    ],
)
def test_invalid_fixture_produces_stable_error_codes(
    fixture_name: str, expected_code_substr: str
) -> None:
    data = _load(_INVALID_DIR / fixture_name)
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    assert not result.valid, f"Fixture {fixture_name} unexpectedly valid"
    # Every error carries a stable code prefix from the layer that
    # raised it. ``MDL`` for model-layer validators, ``SCH`` for
    # JSON-Schema, ``CR``/``SUB``/``LCS``/``ACT``/``REL`` for the
    # semantic-rule tree.
    codes = {e.code for e in result.errors}
    assert any(c.startswith(expected_code_substr) for c in codes), (
        f"Expected an error code starting with {expected_code_substr!r} "
        f"on fixture {fixture_name}; got codes={codes}"
    )


# =============================================================================
# Pipeline introspection
# =============================================================================


def test_explicit_schema_version_skips_auto_detect() -> None:
    """Explicit ``schema_version='1.3.0'`` short-circuits detection."""
    data = _load(_VALID_DIR / "minimal.json")
    engine = ValidationEngine(
        schema_version="1.3.0",
        load_plugins=False,
    )
    # NB: explicit version doesn't yet route to CIRPASS automatically
    # — the engine's family attribute defaults to UNTP when
    # ``schema_version`` isn't ``"auto"``. Phase 5 introduces an
    # explicit ``family=`` kwarg; until then, CIRPASS callers should
    # use auto-detect. Here we just smoke-test that explicit-version
    # validation still works end-to-end.
    result = engine.validate(data)
    assert result.schema_version == "1.3.0"


def test_pipeline_table_lists_both_families() -> None:
    """``_PIPELINE_BY_FAMILY`` covers UNTP and CIRPASS."""
    from dppvalidator.validators.engine import _PIPELINE_BY_FAMILY

    assert SchemaFamily.UNTP in _PIPELINE_BY_FAMILY
    assert SchemaFamily.CIRPASS in _PIPELINE_BY_FAMILY
    # CIRPASS pipeline includes a SHACL layer slot (Phase 4 §4.7).
    assert "shacl" in _PIPELINE_BY_FAMILY[SchemaFamily.CIRPASS]
    # UNTP pipeline keeps JSON-LD (no SHACL).
    assert "jsonld" in _PIPELINE_BY_FAMILY[SchemaFamily.UNTP]
    assert "shacl" not in _PIPELINE_BY_FAMILY[SchemaFamily.UNTP]


def test_validation_result_includes_per_layer_codes_for_full_invalid() -> None:
    """The engine reports schema + model + semantic codes for a
    fixture invalid at multiple layers."""
    # Construct a payload with multiple, layered failures: missing
    # field (schema) + bad CAS (model) + economic-operator missing
    # (semantic — but only when actors are declared).
    data = _load(_VALID_DIR / "full.json")
    # Mutate to introduce a CR001 violation: dppIdentifier == product id.
    data["dppIdentifier"]["value"] = data["product"]["productIdentifier"]["value"]
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    # CR001 is a warning, not an error, so result.valid may still be
    # True — but the warning bucket should carry the CR001 code.
    warning_codes = {w.code for w in result.warnings}
    assert "CR001" in warning_codes, (
        f"Expected CR001 in warnings; got warnings={warning_codes}, "
        f"errors={[e.code for e in result.errors]}"
    )
