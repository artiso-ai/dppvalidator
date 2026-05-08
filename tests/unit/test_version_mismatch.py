"""Acceptance tests for the VER001 version-mismatch error.

Phase 3.3 of docs/plans/UNTP_0.7.0_MIGRATION.md introduced VER001 to
prevent the silent field-loss that Pydantic's ``extra='allow'`` setting
would otherwise allow when a payload's declared version doesn't match
the engine's configured version.

Three behaviours under test:

1. **Mismatch is rejected.** Engine configured for ``schema_version=A``
   + payload declaring ``B`` ⇒ single ``VER001`` error and stop. No
   layer-level errors leak through.
2. **Auto-detect is unaffected.** Engine in ``schema_version='auto'``
   mode never raises VER001 — it adopts the declared version.
3. **Unmarked payloads pass through.** Engine configured for any
   version + payload that declares no version (no ``$schema``, no
   versioned UNTP context URL) is trusted, no VER001.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.validators import ValidationEngine

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_V07_SAMPLE = _FIXTURES / "upstream" / "v0.7.0" / "samples" / "DigitalProductPassport_instance.json"
_V06_SAMPLE = _FIXTURES / "valid" / "full_dpp.json"


def _load(path: Path) -> dict:
    if not path.is_file():  # pragma: no cover - vendored in Phase 0
        pytest.skip(f"Vendor {path} via Phase 0 of the migration plan.")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class TestVer001MismatchFailsFast:
    def test_engine_06_rejects_v07_payload_with_VER001(self) -> None:
        sample = _load(_V07_SAMPLE)
        engine = ValidationEngine(
            schema_version="0.6.1",
            layers=["schema", "model", "jsonld"],
            load_plugins=False,
        )
        result = engine.validate(sample)
        assert result.valid is False
        assert len(result.errors) == 1, (
            f"Expected exactly one VER001 error, got "
            f"{[(e.code, e.message[:60]) for e in result.errors]}"
        )
        assert result.errors[0].code == "VER001"
        assert "0.7.0" in result.errors[0].message
        assert "0.6.1" in result.errors[0].message

    def test_engine_07_rejects_v06_payload_with_VER001(self) -> None:
        sample = _load(_V06_SAMPLE)
        engine = ValidationEngine(
            schema_version="0.7.0",
            layers=["schema", "model"],
            load_plugins=False,
        )
        result = engine.validate(sample)
        assert result.valid is False
        codes = [e.code for e in result.errors]
        assert "VER001" in codes
        # And we stopped before any layer ran (so no MDL/SCH errors).
        assert all(c == "VER001" for c in codes)

    def test_VER001_carries_diagnostic_context(self) -> None:
        sample = _load(_V07_SAMPLE)
        engine = ValidationEngine(schema_version="0.6.1", layers=["schema"], load_plugins=False)
        result = engine.validate(sample)
        err = result.errors[0]
        assert err.context is not None
        assert err.context.get("declared_version") == "0.7.0"
        assert err.context.get("configured_version") == "0.6.1"


class TestAutoDetectIgnoresVer001:
    def test_auto_detect_adopts_declared_version_no_VER001(self) -> None:
        sample = _load(_V07_SAMPLE)
        engine = ValidationEngine(
            schema_version="auto",
            layers=["schema", "model", "jsonld"],
            load_plugins=False,
        )
        result = engine.validate(sample)
        # Auto detection should set schema_version to 0.7.0 and validate
        # cleanly — VER001 must not fire.
        assert all(e.code != "VER001" for e in result.errors), (
            f"Unexpected VER001 in auto mode; errors: {[e.code for e in result.errors]}"
        )
        assert result.schema_version == "0.7.0"


class TestUnmarkedPayloadsAccepted:
    def test_payload_with_no_version_marker_does_not_trip_VER001(self) -> None:
        # Strip every version marker (no $schema, no UNTP context URLs).
        sample = {
            "type": ["DigitalProductPassport", "VerifiableCredential"],
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "https://example.com/credentials/dpp-1",
            "issuer": {"id": "did:web:example.com", "name": "Example"},
            "validFrom": "2025-01-01T00:00:00Z",
            "name": "Unmarked",
            "credentialSubject": {},
        }
        engine = ValidationEngine(schema_version="0.7.0", layers=["schema"], load_plugins=False)
        result = engine.validate(sample)
        assert all(e.code != "VER001" for e in result.errors), (
            "VER001 fired on a payload that declares no version — should "
            "trust the user's configuration."
        )
