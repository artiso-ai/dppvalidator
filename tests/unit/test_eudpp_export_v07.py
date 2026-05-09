"""Phase 3c acceptance tests: v0.7 EU DPP JSON-LD export.

This module covers the exporter half of Phase 3c (see
``docs/plans/UNTP_0.7.0_MIGRATION.md``):

1. :class:`EUDPPTermMapper` indexes the right column per version.
2. :class:`EUDPPJsonLDExporter` auto-detects the source UNTP version from
   the passport class's module path, and an explicit ``schema_version``
   override takes precedence.
3. v0.7 round-trip: a v0.7 sample exports to EU DPP JSON-LD with v0.7
   spellings (``itemNumber``, ``materialProvenance``, ``idGranularity``)
   correctly mapped to the same EU DPP URIs as their v0.6 counterparts.
4. ``gtin`` does not appear in the v0.7 export (correctly removed).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.exporters.eudpp_jsonld import (
    EUDPPJsonLDExporter,
    EUDPPTermMapper,
    export_eudpp_jsonld_dict,
    get_term_mapping_summary,
    validate_eudpp_export,
)
from dppvalidator.models import v0_7
from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION

_UPSTREAM_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "upstream" / "v0.7.0"


def _load_canonical() -> dict:
    p = _UPSTREAM_DIR / "samples" / "DigitalProductPassport_instance.json"
    if not p.is_file():  # pragma: no cover — vendored in Phase 0
        pytest.skip(f"Upstream sample missing: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def passport_v07() -> v0_7.DigitalProductPassport:
    return v0_7.DigitalProductPassport.model_validate(_load_canonical())


# ---------------------------------------------------------------------------
# 1. EUDPPTermMapper picks the right column
# ---------------------------------------------------------------------------


class TestEudppTermMapperPerVersion:
    """The mapper indexes the correct UNTP spellings per version."""

    def test_v06_mapper_uses_canonical_spellings(self) -> None:
        mapper = EUDPPTermMapper(schema_version="0.6.1")
        assert mapper.map_key("serialNumber") == "uniqueProductIdentifier"
        assert mapper.map_key("granularityLevel") == "granularity"
        assert mapper.map_key("producedByParty") == "hasManufacturer"
        assert mapper.map_key("gtin") == "GTIN"

    def test_v07_mapper_uses_renamed_spellings(self) -> None:
        mapper = EUDPPTermMapper(schema_version="0.7.0")
        assert mapper.map_key("itemNumber") == "uniqueProductIdentifier"
        assert mapper.map_key("idGranularity") == "granularity"
        assert mapper.map_key("relatedParty") == "hasManufacturer"
        assert mapper.map_key("materialProvenance") == "hasMaterialProvenance"
        assert mapper.map_key("performanceClaim") == "hasPerformanceClaim"

    def test_v07_mapper_does_not_recognise_v06_only_terms(self) -> None:
        """v0.6-only terms (renamed in v0.7) don't resolve under the v0.7 mapper.

        ``map_key`` returns the input unchanged when the term isn't in the
        mapper's index — that's the documented "passthrough" behaviour.
        """
        mapper = EUDPPTermMapper(schema_version="0.7.0")
        # ``serialNumber`` is the v0.6 spelling; v0.7 says ``itemNumber``.
        assert mapper.map_key("serialNumber") == "serialNumber"
        assert mapper.map_key("granularityLevel") == "granularityLevel"
        assert mapper.map_key("materialsProvenance") == "materialsProvenance"

    def test_v07_mapper_omits_gtin(self) -> None:
        """``gtin`` is removed in v0.7 → must not appear in the index."""
        mapper = EUDPPTermMapper(schema_version="0.7.0")
        assert "gtin" not in mapper.mapped_keys

    def test_default_construction_matches_default_version(self) -> None:
        """Constructing without args uses :data:`DEFAULT_SCHEMA_VERSION`."""
        m = EUDPPTermMapper()
        assert m.schema_version == DEFAULT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# 2. EUDPPJsonLDExporter — explicit version + auto-detect
# ---------------------------------------------------------------------------


class TestExporterVersionDispatch:
    """``EUDPPJsonLDExporter`` resolves the right mapper per call."""

    def test_explicit_version_uses_pinned_mapper(
        self, passport_v07: v0_7.DigitalProductPassport
    ) -> None:
        exporter = EUDPPJsonLDExporter(schema_version="0.7.0")
        assert exporter.schema_version == "0.7.0"
        result = exporter.export_dict(passport_v07)
        assert "credentialSubject" in result

    def test_auto_detect_v07_from_module_path(
        self, passport_v07: v0_7.DigitalProductPassport
    ) -> None:
        """A v0.7 passport auto-detects to the v0.7 mapper without explicit configuration."""
        exporter = EUDPPJsonLDExporter()
        assert exporter.schema_version is None  # not pinned
        # Internal helper exposes the auto-detection result.
        assert exporter._detect_version_from_passport(passport_v07) == "0.7.0"

    def test_auto_detect_unknown_falls_back_to_default(self) -> None:
        """Passports outside the in-tree v0_X namespaces fall back to the default."""

        class _Outsider:
            credential_subject = None

        exporter = EUDPPJsonLDExporter()
        assert (
            exporter._detect_version_from_passport(_Outsider())  # type: ignore[arg-type]
            == DEFAULT_SCHEMA_VERSION
        )

    def test_explicit_version_overrides_auto_detect(
        self, passport_v07: v0_7.DigitalProductPassport
    ) -> None:
        """An explicit ``schema_version='0.6.1'`` on a v0.7 passport overrides auto-detect.

        This is intentional — it lets callers force-export through the v0.6
        mapper for testing or downstream-compat scenarios.
        """
        exporter = EUDPPJsonLDExporter(schema_version="0.6.1")
        result = exporter.export_dict(passport_v07)
        # The exporter pins to v0.6, so v0.7-only spellings (``itemNumber``,
        # ``materialProvenance``, …) wouldn't be in the v0.6 index and pass
        # through unchanged. Sanity-check that it didn't crash.
        assert "credentialSubject" in result


# ---------------------------------------------------------------------------
# 3. v0.7 round-trip: spellings map to expected EU DPP URIs
# ---------------------------------------------------------------------------


class TestV07ExportRoundtrip:
    """Full v0.7 export produces a JSON-LD doc with EU DPP terms."""

    def test_v07_passport_exports_cleanly(self, passport_v07: v0_7.DigitalProductPassport) -> None:
        result = export_eudpp_jsonld_dict(passport_v07)
        # Validates as an EU DPP export (has @context, type, etc.).
        issues = validate_eudpp_export(result)
        assert issues == [], f"Unexpected validation issues: {issues}"

    def test_v07_renames_are_mapped(self, passport_v07: v0_7.DigitalProductPassport) -> None:
        """v0.7 spellings on the source side land at the right EU DPP keys.

        The canonical 0.7.0 sample doesn't include every renamed field, but
        it has ``materialProvenance``, ``idGranularity``, ``relatedParty``
        which all flow through.
        """
        result = export_eudpp_jsonld_dict(passport_v07)
        cs = result.get("credentialSubject")
        assert isinstance(cs, dict)
        # ``materialProvenance`` (v0.7) → ``hasMaterialProvenance`` (EU DPP)
        assert "hasMaterialProvenance" in cs
        # ``relatedParty`` (v0.7) → ``hasManufacturer`` (EU DPP)
        assert "hasManufacturer" in cs
        # ``idGranularity`` (v0.7) is also surfaced at the document root via
        # the metadata helper.
        assert result.get("granularity") == cs.get("granularity")

    def test_v07_export_does_not_carry_v06_only_fields(
        self, passport_v07: v0_7.DigitalProductPassport
    ) -> None:
        """v0.7 source has no ``gtin``, ``serialNumber``, ``materialsProvenance`` keys."""
        result = export_eudpp_jsonld_dict(passport_v07)
        cs = result.get("credentialSubject", {})
        # These are v0.6-only field names. Even before mapping, they shouldn't
        # be present on a v0.7 source.
        for v06_only in ("gtin", "serialNumber", "materialsProvenance"):
            assert v06_only not in cs, f"v0.6-only field {v06_only!r} leaked into v0.7 export"

    def test_v07_export_uses_eudpp_namespace_in_type(
        self, passport_v07: v0_7.DigitalProductPassport
    ) -> None:
        result = export_eudpp_jsonld_dict(passport_v07)
        type_arr = result.get("type")
        assert isinstance(type_arr, list)
        assert "eudpp:DPP" in type_arr


# ---------------------------------------------------------------------------
# 4. get_term_mapping_summary per version
# ---------------------------------------------------------------------------


class TestTermMappingSummaryPerVersion:
    """The summary helper takes a version and reflects the right column."""

    def test_v06_summary_includes_legacy_terms(self) -> None:
        summary = get_term_mapping_summary("0.6.1")
        assert summary.get("serialNumber") == "uniqueProductIdentifier"
        assert summary.get("granularityLevel") == "granularity"
        assert summary.get("gtin") == "GTIN"

    def test_v07_summary_uses_renamed_terms(self) -> None:
        summary = get_term_mapping_summary("0.7.0")
        assert summary.get("itemNumber") == "uniqueProductIdentifier"
        assert summary.get("idGranularity") == "granularity"
        assert summary.get("relatedParty") == "hasManufacturer"
        assert "gtin" not in summary
        assert "serialNumber" not in summary

    def test_default_summary_is_default_version(self) -> None:
        """Default invocation returns :data:`DEFAULT_SCHEMA_VERSION`'s view."""
        default = get_term_mapping_summary()
        # Same as the explicit default-version call.
        assert default == get_term_mapping_summary(DEFAULT_SCHEMA_VERSION)
