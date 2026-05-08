"""Tests for official SHACL validation (Phase 8)."""

import pytest

from dppvalidator.validators.shacl import (
    OfficialSHACLLoader,
    RDFSHACLValidator,
    SHACLValidationResult,
    is_shacl_validation_available,
)


class TestOfficialSHACLLoader:
    """Tests for OfficialSHACLLoader class."""

    def test_create_loader(self):
        """Test creating a SHACL loader."""
        loader = OfficialSHACLLoader()
        assert loader.SHACL_FILE == "cirpass_dpp_shacl.ttl"
        assert loader._shapes_graph is None
        assert loader._shapes_text is None

    def test_is_available_returns_bool(self):
        """Test is_available returns a boolean."""
        loader = OfficialSHACLLoader()
        result = loader.is_available()
        assert isinstance(result, bool)

    def test_load_shapes_text(self):
        """Test loading SHACL shapes as text."""
        loader = OfficialSHACLLoader()
        shapes_text = loader.load_shapes_text()

        assert isinstance(shapes_text, str)
        assert len(shapes_text) > 0
        # SHACL files contain these prefixes
        assert "@prefix" in shapes_text or "PREFIX" in shapes_text

    def test_load_shapes_text_cached(self):
        """Test SHACL text is cached after first load."""
        loader = OfficialSHACLLoader()
        text1 = loader.load_shapes_text()
        text2 = loader.load_shapes_text()

        assert text1 is text2

    def test_clear_cache(self):
        """Test clearing the cache."""
        loader = OfficialSHACLLoader()
        loader.load_shapes_text()
        assert loader._shapes_text is not None

        loader.clear_cache()
        assert loader._shapes_text is None
        assert loader._shapes_graph is None


class TestRDFSHACLValidator:
    """Tests for RDFSHACLValidator class."""

    def test_create_validator_default(self):
        """Test creating validator with default settings."""
        validator = RDFSHACLValidator()
        assert validator._use_official is True

    def test_create_validator_placeholder(self):
        """Test creating validator with placeholder shapes."""
        validator = RDFSHACLValidator(use_official_shapes=False)
        assert validator._use_official is False

    def test_is_available_returns_bool(self):
        """Test is_available returns a boolean."""
        validator = RDFSHACLValidator()
        result = validator.is_available()
        assert isinstance(result, bool)


class TestSHACLAvailabilityFunction:
    """Tests for is_shacl_validation_available function."""

    def test_returns_bool(self):
        """Test function returns a boolean."""
        result = is_shacl_validation_available()
        assert isinstance(result, bool)


class TestSHACLImports:
    """Tests for SHACL imports from package."""

    def test_import_from_validators_package(self):
        """Test importing from validators package."""
        from dppvalidator.validators import (
            OfficialSHACLLoader,
            RDFSHACLValidator,
            is_shacl_validation_available,
            load_official_shacl_shapes,
            validate_jsonld_with_official_shacl,
        )

        assert OfficialSHACLLoader is not None
        assert RDFSHACLValidator is not None
        assert is_shacl_validation_available is not None
        assert load_official_shacl_shapes is not None
        assert validate_jsonld_with_official_shacl is not None


@pytest.mark.skipif(
    not is_shacl_validation_available(),
    reason="rdflib/pyshacl not installed",
)
class TestOfficialSHACLWithRDFLib:
    """Tests that require rdflib and pyshacl to be installed."""

    def test_load_shapes_graph(self):
        """Test loading SHACL shapes as RDF graph."""
        loader = OfficialSHACLLoader()
        graph = loader.load_shapes_graph()

        assert graph is not None
        assert len(graph) > 0

    def test_load_shapes_graph_cached(self):
        """Test shapes graph is cached after first load."""
        loader = OfficialSHACLLoader()
        graph1 = loader.load_shapes_graph()
        graph2 = loader.load_shapes_graph()

        assert graph1 is graph2

    def test_rdf_validator_load_shapes(self):
        """Test RDF validator loads shapes."""
        validator = RDFSHACLValidator(use_official_shapes=True)
        shapes = validator.load_shapes()

        assert shapes is not None
        assert len(shapes) > 0

    def test_load_official_shacl_shapes_function(self):
        """Test load_official_shacl_shapes convenience function."""
        from dppvalidator.validators.shacl import load_official_shacl_shapes

        graph = load_official_shacl_shapes()
        assert graph is not None
        assert len(graph) > 0


