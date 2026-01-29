"""Tests for exporters."""

import json

import pytest

from dppvalidator.exporters import (
    ContextManager,
    JSONExporter,
    JSONLDExporter,
    export_json,
    export_jsonld,
)
from dppvalidator.models import CredentialIssuer, DigitalProductPassport


class TestContextManager:
    """Tests for ContextManager."""

    def test_default_version(self):
        """Test default version is 0.6.1."""
        manager = ContextManager()
        assert manager.version == "0.6.1"

    def test_get_context(self):
        """Test getting context URLs."""
        manager = ContextManager()
        context = manager.get_context()
        assert "https://www.w3.org/ns/credentials/v2" in context
        assert any("untp/dpp/0.6.1" in url for url in context)

    def test_get_type(self):
        """Test getting type array."""
        manager = ContextManager()
        types = manager.get_type()
        assert "DigitalProductPassport" in types
        assert "VerifiableCredential" in types

    def test_validate_context_valid(self):
        """Test validating correct context."""
        manager = ContextManager()
        context = manager.get_context()
        assert manager.validate_context(context) is True

    def test_validate_context_invalid(self):
        """Test validating incorrect context."""
        manager = ContextManager()
        assert manager.validate_context(["https://wrong.context"]) is False

    def test_available_versions(self):
        """Test listing available versions."""
        manager = ContextManager()
        versions = manager.available_versions
        assert "0.6.1" in versions
        assert "0.6.0" in versions


class TestJSONLDExporter:
    """Tests for JSONLDExporter."""

    @pytest.fixture
    def passport(self) -> DigitalProductPassport:
        """Create test passport."""
        return DigitalProductPassport(
            id="https://example.com/credentials/dpp-001",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/001",
                name="Example Company Ltd",
            ),
        )

    def test_export_string(self, passport: DigitalProductPassport):
        """Test exporting to string."""
        exporter = JSONLDExporter()
        result = exporter.export(passport)
        assert isinstance(result, str)
        data = json.loads(result)
        assert "@context" in data

    def test_export_dict(self, passport: DigitalProductPassport):
        """Test exporting to dictionary."""
        exporter = JSONLDExporter()
        result = exporter.export_dict(passport)
        assert isinstance(result, dict)
        assert "@context" in result

    def test_export_includes_context(self, passport: DigitalProductPassport):
        """Test that export includes W3C VC context."""
        exporter = JSONLDExporter()
        result = exporter.export_dict(passport)
        assert "https://www.w3.org/ns/credentials/v2" in result["@context"]

    def test_export_compact(self, passport: DigitalProductPassport):
        """Test compact export (no indentation)."""
        exporter = JSONLDExporter()
        result = exporter.export(passport, indent=None)
        assert "\n" not in result

    def test_convenience_function(self, passport: DigitalProductPassport):
        """Test export_jsonld convenience function."""
        result = export_jsonld(passport)
        data = json.loads(result)
        assert "@context" in data


class TestJSONExporter:
    """Tests for JSONExporter."""

    @pytest.fixture
    def passport(self) -> DigitalProductPassport:
        """Create test passport."""
        return DigitalProductPassport(
            id="https://example.com/credentials/dpp-001",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/001",
                name="Example Company Ltd",
            ),
        )

    def test_export_string(self, passport: DigitalProductPassport):
        """Test exporting to string."""
        exporter = JSONExporter()
        result = exporter.export(passport)
        assert isinstance(result, str)
        data = json.loads(result)
        assert "issuer" in data

    def test_export_dict(self, passport: DigitalProductPassport):
        """Test exporting to dictionary."""
        exporter = JSONExporter()
        result = exporter.export_dict(passport)
        assert isinstance(result, dict)

    def test_export_excludes_none(self, passport: DigitalProductPassport):
        """Test that None values are excluded."""
        exporter = JSONExporter(exclude_none=True)
        result = exporter.export_dict(passport)
        assert result.get("credentialSubject") is None or "credentialSubject" not in result

    def test_convenience_function(self, passport: DigitalProductPassport):
        """Test export_json convenience function."""
        result = export_json(passport)
        data = json.loads(result)
        assert "issuer" in data


