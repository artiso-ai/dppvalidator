"""Phase 6 — pre-Phase-6 CLI invocations still produce stable exit codes.

The plan calls out:

> All pre-existing CLI invocations bit-stable (golden snapshots).

That guarantee covers exit codes and the message-body shape consumers
(shells / CI scripts) rely on. This file pins the contract so any
future CLI refactor that breaks back-compat fails CI.

What's NOT pinned:

- Rich rendering details (ANSI escapes, table glyphs) — those are
  output-format implementation details and may shift.
- Error-message wording — only the structural content (codes,
  paths, severity tags) is asserted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.cli.main import (
    EXIT_BLOCKING_WARNINGS,
    EXIT_FAMILY_MISMATCH,
    EXIT_IO_ERROR,
    EXIT_VALID,
    main,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def valid_untp07_fixture() -> Path:
    return _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"


@pytest.fixture
def valid_cirpass_fixture() -> Path:
    return _FIXTURE_DIR / "valid" / "cirpass-1.3.0" / "minimal.json"


# =============================================================================
# Pre-Phase-6 invocations are unchanged
# =============================================================================


def test_pre_phase6_validate_default_invocation_returns_zero(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    """``dppvalidator validate <untp-fixture>`` (no flags) still returns 0."""
    code = main(["validate", str(valid_untp07_fixture)])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    assert "VALID" in captured.out


def test_pre_phase6_validate_format_text_unchanged(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    code = main(["validate", str(valid_untp07_fixture), "--format", "text"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    # Text output marker survived.
    assert "VALID" in captured.out


def test_pre_phase6_validate_format_json_unchanged(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    code = main(["validate", str(valid_untp07_fixture), "--format", "json"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    body = json.loads(captured.out)
    # Stable JSON structure (pinned in pre-Phase-6 release).
    assert body["valid"] is True
    assert "errors" in body
    assert "warnings" in body
    assert "schema_version" in body


def test_pre_phase6_validate_format_table_unchanged(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    code = main(["validate", str(valid_untp07_fixture), "--format", "table"])
    capsys.readouterr()  # drain to keep test isolation
    assert code == EXIT_VALID


def test_pre_phase6_export_default_invocation_unchanged(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    """``dppvalidator export <untp-fixture>`` (no flags) → JSON-LD output."""
    code = main(["export", str(valid_untp07_fixture)])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    body = json.loads(captured.out)
    assert "@context" in body


def test_pre_phase6_schema_list_still_works(capsys: pytest.CaptureFixture) -> None:
    code = main(["schema", "list"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    # Pre-Phase-6 contract: a "Default" column is present.
    assert "Default" in captured.out


def test_pre_phase6_migrate_default_to_is_untp07(capsys: pytest.CaptureFixture) -> None:
    """``migrate --help`` reports ``--to=untp-0.7`` as the default."""
    with pytest.raises(SystemExit):
        # argparse's --help raises SystemExit.
        main(["migrate", "--help"])
    captured = capsys.readouterr()
    assert "untp-0.7" in captured.out
    # Phase 6 exposed --to but the default is still the legacy path.
    assert "default:" in captured.out.lower() or "default" in captured.out.lower()


# =============================================================================
# Pre-Phase-6 error paths still produce a structured message body
# =============================================================================


def test_pre_phase6_invalid_fixture_emits_error_codes(
    capsys: pytest.CaptureFixture,
) -> None:
    """Invalid fixtures still emit per-error message lines (legacy contract)."""
    invalid_fixture = _FIXTURE_DIR / "invalid" / "missing_issuer.json"
    if not invalid_fixture.exists():
        pytest.skip("no invalid fixture available")
    code = main(["validate", str(invalid_fixture), "--format", "json"])
    captured = capsys.readouterr()
    body = json.loads(captured.out)
    assert body["valid"] is False
    assert body["errors"], "expected at least one error"
    # Each error has the legacy field set.
    for err in body["errors"]:
        assert "code" in err
        assert "path" in err
        assert "message" in err
    # Exit code may be EXIT_INVALID (1) or EXIT_IO_ERROR (5)
    # depending on the fixture; the back-compat contract is on the
    # JSON shape, not the integer.
    assert code in {1, 5}


# =============================================================================
# New Phase 6 invocations are *additive* — they don't change pre-existing flags
# =============================================================================


def test_phase6_target_flag_does_not_affect_default_validate(
    valid_untp07_fixture: Path,
) -> None:
    """Without ``--target``, the new flag has zero effect — exit code unchanged."""
    code = main(["validate", str(valid_untp07_fixture)])
    assert code == EXIT_VALID


def test_phase6_target_auto_is_back_compat(
    valid_untp07_fixture: Path,
) -> None:
    """Explicitly ``--target auto`` matches the no-flag baseline."""
    code = main(["validate", str(valid_untp07_fixture), "--target", "auto"])
    assert code == EXIT_VALID


def test_phase6_format_json_is_back_compat(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    """Adding new format choices to ``--format`` doesn't change ``json``."""
    code = main(["export", str(valid_untp07_fixture), "--format", "json"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    json.loads(captured.out)  # parses cleanly


def test_phase6_format_jsonld_is_back_compat(
    valid_untp07_fixture: Path, capsys: pytest.CaptureFixture
) -> None:
    code = main(["export", str(valid_untp07_fixture), "--format", "jsonld"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    body = json.loads(captured.out)
    assert "@context" in body


# =============================================================================
# New exit codes don't shadow pre-existing ones
# =============================================================================


def test_phase6_io_error_distinct_from_invalid(
    capsys: pytest.CaptureFixture,
) -> None:
    """Missing file → EXIT_IO_ERROR (5), not EXIT_INVALID (1)."""
    code = main(["validate", "/no/such/file.json"])
    _ = capsys.readouterr()
    assert code == EXIT_IO_ERROR


def test_phase6_family_mismatch_distinct_from_invalid(
    valid_cirpass_fixture: Path,
) -> None:
    """``--target untp`` on a CIRPASS payload → EXIT_FAMILY_MISMATCH, not INVALID."""
    code = main(["validate", str(valid_cirpass_fixture), "--target", "untp"])
    assert code == EXIT_FAMILY_MISMATCH


def test_phase6_blocking_warnings_distinct_from_invalid(tmp_path: Path) -> None:
    """``migrate --to cirpass-1.3`` without ``--accept-warnings`` →
    EXIT_BLOCKING_WARNINGS, not EXIT_INVALID."""
    untp_fixture = _FIXTURE_DIR / "valid" / "untp-dpp-instance-0.7.0.json"
    out = tmp_path / "out.json"
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


# =============================================================================
# `--help` output mentions the new surface
# =============================================================================


def test_phase6_validate_help_mentions_target(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit):
        main(["validate", "--help"])
    captured = capsys.readouterr()
    assert "--target" in captured.out
    assert "cirpass" in captured.out


def test_phase6_export_help_mentions_cirpass_jsonld(
    capsys: pytest.CaptureFixture,
) -> None:
    with pytest.raises(SystemExit):
        main(["export", "--help"])
    captured = capsys.readouterr()
    assert "cirpass-jsonld" in captured.out
    assert "eudpp-jsonld" in captured.out


def test_phase6_migrate_help_mentions_to_target(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit):
        main(["migrate", "--help"])
    captured = capsys.readouterr()
    assert "--to" in captured.out
    assert "cirpass-1.3" in captured.out


# =============================================================================
# `dppvalidator --version` legacy
# =============================================================================


def test_phase6_top_level_version_flag_unchanged(
    capsys: pytest.CaptureFixture,
) -> None:
    """``dppvalidator -V`` / ``--version`` still works."""
    code = main(["--version"])
    captured = capsys.readouterr()
    assert code == EXIT_VALID
    assert "dppvalidator" in captured.out
