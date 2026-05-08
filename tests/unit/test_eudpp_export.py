"""Tests for EU DPP JSON-LD export (Phase 9)."""

import json

import pytest

from dppvalidator.exporters.eudpp_jsonld import (
    EUDPP_CONTEXT_URL,
    EUDPPJsonLDExporter,
    EUDPPTermMapper,
    export_eudpp_jsonld,
    export_eudpp_jsonld_dict,
    get_eudpp_jsonld_context,
    get_term_mapping_summary,
    validate_eudpp_export,
)
from dppvalidator.vocabularies.ontology import EUDPPNamespace


class TestEUDPPTermMapper:
    """Tests for EUDPPTermMapper class."""

    def test_create_mapper(self):
        """Test creating a term mapper."""
        mapper = EUDPPTermMapper()
        assert mapper is not None

    def test_map_key_known(self):
        """Test mapping known UNTP keys."""
        mapper = EUDPPTermMapper()

        # Test known mappings
        assert mapper.map_key("id") == "uniqueDPPID"
        assert mapper.map_key("Product") == "Product"
        assert mapper.map_key("validFrom") == "validFrom"

    def test_map_key_unknown(self):
        """Test mapping unknown keys returns original."""
        mapper = EUDPPTermMapper()

        assert mapper.map_key("unknownKey") == "unknownKey"
        assert mapper.map_key("customField") == "customField"

    def test_map_type(self):
        """Test mapping type values."""
        mapper = EUDPPTermMapper()

        # Known types get eudpp: prefix
        result = mapper.map_type("DigitalProductPassport")
        assert result == "eudpp:DPP"

        result = mapper.map_type("Product")
        assert result == "eudpp:Product"

    def test_map_type_unknown(self):
        """Test unknown types are returned unchanged."""
        mapper = EUDPPTermMapper()

        result = mapper.map_type("UnknownType")
        assert result == "UnknownType"

    def test_get_eudpp_key(self):
        """Test getting EU DPP key for UNTP key."""
        mapper = EUDPPTermMapper()

        assert mapper.get_eudpp_key("id") == "uniqueDPPID"
        assert mapper.get_eudpp_key("unknownKey") is None

    def test_mapped_keys_list(self):
        """Test getting list of mapped keys."""
        mapper = EUDPPTermMapper()

        keys = mapper.mapped_keys
        assert isinstance(keys, list)
        assert len(keys) > 0
        assert "id" in keys
        assert "Product" in keys


class TestEUDPPJsonLDExporter:
    """Tests for EUDPPJsonLDExporter class."""

    def test_create_exporter_default(self):
        """Test creating exporter with defaults."""
        exporter = EUDPPJsonLDExporter()
        assert exporter._include_untp is False
        assert exporter._map_terms is True

    def test_create_exporter_with_untp_context(self):
        """Test creating exporter with UNTP context."""
        exporter = EUDPPJsonLDExporter(include_untp_context=True)
        assert exporter._include_untp is True

    def test_create_exporter_no_term_mapping(self):
        """Test creating exporter without term mapping."""
        exporter = EUDPPJsonLDExporter(map_terms=False)
        assert exporter._map_terms is False


class TestGetEUDPPJsonLDContext:
    """Tests for get_eudpp_jsonld_context function."""

    def test_returns_list(self):
        """Test function returns a list."""
        context = get_eudpp_jsonld_context()
        assert isinstance(context, list)

    def test_contains_vc2_context(self):
        """Test context contains W3C VC2."""
        context = get_eudpp_jsonld_context()
        assert EUDPPNamespace.VC2.value in context

    def test_contains_eudpp_namespace(self):
        """Test context contains EU DPP namespace."""
        context = get_eudpp_jsonld_context()

        # Should have a dict with eudpp key
        has_eudpp = any(isinstance(c, dict) and "eudpp" in c for c in context)
        assert has_eudpp