class TestRoundTrip:
    """Round-trip tests: parse → export → parse."""

    def test_roundtrip_jsonld_minimal(self):
        """Test round-trip with minimal passport via JSON-LD."""
        from dppvalidator.validators import ValidationEngine

        # Create original passport
        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-001",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/001",
                name="Round Trip Test Company",
            ),
        )

        # Export to JSON-LD
        exporter = JSONLDExporter()
        exported_json = exporter.export(original)

        # Parse exported JSON
        exported_data = json.loads(exported_json)

        # Validate and re-parse
        engine = ValidationEngine()
        result = engine.validate(exported_data)

        # Verify round-trip success
        assert result.valid is True
        assert result.passport is not None
        assert str(result.passport.id) == str(original.id)
        assert result.passport.issuer.name == original.issuer.name

    def test_roundtrip_json_minimal(self):
        """Test round-trip with minimal passport via plain JSON."""
        from dppvalidator.validators import ValidationEngine

        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-002",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/002",
                name="JSON Round Trip Co",
            ),
        )

        # Export to JSON
        exporter = JSONExporter()
        exported_json = exporter.export(original)

        # Parse and validate
        exported_data = json.loads(exported_json)
        engine = ValidationEngine()
        result = engine.validate(exported_data)

        assert result.valid is True
        assert result.passport is not None
        assert result.passport.issuer.name == original.issuer.name

    def test_roundtrip_with_product(self):
        """Test round-trip with product data."""
        from dppvalidator.models import Product, ProductPassport
        from dppvalidator.validators import ValidationEngine

        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-003",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/003",
                name="Product Test Inc",
            ),
            credentialSubject=ProductPassport(
                product=Product(
                    id="https://example.com/products/widget-001",
                    name="Premium Widget",
                    serialNumber="SN-12345",
                ),
            ),
        )

        # Export and re-parse
        exporter = JSONLDExporter()
        exported = exporter.export(original)
        data = json.loads(exported)

        engine = ValidationEngine()
        result = engine.validate(data)

        assert result.valid is True
        assert result.passport is not None
        assert result.passport.credential_subject is not None
        assert result.passport.credential_subject.product is not None
        assert result.passport.credential_subject.product.name == "Premium Widget"
        assert result.passport.credential_subject.product.serial_number == "SN-12345"

    def test_roundtrip_with_materials(self):
        """Test round-trip with materials data."""
        from dppvalidator.models import Material, ProductPassport
        from dppvalidator.validators import ValidationEngine

        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-004",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/004",
                name="Materials Test Ltd",
            ),
            credentialSubject=ProductPassport(
                materialsProvenance=[
                    Material(name="Steel", massFraction=0.6),
                    Material(name="Plastic", massFraction=0.4),
                ],
            ),
        )

        # Export and re-parse
        exporter = JSONLDExporter()
        exported = exporter.export(original)
        data = json.loads(exported)

        engine = ValidationEngine()
        result = engine.validate(data)

        assert result.valid is True
        assert result.passport is not None
        assert result.passport.credential_subject is not None
        materials = result.passport.credential_subject.materials_provenance
        assert materials is not None
        assert len(materials) == 2
        assert materials[0].name == "Steel"
        assert materials[0].mass_fraction == 0.6

    def test_roundtrip_with_dates(self):
        """Test round-trip preserves dates."""
        from datetime import datetime, timezone

        from dppvalidator.validators import ValidationEngine

        valid_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        valid_until = datetime(2034, 12, 31, tzinfo=timezone.utc)

        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-005",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/005",
                name="Dates Test Corp",
            ),
            validFrom=valid_from,
            validUntil=valid_until,
        )

        exporter = JSONLDExporter()
        exported = exporter.export(original)
        data = json.loads(exported)

        engine = ValidationEngine()
        result = engine.validate(data)

        assert result.valid is True
        assert result.passport is not None
        assert result.passport.valid_from is not None
        assert result.passport.valid_until is not None
        # Dates should be preserved (compare as dates)
        assert result.passport.valid_from.year == 2024
        assert result.passport.valid_until.year == 2034

    def test_roundtrip_dict_export(self):
        """Test round-trip using export_dict."""
        from dppvalidator.validators import ValidationEngine

        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-006",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/006",
                name="Dict Export Test",
            ),
        )

        exporter = JSONLDExporter()
        data = exporter.export_dict(original)

        engine = ValidationEngine()
        result = engine.validate(data)

        assert result.valid is True
        assert result.passport is not None

    def test_roundtrip_preserves_context(self):
        """Test round-trip preserves @context."""
        original = DigitalProductPassport(
            id="https://example.com/credentials/dpp-007",
            issuer=CredentialIssuer(
                id="https://example.com/issuers/007",
                name="Context Test",
            ),
        )

        exporter = JSONLDExporter()
        data = exporter.export_dict(original)

        # Verify context is present
        assert "@context" in data
        assert "https://www.w3.org/ns/credentials/v2" in data["@context"]

        # Re-export should preserve context
        from dppvalidator.validators import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate(data)
        assert result.valid is True

        # Export again
        if result.passport:
            re_exported = exporter.export_dict(result.passport)
            assert "@context" in re_exported


class TestExporterEdgeCases:
    """Edge case tests for exporters."""

    def test_jsonld_exporter_version(self):
        """Test JSONLDExporter with specific version."""
        exporter = JSONLDExporter(version="0.6.0")
        assert exporter.version == "0.6.0"

    def test_context_manager_unknown_version(self):
        """Test ContextManager with unknown version falls back to default."""
        manager = ContextManager(version="99.99.99")
        context = manager.get_context()
        # Should fall back to default
        assert len(context) > 0

    def test_json_exporter_include_none(self):
        """Test JSONExporter with exclude_none=False."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        exporter = JSONExporter(exclude_none=False)
        data = exporter.export_dict(passport)
        # Should include None values
        assert data is not None

    def test_json_exporter_no_alias(self):
        """Test JSONExporter with by_alias=False."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        exporter = JSONExporter()
        data = exporter.export_dict(passport, by_alias=False)
        # Uses snake_case field names
        assert data is not None


class TestExportToFile:
    """Tests for file export functionality."""

    def test_jsonld_export_to_file(self, tmp_path):
        """Test JSONLDExporter export_to_file."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="File Test"),
        )
        output_path = tmp_path / "output.jsonld"

        exporter = JSONLDExporter()
        exporter.export_to_file(passport, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        data = json.loads(content)
        assert "@context" in data

    def test_json_export_to_file(self, tmp_path):
        """Test JSONExporter export_to_file."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="File Test"),
        )
        output_path = tmp_path / "output.json"

        exporter = JSONExporter()
        exporter.export_to_file(passport, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        data = json.loads(content)
        assert "issuer" in data
