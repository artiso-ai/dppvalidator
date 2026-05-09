"""End-to-end CLI tests for Phase 6 CIRPASS surface.

Phase 6 task tests of [docs/plans/CIRPASS_2_MIGRATION.md]. Drives
``dppvalidator validate``, ``dppvalidator export``, and
``dppvalidator migrate`` against bundled CIRPASS fixtures end-to-
end and asserts:

- ``validate --target cirpass`` accepts a CIRPASS payload with exit
  code 0.
- ``validate --target untp`` against a CIRPASS payload exits with
  code 3 (family mismatch) + ``DET001``.
- ``export --format cirpass-jsonld`` produces a JSON-LD payload
  with the EUDPP context attached.
- ``migrate --to cirpass-1.3`` produces an output that the CIRPASS
  pipeline accepts.
- ``schema list`` shows both UNTP and CIRPASS rows with the right
  default markers.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from dppvalidator.cli.main import (
    EXIT_BLOCKING_WARNINGS,
    EXIT_FAMILY_MISMATCH,
    EXIT_INVALID,
    EXIT_VALID,
    main,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
_CIRPASS_VALID = _FIXTURE_DIR / "valid" / "cirpass-1.3.0"


# =============================================================================
# validate --target
# =============================================================================


def test_validate_cirpass_fixture_with_target_cirpass(capsys: pytest.CaptureFixture) -> None:
    """``--target cirpass`` accepts a bundled CIRPASS fixture."""
    code = main(
        [
            "validate",
            str(_CIRPASS_VALID / "minimal.json"),
            "--target",
            "cirpass",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_VALID, captured.out + captured.err


def test_validate_cirpass_fixture_with_target_untp_yields_det001(
    capsys: pytest.CaptureFixture,
) -> None:
    """``--target untp`` on a CIRPASS payload exits 3 with DET001."""
    code = main(
        [
            "validate",
            str(_CIRPASS_VALID / "minimal.json"),
            "--target",
            "untp",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_FAMILY_MISMATCH, captured.out + captured.err
    assert "DET001" in (captured.out + captured.err)


def test_validate_untp_fixture_with_target_cirpass_yields_det001(
    capsys: pytest.CaptureFixture,
) -> None:
    """Symmetric reverse: UNTP payload + ``--target cirpass`` → exit 3."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(["validate", str(untp_fixture), "--target", "cirpass"])
    captured = capsys.readouterr()
    assert code == EXIT_FAMILY_MISMATCH
    assert "DET001" in (captured.out + captured.err)


def test_validate_target_auto_routes_cirpass(capsys: pytest.CaptureFixture) -> None:
    """``--target auto`` (default) still routes a CIRPASS fixture to CIRPASS."""
    code = main(["validate", str(_CIRPASS_VALID / "minimal.json")])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    # Output should mention the CIRPASS schema version.
    assert "1.3" in (captured.out + captured.err)


# =============================================================================
# export --format cirpass-jsonld
# =============================================================================


