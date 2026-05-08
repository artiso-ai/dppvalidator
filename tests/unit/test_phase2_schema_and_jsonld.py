"""Phase 2 acceptance tests: schema-only and JSON-LD-only validation of 0.7.0.

This module covers the two exit-criterion checks for Phase 2 of
``docs/plans/UNTP_0.7.0_MIGRATION.md``:

1. The bundled 0.7.0 JSON Schema validates the upstream canonical 0.7.0
   sample with **zero** schema errors. This proves the in-tree
   ``untp-dpp-schema-0.7.0.json`` is byte-equivalent to the upstream and
   does not need ``Product.json`` ($ref-resolution at validate time) — the
   schema is self-contained.

2. The bundled JSON-LD context for 0.7.0 is reachable through
   ``BUNDLED_CONTEXT_URLS`` so JSON-LD expansion works **offline**. The same
   coverage holds retroactively for 0.6.1 (Phase 2 also vendored that
   context to remove the prior implicit network dependency).

Pydantic-model and semantic-rule validation for 0.7.0 are deliberately out
of scope here — they land in Phase 3 / 3b.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.schemas.registry import SCHEMA_REGISTRY
from dppvalidator.validators.jsonld_semantic import BUNDLED_CONTEXT_URLS, JSONLDValidator
from dppvalidator.validators.schema import SchemaValidator

# Vendored upstream samples (Phase 0). Skip individually if any path is
# missing so a partial checkout still runs the rest of the suite.
_UPSTREAM_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "upstream" / "v0.7.0"
_CANONICAL_SAMPLE = _UPSTREAM_DIR / "samples" / "DigitalProductPassport_instance.json"
_BATTERY_SAMPLE = _UPSTREAM_DIR / "samples" / "DigitalProductPassport_battery_instance.json"
_CATHODE_SAMPLE = _UPSTREAM_DIR / "samples" / "DigitalProductPassport_cathode_instance.json"


def _load(path: Path) -> dict:
    if not path.is_file():  # pragma: no cover - vendored in Phase 0
        pytest.skip(
            f"Upstream sample missing at {path}; vendor via Phase 0 of "
            "docs/plans/UNTP_0.7.0_MIGRATION.md.",
        )
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# 1. Schema-only validation (Layer 1)
# ----------------------------------------------------------------------------


class TestSchemaLayerForUntp070:
    """Drive the bundled 0.7.0 JSON Schema against the upstream samples."""

    @pytest.mark.parametrize(
        ("label", "path"),
        [
            ("canonical", _CANONICAL_SAMPLE),
            ("battery", _BATTERY_SAMPLE),
            ("cathode", _CATHODE_SAMPLE),
        ],
    )
    def test_upstream_sample_passes_schema_validation(self, label: str, path: Path) -> None:
        """Every vendored upstream 0.7.0 sample validates against the bundled schema."""
        sample = _load(path)
        validator = SchemaValidator(schema_version="0.7.0")
        result = validator.validate(sample)
        assert result.valid is True, (
            f"Sample {label} failed schema validation with {len(result.errors)} "
            f"error(s); first: {result.errors[0].message if result.errors else '(none)'}"
        )
        assert result.errors == []
        assert result.schema_version == "0.7.0"

    def test_registry_sha_matches_bundled_file(self) -> None:
        """The registry SHA pin matches the on-disk bytes."""
        import hashlib
        from importlib import resources

        schema = SCHEMA_REGISTRY["0.7.0"]
        assert schema.sha256 is not None, "SCHEMA_REGISTRY['0.7.0'].sha256 must be pinned (Phase 2)"
        f = resources.files("dppvalidator.schemas.data").joinpath("untp-dpp-schema-0.7.0.json")
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        assert actual == schema.sha256, (
            f"Bundled 0.7.0 schema SHA mismatch.\n"
            f"  expected: {schema.sha256}\n  actual:   {actual}\n"
            "Re-vendor or update the registry pin."
        )

    def test_bundled_schema_has_expected_top_level_required_fields(self) -> None:
        """0.7.0 makes ``validFrom``, ``name``, ``credentialSubject`` required."""
        validator = SchemaValidator(schema_version="0.7.0")
        schema = validator._load_schema()
        assert set(schema.get("required", [])) >= {
            "@context",
            "id",
            "issuer",
            "validFrom",
            "name",
            "credentialSubject",
        }

    def test_missing_validFrom_now_fails_schema(self) -> None:
        """A 0.7.0 payload missing ``validFrom`` must fail Layer 1."""
        sample = _load(_CANONICAL_SAMPLE)
        broken = {k: v for k, v in sample.items() if k != "validFrom"}
        validator = SchemaValidator(schema_version="0.7.0")
        result = validator.validate(broken)
        assert result.valid is False
        assert any(
            "validFrom" in e.message or e.path.endswith("validFrom") for e in result.errors
        ), f"Expected a validFrom-related error; got: {[e.message for e in result.errors]}"


# ----------------------------------------------------------------------------
# 2. JSON-LD layer offline-readiness (Layer 4)
# ----------------------------------------------------------------------------


class TestJsonLdLayerOffline:
    """The bundled UNTP contexts must satisfy JSON-LD expansion without network."""

    def test_bundled_urls_cover_both_versions(self) -> None:
        """Both the 0.6.1 and 0.7.0 UNTP context URLs are bundled."""
        assert "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/" in BUNDLED_CONTEXT_URLS
        assert "https://vocabulary.uncefact.org/untp/0.7.0/context/" in BUNDLED_CONTEXT_URLS
        # Plus the W3C VC v2 context that was already there pre-Phase 2.
        assert "https://www.w3.org/ns/credentials/v2" in BUNDLED_CONTEXT_URLS

    def test_070_sample_jsonld_expands_with_no_undefined_terms(self) -> None:
        """A real 0.7.0 sample expands cleanly through PyLD using bundled contexts."""
        sample = _load(_CANONICAL_SAMPLE)
        validator = JSONLDValidator(schema_version="0.7.0", strict=False)
        result = validator.validate(sample)
        # JLD001 (missing @context) must NOT fire; JLD002 (undefined term) is
        # advisory in non-strict mode but should not produce errors here.
        assert result.errors == [], (
            f"JSON-LD expansion produced errors: {[(e.code, e.message) for e in result.errors]}"
        )

    def test_070_sample_jsonld_expands_without_network(self, monkeypatch) -> None:
        """Expansion of the canonical 0.7.0 sample must not hit the network.

        We swap PyLD's default document loader with one that raises if it is
        invoked, then run JSON-LD validation through the validator's
        :class:`CachingDocumentLoader` (which pre-populates the cache from
        ``BUNDLED_CONTEXT_URLS``).
        """
        from pyld import jsonld

        sentinel = "NETWORK ACCESS UNEXPECTEDLY ATTEMPTED in JSON-LD layer"

        def _trip(url, options=None):  # noqa: ARG001
            raise RuntimeError(f"{sentinel}: {url}")

        monkeypatch.setattr(jsonld, "get_document_loader", lambda: _trip)

        sample = _load(_CANONICAL_SAMPLE)
        validator = JSONLDValidator(schema_version="0.7.0", strict=False)
        result = validator.validate(sample)
        # If the trip wired in by monkeypatch fired, the failure would surface
        # as a JsonLdError caught and reported as a JLD000-class error. Assert
        # we got a clean (non-erroring) run.
        assert all(sentinel not in e.message for e in result.errors + result.warnings), (
            "Network was hit despite the bundled context being available."
        )
        assert result.errors == [], (
            f"Offline 0.7.0 JSON-LD validation produced unexpected errors: "
            f"{[(e.code, e.message) for e in result.errors]}"
        )

    def test_061_legacy_sample_jsonld_expands_without_network(self, monkeypatch) -> None:
        """Same offline guarantee retroactively holds for the 0.6.1 fixture."""
        from pyld import jsonld

        def _trip(url, options=None):  # noqa: ARG001
            raise RuntimeError(f"NETWORK HIT: {url}")

        monkeypatch.setattr(jsonld, "get_document_loader", lambda: _trip)

        legacy = Path(__file__).resolve().parents[1] / "fixtures" / "valid" / "minimal_dpp.json"
        sample = _load(legacy)
        validator = JSONLDValidator(schema_version="0.6.1", strict=False)
        result = validator.validate(sample)
        assert all("NETWORK HIT" not in e.message for e in result.errors + result.warnings)