class TestValidateEUDPPExport:
    """Tests for validate_eudpp_export function."""

    def test_valid_export(self):
        """Test validation of valid export."""
        data = {
            "@context": [
                EUDPPNamespace.VC2.value,
                {"eudpp": EUDPPNamespace.EUDPP.value},
            ],
            "type": ["eudpp:DPP"],
        }

        issues = validate_eudpp_export(data)
        assert issues == []

    def test_missing_context(self):
        """Test validation detects missing @context."""
        data = {"type": ["eudpp:DPP"]}

        issues = validate_eudpp_export(data)
        assert "Missing @context" in issues

    def test_missing_type(self):
        """Test validation detects missing type."""
        data = {
            "@context": [
                EUDPPNamespace.VC2.value,
                {"eudpp": EUDPPNamespace.EUDPP.value},
            ],
        }

        issues = validate_eudpp_export(data)
        assert "Missing type" in issues

    def test_missing_vc2_context(self):
        """Test validation detects missing VC2 context."""
        data = {
            "@context": [{"eudpp": EUDPPNamespace.EUDPP.value}],
            "type": ["eudpp:DPP"],
        }

        issues = validate_eudpp_export(data)
        assert "Missing W3C VC2 context" in issues

    def test_missing_eudpp_namespace(self):
        """Test validation detects missing EU DPP namespace."""
        data = {
            "@context": [EUDPPNamespace.VC2.value],
            "type": ["eudpp:DPP"],
        }

        issues = validate_eudpp_export(data)
        assert "Missing EU DPP namespace in context" in issues


class TestGetTermMappingSummary:
    """Tests for get_term_mapping_summary function."""

    def test_returns_dict(self):
        """Test function returns a dictionary."""
        summary = get_term_mapping_summary()
        assert isinstance(summary, dict)

    def test_contains_mappings(self):
        """Test summary contains expected mappings."""
        summary = get_term_mapping_summary()

        assert "id" in summary
        assert summary["id"] == "uniqueDPPID"

        assert "Product" in summary
        assert summary["Product"] == "Product"


class TestEUDPPExporterImports:
    """Tests for EU DPP exporter imports from package."""

    def test_import_from_exporters_package(self):
        """Test importing from exporters package."""
        from dppvalidator.exporters import (
            EUDPP_CONTEXT_URL,
            EUDPPJsonLDExporter,
            EUDPPTermMapper,
            export_eudpp_jsonld,
            export_eudpp_jsonld_dict,
            get_eudpp_jsonld_context,
            get_term_mapping_summary,
            validate_eudpp_export,
        )

        assert EUDPPJsonLDExporter is not None
        assert EUDPPTermMapper is not None
        assert EUDPP_CONTEXT_URL is not None
        assert export_eudpp_jsonld is not None
        assert export_eudpp_jsonld_dict is not None
        assert get_eudpp_jsonld_context is not None
        assert get_term_mapping_summary is not None
        assert validate_eudpp_export is not None


class TestEUDPPContextURL:
    """Tests for EUDPP_CONTEXT_URL constant."""

    def test_context_url_defined(self):
        """Test context URL is defined."""
        assert EUDPP_CONTEXT_URL is not None
        assert isinstance(EUDPP_CONTEXT_URL, str)
        assert "dpp" in EUDPP_CONTEXT_URL.lower()


