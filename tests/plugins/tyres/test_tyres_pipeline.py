"""Phase 7 — full-pipeline integration test for the tyres plugin.

Runs the bundled ``plugins/tyres/samples/birth.json`` fixture
through the engine end-to-end and asserts the Phase 7 exit
criterion (zero validation errors). Also smoke-tests the CSV
exporter via its registered entry-point.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("dppvalidator_tyres")

from dppvalidator import ValidationEngine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BIRTH_FIXTURE = _REPO_ROOT / "plugins" / "tyres" / "samples" / "birth.json"


def test_birth_fixture_path_exists() -> None:
    """Phase 7 exit-criterion fixture is bundled with the plugin."""
    assert _BIRTH_FIXTURE.is_file()


def test_birth_fixture_validates_with_zero_errors() -> None:
    """Phase 7 exit criterion §1: birth.json returns zero errors.

    > uv run dppvalidator validate plugins/tyres/samples/birth.json
    > returns zero errors against the GDSO Birth v0.9 spec.
    """
    data = json.loads(_BIRTH_FIXTURE.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    # The fixture is well-formed for the TYR plugin's checks; any
    # *errors* originate from base-engine layers and would be
    # genuine bugs.
    error_codes = sorted({e.code for e in result.errors})
    assert not result.errors, (
        f"Birth fixture produced unexpected errors: {error_codes} — "
        f"first error: {result.errors[0].path}: {result.errors[0].message}"
    )


def test_tyr_plugin_validators_discoverable() -> None:
    """All eight TYR rules surface via the plugin discovery API."""
    from dppvalidator.plugins.discovery import list_available_plugins

    available = list_available_plugins()
    validators = set(available.get("validators", []))
    expected = {
        "tyr001_dot_marking",
        "tyr002_birth_chain",
        "tyr003_load_index",
        "tyr004_speed_rating",
        "tyr005_section_width",
        "tyr006_retread_provenance",
        "tyr007_collection_actor",
        "tyr008_recycling_method",
    }
    assert expected <= validators, (
        f"Missing TYR validators in plugin discovery: {expected - validators}"
    )


def test_tyr_plugin_exporter_discoverable() -> None:
    """The CSV exporter is registered under ``dppvalidator.exporters``."""
    from dppvalidator.plugins.discovery import list_available_plugins

    available = list_available_plugins()
    exporters = set(available.get("exporters", []))
    assert "tyres_lifecycle_csv" in exporters


def test_tyr_rules_run_against_birth_fixture() -> None:
    """The plugin layer wires the TYR rules into the engine pipeline."""
    data = json.loads(_BIRTH_FIXTURE.read_text(encoding="utf-8"))
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    # Inspect the plugin layer's diagnostic output: TYR rules ran
    # against the passport (no errors, but the plugin layer was
    # consulted).
    all_codes = {e.code for e in (*result.errors, *result.warnings, *result.info)}
    # A clean birth fixture won't fire any TYR rule, but the
    # plugin layer must have *executed* (we can't directly observe
    # this; instead pin the contract that no rule misfires).
    tyr_codes = {c for c in all_codes if c.startswith("TYR")}
    assert tyr_codes == set(), f"Birth fixture unexpectedly fired TYR rules: {tyr_codes}"


def test_tyr_rules_fire_on_broken_fixture(tmp_path: Path) -> None:
    """When the fixture has malformed tyre data, TYR rules fire."""
    data = json.loads(_BIRTH_FIXTURE.read_text(encoding="utf-8"))
    # Strip the DOT marking → TYR001 must fire.
    history = data["credentialSubject"]["extensions"]["tyreLifecycleHistory"]
    del history["birth"]["dotMarking"]
    engine = ValidationEngine(schema_version="auto")
    result = engine.validate(data)
    fired_codes = {
        e.code for e in (*result.errors, *result.warnings, *result.info) if e.code.startswith("TYR")
    }
    assert "TYR001" in fired_codes, (
        f"Expected TYR001 when DOT marking is missing; got {fired_codes}"
    )
    # Avoid unused-arg warning.
    _ = tmp_path


# =============================================================================
# CSV exporter smoke test
# =============================================================================


def test_csv_exporter_flattens_birth_fixture() -> None:
    """The CSV exporter produces a header row + one Birth row."""
    from dppvalidator_tyres.exporters import TyreLifecycleCSVExporter

    data = json.loads(_BIRTH_FIXTURE.read_text(encoding="utf-8"))
    # Build a dict-shaped passport stub the exporter can walk.

    class _Subject:
        def __init__(self) -> None:
            self.extensions = data["credentialSubject"]["extensions"]

    class _Passport:
        def __init__(self) -> None:
            self.credential_subject = _Subject()

    csv_text = TyreLifecycleCSVExporter().export(_Passport())
    lines = csv_text.strip().splitlines()
    assert lines[0].split(",")[0] == "tyreUuid"
    # The fixture has one Birth + zero events, so 2 lines (header + 1).
    assert len(lines) == 2
    # Birth row has the expected actor name.
    assert "ACME Tyres" in lines[1]