@pytest.mark.skipif(
    is_shacl_validation_available(),
    reason="Test only when rdflib/pyshacl not installed",
)
class TestSHACLWithoutRDFLib:
    """Tests for graceful handling when rdflib/pyshacl not installed."""

    def test_load_shapes_graph_raises_error(self):
        """Test load_shapes_graph raises ImportError."""
        loader = OfficialSHACLLoader()

        with pytest.raises(ImportError) as exc_info:
            loader.load_shapes_graph()

        assert "pip install dppvalidator[rdf]" in str(exc_info.value)

    def test_rdf_validator_load_shapes_raises_error(self):
        """Test RDF validator raises ImportError."""
        validator = RDFSHACLValidator()

        with pytest.raises(ImportError) as exc_info:
            validator.load_shapes()

        assert "pip install dppvalidator[rdf]" in str(exc_info.value)


class TestSHACLValidationResult:
    """Tests for SHACLValidationResult dataclass."""

    def test_create_result_conforms(self):
        """Test creating conforming result."""
        result = SHACLValidationResult(conforms=True)

        assert result.conforms is True
        assert result.violations == []
        assert result.warnings == []
        assert result.info == []

    def test_create_result_violations(self):
        """Test creating result with violations."""
        result = SHACLValidationResult(
            conforms=False,
            violations=[{"path": "test", "message": "error"}],
        )

        assert result.conforms is False
        assert len(result.violations) == 1

    def test_create_result_warnings(self):
        """Test creating result with warnings."""
        result = SHACLValidationResult(
            conforms=True,
            warnings=[{"path": "test", "message": "warning"}],
        )

        assert result.conforms is True
        assert len(result.warnings) == 1


class TestSHACLShapesContent:
    """Tests for SHACL shapes file content."""

    def test_shapes_file_contains_shacl_prefixes(self):
        """Test shapes file contains SHACL prefixes."""
        loader = OfficialSHACLLoader()
        content = loader.load_shapes_text()

        # SHACL shapes should reference sh: prefix
        assert "sh:" in content or "shacl" in content.lower()

    def test_shapes_file_contains_node_shapes(self):
        """Test shapes file contains NodeShape definitions."""
        loader = OfficialSHACLLoader()
        content = loader.load_shapes_text()

        # Should contain NodeShape or PropertyShape
        assert "NodeShape" in content or "PropertyShape" in content

    def test_shapes_file_references_dpp_properties(self):
        """Test shapes file references DPP properties."""
        loader = OfficialSHACLLoader()
        content = loader.load_shapes_text()

        # Should reference DPP-related terms
        # Check for common terms that would appear in DPP SHACL
        has_dpp_terms = any(
            term in content for term in ["DPP", "Product", "uniqueDPPID", "Operator", "Actor"]
        )
        assert has_dpp_terms, "SHACL shapes should reference DPP terms"