class TestExporterWithMockPassport:
    """Tests for exporter with mock passport data."""

    @pytest.fixture
    def mock_passport(self):
        """Create a mock passport-like object for testing."""

        class MockCredentialSubject:
            granularity_level = "model"

        class MockPassport:
            credential_subject = MockCredentialSubject()

            def model_dump(self, **_kwargs):  # noqa: ARG002
                return {
                    "id": "urn:uuid:12345",
                    "type": ["DigitalProductPassport"],
                    "issuer": {"id": "did:example:issuer"},
                    "validFrom": "2025-01-01T00:00:00Z",
                    "credentialSubject": {
                        "product": {
                            "id": "urn:gtin:1234567890123",
                            "name": "Test Product",
                            "description": "A test product",
                        }
                    },
                }

        return MockPassport()

    def test_export_dict(self, mock_passport):
        """Test exporting passport to dictionary."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export_dict(mock_passport)

        assert isinstance(result, dict)
        assert "@context" in result

    def test_export_string(self, mock_passport):
        """Test exporting passport to JSON string."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export(mock_passport)

        assert isinstance(result, str)

        # Should be valid JSON
        parsed = json.loads(result)
        assert "@context" in parsed

    def test_export_contains_vc2_context(self, mock_passport):
        """Test export contains W3C VC2 context."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export_dict(mock_passport)

        assert EUDPPNamespace.VC2.value in result["@context"]

    def test_export_contains_eudpp_namespace(self, mock_passport):
        """Test export contains EU DPP namespace."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export_dict(mock_passport)

        # Context should contain eudpp namespace
        has_eudpp = any(isinstance(c, dict) and "eudpp" in c for c in result["@context"])
        assert has_eudpp

    def test_export_with_term_mapping(self, mock_passport):
        """Test export applies term mapping."""
        exporter = EUDPPJsonLDExporter(map_terms=True)
        result = exporter.export_dict(mock_passport)

        # "id" should be mapped to "uniqueDPPID"
        assert "uniqueDPPID" in result

    def test_export_without_term_mapping(self, mock_passport):
        """Test export without term mapping."""
        exporter = EUDPPJsonLDExporter(map_terms=False)
        result = exporter.export_dict(mock_passport)

        # "id" should remain "id"
        assert "id" in result

    def test_export_with_untp_context(self, mock_passport):
        """Test export includes UNTP context when requested."""
        exporter = EUDPPJsonLDExporter(include_untp_context=True)
        result = exporter.export_dict(mock_passport)

        # Should have UNTP namespace in context
        has_untp = any(isinstance(c, dict) and "untp" in c for c in result["@context"])
        assert has_untp

    def test_export_adds_schema_version(self, mock_passport):
        """Test export adds schema version."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export_dict(mock_passport)

        assert "schemaVersion" in result
        assert "CIRPASS" in result["schemaVersion"]

    def test_export_adds_granularity(self, mock_passport):
        """Test export adds granularity from credential subject."""
        exporter = EUDPPJsonLDExporter()
        result = exporter.export_dict(mock_passport)

        assert "granularity" in result
        assert result["granularity"] == "model"


class TestConvenienceFunctions:
    """Tests for convenience export functions."""

    @pytest.fixture
    def mock_passport(self):
        """Create a mock passport for testing."""

        class MockCredentialSubject:
            granularity_level = None

        class MockPassport:
            credential_subject = MockCredentialSubject()

            def model_dump(self, **_kwargs):  # noqa: ARG002
                return {
                    "id": "urn:uuid:test",
                    "type": ["DigitalProductPassport"],
                }

        return MockPassport()

    def test_export_eudpp_jsonld(self, mock_passport):
        """Test export_eudpp_jsonld convenience function."""
        result = export_eudpp_jsonld(mock_passport)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "@context" in parsed

    def test_export_eudpp_jsonld_dict(self, mock_passport):
        """Test export_eudpp_jsonld_dict convenience function."""
        result = export_eudpp_jsonld_dict(mock_passport)

        assert isinstance(result, dict)
        assert "@context" in result

    def test_export_eudpp_jsonld_no_mapping(self, mock_passport):
        """Test convenience function with no term mapping."""
        result = export_eudpp_jsonld_dict(mock_passport, map_terms=False)

        assert "id" in result

    def test_export_eudpp_jsonld_with_mapping(self, mock_passport):
        """Test convenience function with term mapping."""
        result = export_eudpp_jsonld_dict(mock_passport, map_terms=True)

        assert "uniqueDPPID" in result
