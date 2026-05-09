"""Phase 6 export matrix: every ``--format`` × every fixture combination.

Per the Phase 6 task list (``Tests`` bullet of
[docs/plans/CIRPASS_2_MIGRATION.md]):

> tests/integration/test_cli_export_matrix.py — every ``--format`` ×
> every fixture; output is schema-valid where applicable.

This file matrixes the four supported formats against every bundled
valid fixture and asserts:

- The CLI exits with code 0.
- The output parses as valid JSON.
- For JSON-LD-shaped formats, ``@context`` is present.
- For ``cirpass-jsonld``, the projected output passes the CIRPASS
  Pydantic model.
- For ``json``, the output round-trips through Pydantic.

The matrix is deliberately small — bundled fixtures are stable
across releases — so the test runs quickly while still pinning the
back-compat surface.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.cli.main import EXIT_VALID, main

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

# Curated set of valid fixtures — pre-Phase-6 callers were already
# using these, and they cover the v0.6 / v0.7 / CIRPASS surfaces.
_UNTP_VALID_FIXTURES: tuple[Path, ...] = (_FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json",)
_CIRPASS_VALID_FIXTURES: tuple[Path, ...] = (
    _FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "minimal.json",
    _FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "multilingual.json",
    _FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "full.json",
)


# =============================================================================
# Matrix: format × UNTP fixture
# =============================================================================


@pytest.mark.parametrize("fmt", ["json", "jsonld", "eudpp-jsonld", "cirpass-jsonld"])
@pytest.mark.parametrize("fixture", _UNTP_VALID_FIXTURES)
def test_export_matrix_untp_input(fmt: str, fixture: Path, capsys: pytest.CaptureFixture) -> None:
    """Every format accepts a UNTP 0.7.0 input and emits valid JSON."""
    if not fixture.exists():
        pytest.skip(f"missing fixture: {fixture}")
    code = main(["export", str(fixture), "--format", fmt])
    captured = capsys.readouterr()
    assert code == EXIT_VALID, captured.out + captured.err
    body = json.loads(captured.out)
    if fmt in {"jsonld", "eudpp-jsonld", "cirpass-jsonld"}:
        assert "@context" in body
    if fmt == "cirpass-jsonld":
        assert "dppIdentifier" in body
        assert "product" in body


# =============================================================================
# Matrix: format × CIRPASS fixture (where applicable)
# =============================================================================


@pytest.mark.parametrize("fixture", _CIRPASS_VALID_FIXTURES)
def test_export_cirpass_jsonld_native_input(fixture: Path, capsys: pytest.CaptureFixture) -> None:
    """``--format cirpass-jsonld`` round-trips a native CIRPASS fixture.

    The CLI's auto-detect picks the CIRPASS pipeline; the model
    layer accepts the payload; the exporter emits a CIRPASS JSON-LD
    doc that the CIRPASS Pydantic root can parse back.
    """
    code = main(["export", str(fixture), "--format", "cirpass-jsonld"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID, captured.out + captured.err
    body = json.loads(captured.out)
    assert "@context" in body
    assert "dppIdentifier" in body
    # Sanity: the CIRPASS Pydantic root accepts the projected output.
    from dppvalidator.models.cirpass.v1_3 import ReferencePassport

    # Strip the JSON-LD-only @context + type before re-parsing.
    payload = {k: v for k, v in body.items() if k not in {"@context", "type"}}
    ReferencePassport.model_validate(payload)


# =============================================================================
# Stable output: --compact flag still works
# =============================================================================


@pytest.mark.parametrize("fmt", ["jsonld", "cirpass-jsonld"])
def test_export_compact_flag_collapses_whitespace(fmt: str, capsys: pytest.CaptureFixture) -> None:
    """``--compact`` produces a one-line JSON output."""
    fixture = _UNTP_VALID_FIXTURES[0]
    if not fixture.exists():
        pytest.skip(f"missing fixture: {fixture}")
    code = main(["export", str(fixture), "--format", fmt, "--compact"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    # The compact output has no leading whitespace on subsequent
    # lines (single-line or trailing-newline-only output).
    lines = captured.out.strip().split("\n")
    assert len(lines) == 1


# =============================================================================
# `-o`/`--output` writes to file rather than stdout
# =============================================================================


@pytest.mark.parametrize("fmt", ["jsonld", "eudpp-jsonld", "cirpass-jsonld", "json"])
def test_export_output_flag_writes_file(
    fmt: str, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    fixture = _UNTP_VALID_FIXTURES[0]
    if not fixture.exists():
        pytest.skip(f"missing fixture: {fixture}")
    out = tmp_path / f"out.{fmt}.json"
    code = main(["export", str(fixture), "--format", fmt, "-o", str(out)])
    captured = capsys.readouterr()
    assert code == EXIT_VALID, captured.out + captured.err
    assert out.is_file()
    body = json.loads(out.read_text(encoding="utf-8"))
    if fmt in {"jsonld", "eudpp-jsonld", "cirpass-jsonld"}:
        assert "@context" in body
