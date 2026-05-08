"""Tests for EU DPP Core Ontology alignment and SHACL validation."""

import pytest

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators.shacl import (
    CIRPASS_SHAPES,
    SHACLNodeShape,
    SHACLPropertyShape,
    SHACLSeverity,
    SHACLValidationResult,
    SHACLValidator,
    get_cirpass_shapes,
    validate_with_shacl,
)
from dppvalidator.vocabularies.ontology import (
    TERM_MAPPINGS,
    CIRPASSNamespace,
    EUDPPNamespace,
    OntologyMapper,
    TermMapping,
    compact_cirpass_uri,
    compact_eudpp_uri,
    expand_cirpass_uri,
    expand_eudpp_uri,
    get_cirpass_context,
    get_eudpp_context,
)


class TestEUDPPNamespace:
    """Tests for EU DPP Core Ontology namespace definitions."""

    def test_official_namespace(self):
        """Test official EU DPP namespace is correct."""
        assert EUDPPNamespace.EUDPP.value == "http://dpp.taltech.ee/EUDPP#"

    def test_si_namespace(self):
        """Test SI Digital Framework namespace."""
        assert EUDPPNamespace.SI.value == "https://si-digital-framework.org/SI#"

    def test_namespace_values(self):
        """Test namespace enum values exist."""
        assert EUDPPNamespace.EUDPP.value.startswith("http")
        assert EUDPPNamespace.UNTP_DPP.value.startswith("https://")
        assert EUDPPNamespace.VC2.value.startswith("https://")

    def test_backward_compatibility_alias(self):
        """Test CIRPASSNamespace is alias for EUDPPNamespace."""
        assert CIRPASSNamespace is EUDPPNamespace


class TestTermMapping:
    """Tests for term mapping between UNTP and CIRPASS."""

    def test_term_mappings_not_empty(self):
        """Test TERM_MAPPINGS is not empty."""
        assert len(TERM_MAPPINGS) > 0

    def test_term_mapping_structure(self):
        """Test TermMapping has required fields."""
        for mapping in TERM_MAPPINGS:
            assert isinstance(mapping, TermMapping)
            assert mapping.untp_term
            assert mapping.cirpass_uri
            assert mapping.description

    def test_all_uris_have_eudpp_prefix(self):
        """Test all URIs use eudpp: prefix."""
        for mapping in TERM_MAPPINGS:
            assert mapping.cirpass_uri.startswith("eudpp:")


class TestOntologyMapper:
    """Tests for OntologyMapper class."""

    @pytest.fixture
    def mapper(self) -> OntologyMapper:
        """Create mapper instance."""
        return OntologyMapper()

    def test_to_cirpass_valid_term(self, mapper: OntologyMapper):
        """Test mapping UNTP term to EU DPP URI."""
        result = mapper.to_cirpass("DigitalProductPassport")
        assert result == "eudpp:DPP"

    def test_to_cirpass_invalid_term(self, mapper: OntologyMapper):
        """Test mapping invalid term returns None."""
        result = mapper.to_cirpass("InvalidTerm")
        assert result is None

    def test_to_untp_valid_uri(self, mapper: OntologyMapper):
        """Test mapping EU DPP URI to UNTP term."""
        result = mapper.to_untp("eudpp:DPP")
        assert result == "DigitalProductPassport"

    def test_to_untp_invalid_uri(self, mapper: OntologyMapper):
        """Test mapping invalid URI returns None."""
        result = mapper.to_untp("eudpp:InvalidUri")
        assert result is None

    def test_get_mapping_by_untp_term(self, mapper: OntologyMapper):
        """Test getting full mapping by UNTP term."""
        mapping = mapper.get_mapping("Product")
        assert mapping is not None
        assert mapping.untp_term == "Product"
        assert mapping.cirpass_uri == "eudpp:Product"

    def test_get_mapping_by_eudpp_uri(self, mapper: OntologyMapper):
        """Test getting full mapping by EU DPP URI."""
        mapping = mapper.get_mapping("eudpp:Product")
        assert mapping is not None
        assert mapping.untp_term == "Product"

    def test_get_espr_reference(self, mapper: OntologyMapper):
        """Test getting ESPR reference for term."""
        ref = mapper.get_espr_reference("DigitalProductPassport")
        assert ref is not None
        assert "ESPR" in ref

    def test_iter_mappings(self, mapper: OntologyMapper):
        """Test iterating over all mappings."""
        mappings = list(mapper.iter_mappings())
        assert len(mappings) == len(TERM_MAPPINGS)

    def test_mapped_terms_property(self, mapper: OntologyMapper):
        """Test mapped_terms property."""
        terms = mapper.mapped_terms
        assert "DigitalProductPassport" in terms
        assert "Product" in terms

    def test_mapping_count_property(self, mapper: OntologyMapper):
        """Test mapping_count property."""
        assert mapper.mapping_count == len(TERM_MAPPINGS)


class TestURIExpansion:
    """Tests for URI expansion and compaction."""

    def test_expand_eudpp_uri(self):
        """Test expanding compact EU DPP URI."""
        result = expand_eudpp_uri("eudpp:Product")
        assert result == "http://dpp.taltech.ee/EUDPP#Product"

    def test_expand_already_full_uri(self):
        """Test expanding already full URI."""
        full = "https://example.com/term"
        result = expand_eudpp_uri(full)
        assert result == full

    def test_compact_eudpp_uri(self):
        """Test compacting full EU DPP URI."""
        full = f"{EUDPPNamespace.EUDPP.value}Product"
        result = compact_eudpp_uri(full)
        assert result == "eudpp:Product"

    def test_compact_unknown_uri(self):
        """Test compacting unknown namespace."""
        unknown = "https://unknown.org/term"
        result = compact_eudpp_uri(unknown)
        assert result == unknown

    def test_backward_compat_expand(self):
        """Test backward compatibility alias for expand."""
        result = expand_cirpass_uri("eudpp:Product")
        assert "Product" in result

    def test_backward_compat_compact(self):
        """Test backward compatibility alias for compact."""
        full = f"{EUDPPNamespace.EUDPP.value}Product"
        result = compact_cirpass_uri(full)
        assert result == "eudpp:Product"