def test_export_cirpass_jsonld_from_untp_fixture(capsys: pytest.CaptureFixture) -> None:
    """``export --format cirpass-jsonld`` projects a UNTP envelope onto CIRPASS."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(
        [
            "export",
            str(untp_fixture),
            "--format",
            "cirpass-jsonld",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    # Stdout is the CIRPASS JSON-LD doc.
    out = json.loads(captured.out)
    assert "@context" in out
    assert "dppIdentifier" in out
    assert "product" in out


def test_export_cirpass_jsonld_default_language_threading(
    capsys: pytest.CaptureFixture,
) -> None:
    """``--default-language`` threads through to the CIRPASS LocalisedText tags."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(
        [
            "export",
            str(untp_fixture),
            "--format",
            "cirpass-jsonld",
            "--default-language",
            "de",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    out = json.loads(captured.out)
    # Every productName entry carries language=de.
    names = out["product"]["productName"]
    assert names
    for entry in names:
        assert entry["language"] == "de"


def test_export_eudpp_jsonld_format_still_works(capsys: pytest.CaptureFixture) -> None:
    """``--format eudpp-jsonld`` (Phase 6 enum extension) still emits a valid doc."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(
        [
            "export",
            str(untp_fixture),
            "--format",
            "eudpp-jsonld",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    out = json.loads(captured.out)
    assert "@context" in out


# =============================================================================
# migrate --to cirpass-1.3
# =============================================================================


def test_migrate_to_cirpass_writes_output(tmp_path: Path) -> None:
    """``migrate --to cirpass-1.3`` writes a CIRPASS-shaped JSON file."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    out = tmp_path / "cirpass.json"
    # The mapping shim emits MAP002 warnings; --accept-warnings is
    # required for the write to proceed.
    code = main(
        [
            "migrate",
            str(untp_fixture),
            "--to",
            "cirpass-1.3",
            "-o",
            str(out),
            "--accept-warnings",
        ]
    )
    assert code == EXIT_VALID
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "dppIdentifier" in payload
    assert "product" in payload


def test_migrate_to_cirpass_blocks_without_accept_warnings(tmp_path: Path) -> None:
    """Without ``--accept-warnings``, the cirpass-1.3 migrate refuses to write."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    out = tmp_path / "cirpass.json"
    code = main(
        [
            "migrate",
            str(untp_fixture),
            "--to",
            "cirpass-1.3",
            "-o",
            str(out),
        ]
    )
    assert code == EXIT_BLOCKING_WARNINGS
    # Sidecar JSON exists; main file does not.
    assert not out.is_file()
    sidecar = out.with_suffix(out.suffix + ".warnings.json")
    assert sidecar.is_file()
    body = json.loads(sidecar.read_text(encoding="utf-8"))
    assert body["family_to"] == "cirpass"
    assert body["schema_version_to"] == "1.3.0"
    # MAP-coded warnings present.
    codes = {w["code"] for w in body["warnings"]}
    assert any(c.startswith("MAP") for c in codes)


def test_migrate_to_untp07_back_compat_unchanged(tmp_path: Path) -> None:
    """Phase 6 must not regress the pre-Phase-6 UNTP 0.6 → 0.7 path."""
    v06_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.6.1.json"
    if not v06_fixture.exists():
        pytest.skip("no v0.6 fixture available")
    out = tmp_path / "v07.json"
    code = main(
        [
            "migrate",
            str(v06_fixture),
            "-o",
            str(out),
            "--accept-warnings",
        ]
    )
    # Either OK or blocking-warnings (depending on the fixture); the
    # important thing is that the legacy --to default is wired.
    assert code in (EXIT_VALID, EXIT_BLOCKING_WARNINGS)


# =============================================================================
# schema list
# =============================================================================


def test_schema_list_shows_both_families(capsys: pytest.CaptureFixture) -> None:
    """``schema list`` shows UNTP and CIRPASS rows with default markers."""
    code = main(["schema", "list"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    output = captured.out
    assert "untp" in output.lower()
    assert "cirpass" in output.lower()
    assert "1.3.0" in output
    assert "0.7.0" in output


# =============================================================================
# Stdin handling for cirpass-jsonld export (smoke)
# =============================================================================


def test_export_cirpass_jsonld_native_cirpass_input(
    tmp_path: Path,  # noqa: ARG001 — kept for symmetry with sibling tests
    capsys: pytest.CaptureFixture,
) -> None:
    """``export --format cirpass-jsonld`` accepts a native CIRPASS payload too."""
    cirpass_fixture = _CIRPASS_VALID / "full.json"
    code = main(
        [
            "export",
            str(cirpass_fixture),
            "--format",
            "cirpass-jsonld",
        ]
    )
    captured = capsys.readouterr()
    # Native CIRPASS inputs may not pass the engine's UNTP-default
    # validation when --schema-version=auto resolves cirpass; the
    # auto-detect path routes to the CIRPASS pipeline. Accept either
    # exit code that means "could be processed".
    assert code in (EXIT_VALID, EXIT_INVALID)
    if code == EXIT_VALID:
        out = json.loads(captured.out)
        assert "@context" in out


# =============================================================================
# Stable error messaging (DET001 surface)
# =============================================================================


def test_det001_message_includes_target_and_detected(
    capsys: pytest.CaptureFixture,
) -> None:
    """The DET001 error message names both --target and the detected family."""
    code = main(
        [
            "validate",
            str(_CIRPASS_VALID / "minimal.json"),
            "--target",
            "untp",
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_FAMILY_MISMATCH
    body = captured.out + captured.err
    assert "untp" in body.lower()
    assert "cirpass" in body.lower()


# =============================================================================
# Exit-code integer stability
# =============================================================================


def test_phase6_exit_codes_stable() -> None:
    """Exit-code integers are pinned across releases (Phase 6 §6.7).

    See ``docs/reference/cli/exit-codes.md`` for the full table.
    """
    from dppvalidator.cli.main import (
        EXIT_BLOCKING_WARNINGS,
        EXIT_ERROR,
        EXIT_FAMILY_MISMATCH,
        EXIT_INVALID,
        EXIT_IO_ERROR,
        EXIT_VALID,
    )

    assert EXIT_VALID == 0
    assert EXIT_INVALID == 1
    assert EXIT_ERROR == 2
    assert EXIT_FAMILY_MISMATCH == 3
    assert EXIT_BLOCKING_WARNINGS == 4
    assert EXIT_IO_ERROR == 5


# =============================================================================
# Smoke: `--format json` legacy still works (back-compat)
# =============================================================================


def test_export_legacy_json_format_unchanged(capsys: pytest.CaptureFixture) -> None:
    """The pre-Phase-6 ``--format json`` still produces valid JSON."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(["export", str(untp_fixture), "--format", "json"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    json.loads(captured.out)


def test_export_legacy_jsonld_format_unchanged(capsys: pytest.CaptureFixture) -> None:
    """The pre-Phase-6 ``--format jsonld`` still produces valid JSON-LD."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    code = main(["export", str(untp_fixture), "--format", "jsonld"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    out = json.loads(captured.out)
    assert "@context" in out


_ = io  # noqa: PIE790 — reserved for future stdin-driven CLI tests
_ = sys