class TestSHACLValidatorStructure:
    """Tests for SHACLValidator structural validation."""

    def test_validator_default_shapes(self):
        """Test validator uses CIRPASS shapes by default."""
        from dppvalidator.validators.shacl import CIRPASS_SHAPES, SHACLValidator

        validator = SHACLValidator()
        assert validator._shapes == CIRPASS_SHAPES

    def test_validator_custom_shapes(self):
        """Test validator accepts custom shapes."""
        from dppvalidator.validators.shacl import SHACLNodeShape, SHACLValidator

        custom_shapes = (
            SHACLNodeShape(
                target_class="custom:Class",
                name="CustomShape",
                description="Custom shape",
            ),
        )
        validator = SHACLValidator(shapes=custom_shapes)
        assert validator._shapes == custom_shapes

    def test_validator_shape_count(self):
        """Test shape_count property returns correct count."""
        from dppvalidator.validators.shacl import SHACLValidator

        validator = SHACLValidator()
        assert validator.shape_count == 3  # DPP, Product, Material shapes

    def test_validator_shape_names(self):
        """Test shape_names property returns shape names."""
        from dppvalidator.validators.shacl import SHACLValidator

        validator = SHACLValidator()
        names = validator.shape_names

        assert "CIRPASSDPPShape" in names
        assert "CIRPASSProductShape" in names
        assert "CIRPASSMaterialShape" in names

    def test_validator_get_shape_found(self):
        """Test get_shape returns shape by name."""
        from dppvalidator.validators.shacl import SHACLValidator

        validator = SHACLValidator()
        shape = validator.get_shape("CIRPASSDPPShape")

        assert shape is not None
        assert shape.name == "CIRPASSDPPShape"

    def test_validator_get_shape_not_found(self):
        """Test get_shape returns None for unknown shape."""
        from dppvalidator.validators.shacl import SHACLValidator

        validator = SHACLValidator()
        shape = validator.get_shape("NonexistentShape")

        assert shape is None