class TestGetEUDPPContext:
    """Tests for get_eudpp_context function."""

    def test_context_has_eudpp(self):
        """Test context includes eudpp namespace."""
        ctx = get_eudpp_context()
        assert "eudpp" in ctx
        assert ctx["eudpp"] == "http://dpp.taltech.ee/EUDPP#"

    def test_context_has_si(self):
        """Test context includes SI namespace."""
        ctx = get_eudpp_context()
        assert "si" in ctx
        assert ctx["si"] == "https://si-digital-framework.org/SI#"

    def test_context_has_untp(self):
        """Test context includes untp namespace."""
        ctx = get_eudpp_context()
        assert "untp" in ctx

    def test_context_is_dict(self):
        """Test context is a dictionary."""
        ctx = get_eudpp_context()
        assert isinstance(ctx, dict)
        assert len(ctx) >= 5

    def test_backward_compat_context(self):
        """Test backward compatibility alias."""
        ctx = get_cirpass_context()
        assert "eudpp" in ctx


class TestSHACLShapes:
    """Tests for SHACL shape definitions."""

    def test_cirpass_shapes_not_empty(self):
        """Test CIRPASS_SHAPES is not empty."""
        assert len(CIRPASS_SHAPES) > 0

    def test_get_cirpass_shapes_function(self):
        """Test get_cirpass_shapes returns shapes."""
        shapes = get_cirpass_shapes()
        assert shapes == CIRPASS_SHAPES

    def test_shape_structure(self):
        """Test SHACLNodeShape has required fields."""
        for shape in CIRPASS_SHAPES:
            assert isinstance(shape, SHACLNodeShape)
            assert shape.target_class
            assert shape.name
            assert shape.description

    def test_property_shapes_exist(self):
        """Test shapes have property shapes."""
        dpp_shape = CIRPASS_SHAPES[0]
        assert len(dpp_shape.properties) > 0

    def test_property_shape_structure(self):
        """Test SHACLPropertyShape has required fields."""
        dpp_shape = CIRPASS_SHAPES[0]
        for prop in dpp_shape.properties:
            assert isinstance(prop, SHACLPropertyShape)
            assert prop.path
            assert prop.name
            assert prop.description


class TestSHACLSeverity:
    """Tests for SHACL severity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert SHACLSeverity.VIOLATION.value == "sh:Violation"
        assert SHACLSeverity.WARNING.value == "sh:Warning"
        assert SHACLSeverity.INFO.value == "sh:Info"


class TestSHACLValidator:
    """Tests for SHACLValidator class."""

    @pytest.fixture
    def validator(self) -> SHACLValidator:
        """Create validator instance."""
        return SHACLValidator()

    def test_shape_count(self, validator: SHACLValidator):
        """Test shape_count property."""
        assert validator.shape_count == len(CIRPASS_SHAPES)

    def test_shape_names(self, validator: SHACLValidator):
        """Test shape_names property."""
        names = validator.shape_names
        assert "CIRPASSDPPShape" in names
        assert "CIRPASSProductShape" in names

    def test_get_shape(self, validator: SHACLValidator):
        """Test get_shape method."""
        shape = validator.get_shape("CIRPASSDPPShape")
        assert shape is not None
        assert shape.name == "CIRPASSDPPShape"

    def test_get_shape_not_found(self, validator: SHACLValidator):
        """Test get_shape returns None for unknown shape."""
        shape = validator.get_shape("UnknownShape")
        assert shape is None

    def test_validate_valid_passport(self, validator: SHACLValidator):
        """Test validating a valid passport."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=ProductPassport(
                granularityLevel="model",
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                ),
            ),
        )
        result = validator.validate_structure(passport)
        assert result.conforms is True
        assert len(result.violations) == 0

    def test_validate_missing_valid_from_produces_violation(self, validator: SHACLValidator):
        """Test validating passport without validFrom produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        result = validator.validate_structure(passport)
        assert result.conforms is False
        assert len(result.violations) >= 1
        assert any("marketPlacementDate" in v["path"] for v in result.violations)

    def test_validate_missing_valid_from(self, validator: SHACLValidator):
        """Test validating passport without validFrom produces violation."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        result = validator.validate_structure(passport)
        assert result.conforms is False
        assert any("marketPlacementDate" in v["path"] for v in result.violations)

    def test_validate_missing_granularity_produces_warning(self, validator: SHACLValidator):
        """Test validating passport without granularity produces warning."""
        from dppvalidator.models import ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=ProductPassport(),
        )
        result = validator.validate_structure(passport)
        assert len(result.warnings) >= 1
        assert any("granularityLevel" in w["path"] for w in result.warnings)


class TestValidateWithSHACL:
    """Tests for validate_with_shacl convenience function."""

    def test_validate_with_shacl_valid(self):
        """Test validate_with_shacl with valid passport."""
        from dppvalidator.models import Product, ProductPassport

        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=ProductPassport(
                granularityLevel="model",
                product=Product(
                    id="https://example.com/product",
                    name="Test Product",
                ),
            ),
        )
        result = validate_with_shacl(passport)
        assert isinstance(result, SHACLValidationResult)
        assert result.conforms is True

    def test_validate_with_shacl_missing_valid_from(self):
        """Test validate_with_shacl with missing validFrom."""
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        result = validate_with_shacl(passport)
        assert result.conforms is False
