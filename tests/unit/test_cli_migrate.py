"""CLI tests for ``dppvalidator migrate`` and ``validate --upgrade-from``.

Phase 4 wires the compat shim into two CLI surfaces:

- ``dppvalidator migrate`` writes the upgraded JSON to ``-o`` /
  ``--in-place`` / stdout; refuses to write when warnings fire unless
  ``--accept-warnings`` is set; emits a sidecar ``.warnings.json`` file
  whenever any non-info warning is recorded.
- ``dppvalidator validate --upgrade-from <ver>`` runs the shim before
  validating, surfacing both upgrade warnings and validation issues in
  one report.

These tests exercise both surfaces end-to-end via the public ``main``
entry point, so they double as integration coverage for the dispatch
table and arg-parser wiring.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from dppvalidator.cli.main import main


@pytest.fixture
def v06_payload(tmp_path: Path) -> Path:
    """Write a minimal v0.6 DPP fixture for the CLI to read.

    The fixture intentionally carries an unconditional v0.7-only
    blocking transformation (``Product.registeredId`` → UPG001 lossy)
    so we can exercise the warnings-block path. To exercise the
    no-warnings path, individual tests pop the offending field before
    invoking the CLI.
    """
    data: dict[str, Any] = {
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "id": "https://example.com/credentials/test",
        "name": "Sample DPP",  # Pre-populated to avoid UPG002 from name synthesis.
        "issuer": {"id": "did:example:1", "name": "Example"},
        "validFrom": "2024-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["ProductPassport"],
            "id": "https://example.com/subject/1",
            "product": {
                "type": ["Product"],
                "id": "https://example.com/products/1",
                "name": "Sample",
                "registeredId": "ABN-123",
            },
        },
    }
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# `migrate` command
# ---------------------------------------------------------------------------


class TestMigrateCommand:
    """Acceptance tests for ``dppvalidator migrate``."""

    def test_writes_to_stdout_when_no_output_path(
        self, v06_payload: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Drop the registeredId line so the payload upgrades without
        # blocking warnings (registeredId fires UPG001).
        data = json.loads(v06_payload.read_text())
        data["credentialSubject"]["product"].pop("registeredId", None)
        v06_payload.write_text(json.dumps(data), encoding="utf-8")
        exit_code = main(["migrate", str(v06_payload)])
        captured = capsys.readouterr()
        assert exit_code == 0
        # Stdout should contain serialised JSON of the upgraded payload.
        assert "vocabulary.uncefact.org/untp/0.7" in captured.out

    def test_writes_to_explicit_output_file(self, v06_payload: Path, tmp_path: Path) -> None:
        data = json.loads(v06_payload.read_text())
        data["credentialSubject"]["product"].pop("registeredId", None)
        v06_payload.write_text(json.dumps(data), encoding="utf-8")
        out = tmp_path / "upgraded.json"
        exit_code = main(["migrate", str(v06_payload), "-o", str(out)])
        assert exit_code == 0
        assert out.is_file()
        upgraded = json.loads(out.read_text())
        assert any("vocabulary.uncefact.org/untp/0.7" in c for c in upgraded["@context"])

    def test_in_place_overwrites_input(self, v06_payload: Path) -> None:
        data = json.loads(v06_payload.read_text())
        data["credentialSubject"]["product"].pop("registeredId", None)
        v06_payload.write_text(json.dumps(data), encoding="utf-8")
        exit_code = main(["migrate", str(v06_payload), "--in-place"])
        assert exit_code == 0
        upgraded = json.loads(v06_payload.read_text())
        assert any("vocabulary.uncefact.org/untp/0.7" in c for c in upgraded["@context"])

    def test_in_place_and_output_are_mutually_exclusive(
        self, v06_payload: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "x.json"
        exit_code = main(
            ["migrate", str(v06_payload), "--in-place", "-o", str(out)],
        )
        assert exit_code != 0

    def test_refuses_to_write_when_warnings_fire(self, v06_payload: Path, tmp_path: Path) -> None:
        # The fixture has registeredId → UPG001 (lossy/warning) — without
        # --accept-warnings the command must refuse.
        out = tmp_path / "upgraded.json"
        exit_code = main(["migrate", str(v06_payload), "-o", str(out)])
        assert exit_code == 1
        # Sidecar must always be written when blocking warnings fire.
        sidecar = out.with_suffix(out.suffix + ".warnings.json")
        assert sidecar.is_file(), "sidecar warnings file must be written"
        # Main output file must NOT be written.
        assert not out.is_file()

    def test_accept_warnings_lets_write_proceed(self, v06_payload: Path, tmp_path: Path) -> None:
        out = tmp_path / "upgraded.json"
        exit_code = main(
            ["migrate", str(v06_payload), "-o", str(out), "--accept-warnings"],
        )
        assert exit_code == 0
        assert out.is_file()
        sidecar = out.with_suffix(out.suffix + ".warnings.json")
        assert sidecar.is_file()
        sidecar_data = json.loads(sidecar.read_text())
        assert sidecar_data["schema_version_from"].startswith("0.6")
        assert any(w["code"].startswith("UPG") for w in sidecar_data["warnings"])

    def test_rejects_unknown_source_version(self, v06_payload: Path) -> None:
        exit_code = main(
            ["migrate", str(v06_payload), "--from", "0.5.0"],
        )
        assert exit_code != 0

    def test_missing_input_file_returns_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.json"
        exit_code = main(["migrate", str(missing)])
        assert exit_code != 0

    def test_invalid_json_input_returns_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not json", encoding="utf-8")
        exit_code = main(["migrate", str(bad)])
        assert exit_code != 0

    def test_in_place_with_stdin_is_rejected(
        self,
        monkeypatch: pytest.MonkeyPatch,
        v06_payload: Path,  # noqa: ARG002 — fixture only here for parser order
    ) -> None:
        # ``--in-place`` requires a real file path; ``-`` (stdin) cannot
        # be written back to.
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        exit_code = main(["migrate", "-", "--in-place"])
        assert exit_code != 0

    def test_stdin_input_works(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reading from stdin and writing to stdout is the pipe-friendly path."""
        import io

        payload: dict[str, Any] = {
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "@context": [
                "https://www.w3.org/ns/credentials/v2",
                "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
            ],
            "id": "https://example.com/credentials/test",
            "name": "From stdin",
            "issuer": {"id": "did:example:1", "name": "Example"},
            "validFrom": "2024-01-01T00:00:00Z",
            "credentialSubject": {
                "type": ["ProductPassport"],
                "id": "https://example.com/subject/1",
                "product": {
                    "type": ["Product"],
                    "id": "https://example.com/products/1",
                    "name": "Sample",
                },
            },
        }
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        exit_code = main(["migrate", "-"])
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "vocabulary.uncefact.org/untp/0.7" in captured.out


# ---------------------------------------------------------------------------
# `validate --upgrade-from` flag
# ---------------------------------------------------------------------------


class TestValidateUpgradeFrom:
    """``dppvalidator validate --upgrade-from`` runs the shim then validates."""

    def test_flag_is_accepted(self, v06_payload: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # We don't care about the exit code (the upgraded fixture is
        # likely still invalid against the v0.7 schema due to required
        # fields the shim can't synthesise) — only that the flag is
        # accepted and the shim runs.
        main(
            [
                "validate",
                str(v06_payload),
                "--upgrade-from",
                "0.6.1",
                "--schema-version",
                "0.6.1",  # not the target — we're only sanity-checking flag wiring
            ]
        )
        captured = capsys.readouterr()
        # The upgrade-warnings header should appear in the output.
        assert "Upgrade warnings" in captured.out or "UPG" in captured.out

    def test_no_flag_means_no_shim(
        self, v06_payload: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(
            [
                "validate",
                str(v06_payload),
                "--schema-version",
                "0.6.1",
            ]
        )
        captured = capsys.readouterr()
        assert "Upgrade warnings" not in captured.out
        assert "UPG" not in captured.out