class TestSHACLValidatorConstraints:
    """Tests for SHACL constraint validation on DPP structure."""

    def test_validate_structure_missing_issuer(self):
        """Test validation detects missing economic operator."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        passport = MagicMock()
        passport.issuer = None
        passport.valid_from = "2024-01-01"
        passport.credential_subject = None

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is False
        assert any("economicOperator" in v["path"] for v in result.violations)

    def test_validate_structure_missing_valid_from(self):
        """Test validation detects missing market placement date."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = None
        passport.credential_subject = None

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is False
        assert any("marketPlacementDate" in v["path"] for v in result.violations)

    def test_validate_structure_missing_granularity_warning(self):
        """Test validation warns about missing granularity level."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level=None,
            product=None,
            materials_provenance=None,
        )

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is True  # Only warning, not violation
        assert any("granularityLevel" in w["path"] for w in result.warnings)

    def test_validate_structure_missing_product_name(self):
        """Test validation detects missing product name."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        product = MagicMock()
        product.name = None

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level="batch",
            product=product,
            materials_provenance=None,
        )

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is False
        assert any("productName" in v["path"] for v in result.violations)

    def test_validate_structure_missing_material_name(self):
        """Test validation detects missing material name."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        material = MagicMock()
        material.name = None
        material.mass_fraction = 0.5

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level="batch",
            product=None,
            materials_provenance=[material],
        )

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is False
        assert any("materialName" in v["path"] for v in result.violations)

    def test_validate_structure_missing_mass_fraction_warning(self):
        """Test validation warns about missing mass percentage."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        material = MagicMock()
        material.name = "Steel"
        material.mass_fraction = None

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level="batch",
            product=None,
            materials_provenance=[material],
        )

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is True  # Only warning, not violation
        assert any("massPercentage" in w["path"] for w in result.warnings)

    def test_validate_structure_multiple_materials(self):
        """Test validation checks all materials in list."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import SHACLValidator

        # MagicMock has special handling for 'name', so we configure it explicitly
        material1 = MagicMock()
        material1.name = "Steel"
        material1.mass_fraction = 0.6

        material2 = MagicMock()
        material2.name = None  # Missing name - should cause violation
        material2.mass_fraction = None

        material3 = MagicMock()
        material3.name = "Plastic"
        material3.mass_fraction = None  # Missing mass - should cause warning

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level="batch",
            product=None,
            materials_provenance=[material1, material2, material3],
        )

        validator = SHACLValidator()
        result = validator.validate_structure(passport)

        assert result.conforms is False
        # Should have violation for material2 missing name
        assert any("materialName" in v["path"] and "[1]" in v["path"] for v in result.violations)
        # Should have warnings for missing mass fractions
        assert len(result.warnings) >= 1


class TestSHACLConvenienceFunctions:
    """Tests for SHACL convenience functions."""

    def test_get_cirpass_shapes_returns_tuple(self):
        """Test get_cirpass_shapes returns shapes tuple."""
        from dppvalidator.validators.shacl import CIRPASS_SHAPES, get_cirpass_shapes

        shapes = get_cirpass_shapes()
        assert shapes == CIRPASS_SHAPES
        assert len(shapes) == 3

    def test_validate_with_shacl_creates_validator(self):
        """Test validate_with_shacl convenience function."""
        from unittest.mock import MagicMock

        from dppvalidator.validators.shacl import validate_with_shacl

        passport = MagicMock()
        passport.issuer = MagicMock(id="did:web:example.com")
        passport.valid_from = "2024-01-01"
        passport.credential_subject = MagicMock(
            granularity_level="item",
            product=None,
            materials_provenance=None,
        )

        result = validate_with_shacl(passport)

        assert result.conforms is True


@pytest.mark.skipif(
    not is_shacl_validation_available(),
    reason="rdflib/pyshacl not installed",
)
class TestRDFSHACLValidatorAdvanced:
    """Advanced tests for RDFSHACLValidator with pyshacl."""

    def test_rdf_validator_placeholder_shapes(self):
        """Test RDF validator loads placeholder shapes when requested."""
        validator = RDFSHACLValidator(use_official_shapes=False)
        shapes = validator.load_shapes()

        assert shapes is not None
        # Placeholder returns empty graph
        assert len(shapes) == 0

    def test_rdf_validator_validate_graph_conforming(self):
        """Test validate_graph with conforming data."""
        from rdflib import RDF, RDFS, Graph, Namespace

        validator = RDFSHACLValidator(use_official_shapes=True)

        # Create a minimal conforming data graph
        data_graph = Graph()
        EX = Namespace("http://example.org/")
        data_graph.add((EX.product, RDF.type, RDFS.Resource))

        result = validator.validate_graph(data_graph)

        # Should return a SHACLValidationResult
        assert isinstance(result, SHACLValidationResult)

    def test_rdf_validator_validate_jsonld(self):
        """Test validate_jsonld with JSON-LD data."""
        validator = RDFSHACLValidator(use_official_shapes=True)

        jsonld_data = {
            "@context": {"ex": "http://example.org/"},
            "@id": "ex:product1",
            "@type": "ex:Product",
        }

        result = validator.validate_jsonld(jsonld_data)

        assert isinstance(result, SHACLValidationResult)

    def test_validate_jsonld_with_official_shacl_function(self):
        """Test validate_jsonld_with_official_shacl convenience function."""
        from dppvalidator.validators.shacl import validate_jsonld_with_official_shacl

        jsonld_data = {
            "@context": {"ex": "http://example.org/"},
            "@id": "ex:product1",
            "@type": "ex:Product",
        }

        result = validate_jsonld_with_official_shacl(jsonld_data)

        assert isinstance(result, SHACLValidationResult)


class TestSHACLDataclasses:
    """Tests for SHACL dataclass definitions."""

    def test_shacl_property_shape_creation(self):
        """Test SHACLPropertyShape dataclass creation."""
        from dppvalidator.validators.shacl import SHACLPropertyShape, SHACLSeverity

        shape = SHACLPropertyShape(
            path="ex:property",
            name="TestProperty",
            description="Test property shape",
            min_count=1,
            max_count=5,
            datatype="xsd:string",
            pattern="^[A-Z]+$",
            node_kind="sh:IRI",
            severity=SHACLSeverity.WARNING,
        )

        assert shape.path == "ex:property"
        assert shape.min_count == 1
        assert shape.max_count == 5
        assert shape.severity == SHACLSeverity.WARNING

    def test_shacl_node_shape_creation(self):
        """Test SHACLNodeShape dataclass creation."""
        from dppvalidator.validators.shacl import (
            SHACLNodeShape,
            SHACLPropertyShape,
        )

        prop = SHACLPropertyShape(
            path="ex:prop",
            name="Prop",
            description="Property",
        )
        shape = SHACLNodeShape(
            target_class="ex:Class",
            name="TestShape",
            description="Test node shape",
            properties=(prop,),
        )

        assert shape.target_class == "ex:Class"
        assert len(shape.properties) == 1

    def test_shacl_severity_enum_values(self):
        """Test SHACLSeverity enum has correct values."""
        from dppvalidator.validators.shacl import SHACLSeverity

        assert SHACLSeverity.VIOLATION.value == "sh:Violation"
        assert SHACLSeverity.WARNING.value == "sh:Warning"
        assert SHACLSeverity.INFO.value == "sh:Info"

    def test_shacl_constraint_type_enum_values(self):
        """Test SHACLConstraintType enum has correct values."""
        from dppvalidator.validators.shacl import SHACLConstraintType

        assert SHACLConstraintType.MIN_COUNT.value == "sh:minCount"
        assert SHACLConstraintType.MAX_COUNT.value == "sh:maxCount"
        assert SHACLConstraintType.DATATYPE.value == "sh:datatype"
        assert SHACLConstraintType.PATTERN.value == "sh:pattern"


class TestOfficialSHACLLoaderEdgeCases:
    """Tests for OfficialSHACLLoader edge cases."""

    def test_loader_file_not_found_error(self):
        """Test loader raises FileNotFoundError for missing file."""
        import unittest.mock as mock

        loader = OfficialSHACLLoader()

        # Mock the files function to raise FileNotFoundError
        with (
            mock.patch(
                "dppvalidator.validators.shacl.files",
                side_effect=FileNotFoundError("Mock error"),
            ),
            pytest.raises(FileNotFoundError),
        ):
            loader.load_shapes_text()

    def test_loader_caches_text_on_reload(self):
        """Test loader caches text and returns same instance."""
        loader = OfficialSHACLLoader()

        text1 = loader.load_shapes_text()
        text2 = loader.load_shapes_text()

        assert text1 is text2

    def test_loader_clear_cache_resets_state(self):
        """Test clear_cache resets internal state."""
        loader = OfficialSHACLLoader()

        # Load to populate cache
        loader.load_shapes_text()
        assert loader._shapes_text is not None

        # Clear cache
        loader.clear_cache()
        assert loader._shapes_text is None
        assert loader._shapes_graph is None


@pytest.mark.skipif(
    not is_shacl_validation_available(),
    reason="rdflib/pyshacl not installed",
)
class TestRDFSHACLValidationResultParsing:
    """Tests for SHACL validation result parsing."""

    def test_validate_graph_non_conforming_data(self):
        """Test validate_graph with non-conforming data."""
        from rdflib import RDF, RDFS, Graph, Literal, Namespace

        validator = RDFSHACLValidator(use_official_shapes=True)

        # Create data that might trigger SHACL violations
        data_graph = Graph()
        EX = Namespace("http://example.org/")
        EUDPP = Namespace("http://data.europa.eu/2024/dpp/")

        # Add a DPP without required properties
        data_graph.add((EX.dpp1, RDF.type, EUDPP.DPP))
        data_graph.add((EX.dpp1, RDFS.label, Literal("Test DPP")))

        result = validator.validate_graph(data_graph)

        # Result should be returned regardless of conformance
        assert isinstance(result, SHACLValidationResult)

    def test_validate_graph_with_violations(self):
        """Test result parsing captures violations and warnings."""
        from rdflib import RDF, Graph, Namespace

        validator = RDFSHACLValidator(use_official_shapes=True)

        # Create minimal data
        data_graph = Graph()
        EX = Namespace("http://example.org/")
        data_graph.add((EX.item, RDF.type, EX.Thing))

        result = validator.validate_graph(data_graph)

        # Should have parsed results into appropriate lists
        assert isinstance(result.violations, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.info, list)

    def test_parse_validation_results_extracts_severity(self):
        """Test _parse_validation_results extracts severity correctly."""
        from rdflib import Graph, Literal, Namespace, URIRef

        validator = RDFSHACLValidator()

        # Create a mock results graph with SHACL result structure
        SH = Namespace("http://www.w3.org/ns/shacl#")
        results_graph = Graph()

        report = URIRef("http://example.org/report")
        validation_result = URIRef("http://example.org/result1")

        results_graph.add((report, SH.conforms, Literal(False)))
        results_graph.add((report, SH.result, validation_result))
        results_graph.add((validation_result, SH.resultSeverity, SH.Violation))
        results_graph.add((validation_result, SH.resultMessage, Literal("Test error")))
        results_graph.add((validation_result, SH.resultPath, URIRef("http://example.org/path")))
        results_graph.add((validation_result, SH.focusNode, URIRef("http://example.org/node")))

        result = SHACLValidationResult(conforms=False)
        parsed = validator._parse_validation_results(results_graph, result)

        # Should extract violation info
        assert len(parsed.violations) > 0
        assert parsed.violations[0]["message"] == "Test error"

    def test_parse_validation_results_warning_severity(self):
        """Test _parse_validation_results handles warning severity."""
        from rdflib import Graph, Literal, Namespace, URIRef

        validator = RDFSHACLValidator()

        SH = Namespace("http://www.w3.org/ns/shacl#")
        results_graph = Graph()

        report = URIRef("http://example.org/report")
        validation_result = URIRef("http://example.org/result1")

        results_graph.add((report, SH.conforms, Literal(True)))
        results_graph.add((report, SH.result, validation_result))
        results_graph.add((validation_result, SH.resultSeverity, SH.Warning))
        results_graph.add((validation_result, SH.resultMessage, Literal("Test warning")))

        result = SHACLValidationResult(conforms=True)
        parsed = validator._parse_validation_results(results_graph, result)

        # Should extract warning info
        assert len(parsed.warnings) > 0

    def test_parse_validation_results_info_severity(self):
        """Test _parse_validation_results handles info severity."""
        from rdflib import Graph, Literal, Namespace, URIRef

        validator = RDFSHACLValidator()

        SH = Namespace("http://www.w3.org/ns/shacl#")
        results_graph = Graph()

        report = URIRef("http://example.org/report")
        validation_result = URIRef("http://example.org/result1")

        results_graph.add((report, SH.conforms, Literal(True)))
        results_graph.add((report, SH.result, validation_result))
        results_graph.add((validation_result, SH.resultSeverity, SH.Info))
        results_graph.add((validation_result, SH.resultMessage, Literal("Test info")))

        result = SHACLValidationResult(conforms=True)
        parsed = validator._parse_validation_results(results_graph, result)

        # Should extract info
        assert len(parsed.info) > 0


@pytest.mark.skipif(
    is_shacl_validation_available(),
    reason="Test only when rdflib/pyshacl not installed",
)
class TestRDFSHACLWithoutDependencies:
    """Tests for RDF SHACL validator without dependencies."""

    def test_validate_graph_raises_import_error(self):
        """Test validate_graph raises ImportError without pyshacl."""
        validator = RDFSHACLValidator()

        with pytest.raises(ImportError) as exc_info:
            validator.validate_graph(None)

        assert "pyshacl" in str(exc_info.value)

    def test_validate_jsonld_raises_import_error(self):
        """Test validate_jsonld raises ImportError without rdflib."""
        validator = RDFSHACLValidator()

        with pytest.raises(ImportError) as exc_info:
            validator.validate_jsonld({"@id": "test"})

        assert "rdflib" in str(exc_info.value)

    def test_placeholder_shapes_raises_import_error(self):
        """Test _load_placeholder_shapes raises ImportError without rdflib."""
        validator = RDFSHACLValidator(use_official_shapes=False)

        with pytest.raises(ImportError) as exc_info:
            validator.load_shapes()

        assert "rdflib" in str(exc_info.value)
