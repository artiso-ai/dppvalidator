"""Cross-check the production-mirror URL split for UNTP DPP schemas.

Polish step A from the post-Phase-6 review: ``SchemaVersion`` now
carries a ``production_url`` field for the canonical
``untp.unece.org`` hosting alongside the SHA-pinned ``url``. This
module pins the new contract so a future refactor doesn't silently
drop the production link.

Pins:

1. ``SchemaVersion.production_url`` is exposed as a frozen-dataclass
   attribute and defaults to ``None`` when not set.
2. ``SchemaRegistry.get_production_url(version)`` returns the
   registry's recorded production URL or ``None``.
3. The 0.7.0 entry has a non-``None`` production URL pointing at
   ``untp.unece.org``.
4. The ``production_url`` recorded in MANIFEST.json (under the
   ``untp-dpp-schema@0.7.0`` artefact) matches the registry entry —
   the two surfaces must not drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.schemas.registry import (
    SCHEMA_REGISTRY,
    SchemaRegistry,
    SchemaVersion,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_PATH = _REPO_ROOT / "src" / "dppvalidator" / "schemas" / "data" / "MANIFEST.json"
_EXPECTED_V07_PRODUCTION_URL = (
    "https://untp.unece.org/artefacts/schema/v0.7.0/dpp/DigitalProductPassport.json"
)


# ---------------------------------------------------------------------------
# 1. Dataclass shape
# ---------------------------------------------------------------------------


class TestSchemaVersionProductionUrlField:
    """``SchemaVersion`` exposes ``production_url`` as a public attribute."""

    def test_production_url_defaults_to_none(self) -> None:
        sv = SchemaVersion(
            version="9.9.9",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=("https://www.w3.org/ns/credentials/v2",),
        )
        assert sv.production_url is None

    def test_production_url_can_be_set(self) -> None:
        sv = SchemaVersion(
            version="9.9.9",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=("https://www.w3.org/ns/credentials/v2",),
            production_url="https://prod.example.com/schema.json",
        )
        assert sv.production_url == "https://prod.example.com/schema.json"

    def test_production_url_field_is_frozen(self) -> None:
        """The dataclass is frozen — assignment must raise."""
        from dataclasses import FrozenInstanceError

        sv = SchemaVersion(
            version="9.9.9",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=("https://www.w3.org/ns/credentials/v2",),
        )
        with pytest.raises(FrozenInstanceError):
            sv.production_url = "https://other.example.com/schema.json"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. Registry accessor
# ---------------------------------------------------------------------------


class TestRegistryGetProductionUrl:
    """``SchemaRegistry.get_production_url`` exposes the field."""

    def test_returns_url_for_v07(self) -> None:
        registry = SchemaRegistry()
        url = registry.get_production_url("0.7.0")
        assert url == _EXPECTED_V07_PRODUCTION_URL

    def test_returns_none_for_versions_without_production_url(self) -> None:
        # 0.6.0 and 0.6.1 don't currently carry a production URL — the
        # accessor should report None rather than raise.
        registry = SchemaRegistry()
        assert registry.get_production_url("0.6.0") is None
        assert registry.get_production_url("0.6.1") is None

    def test_unknown_version_raises(self) -> None:
        registry = SchemaRegistry()
        with pytest.raises(ValueError, match="Unknown schema version"):
            registry.get_production_url("9.9.9")


# ---------------------------------------------------------------------------
# 3. v0.7.0 entry in the registry table
# ---------------------------------------------------------------------------


class TestV07ProductionUrlContent:
    """The 0.7.0 entry's production URL points at the right host."""

    def test_registry_v07_production_url_matches_expected(self) -> None:
        entry = SCHEMA_REGISTRY["0.7.0"]
        assert entry.production_url == _EXPECTED_V07_PRODUCTION_URL

    def test_registry_v07_production_url_is_not_the_source_url(self) -> None:
        """Production URL is distinct from SHA-pinned source URL.

        The whole point of the field is to record provenance separately
        from integrity. Collapsing both into the same string would
        defeat the abstraction.
        """
        entry = SCHEMA_REGISTRY["0.7.0"]
        assert entry.production_url != entry.url


# ---------------------------------------------------------------------------
# 4. MANIFEST ↔ registry agreement
# ---------------------------------------------------------------------------


class TestManifestRegistryAgreement:
    """``production_url`` recorded in MANIFEST matches the registry entry.

    The two surfaces document the same fact ("where does this artefact
    live in production?") and must not drift. CI catches drift
    immediately rather than letting one fall stale unnoticed.
    """

    def test_v07_dpp_schema_manifest_carries_production_url(self) -> None:
        manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        v07_entry = next(
            entry
            for entry in manifest["artefacts"]
            if entry["kind"] == "untp-dpp-schema" and entry["version"] == "0.7.0"
        )
        assert v07_entry.get("production_url") == _EXPECTED_V07_PRODUCTION_URL

    def test_v07_dpp_schema_manifest_and_registry_agree(self) -> None:
        manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        v07_entry = next(
            entry
            for entry in manifest["artefacts"]
            if entry["kind"] == "untp-dpp-schema" and entry["version"] == "0.7.0"
        )
        registry_entry = SCHEMA_REGISTRY["0.7.0"]
        assert v07_entry["production_url"] == registry_entry.production_url
