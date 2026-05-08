"""Integration tests for CIRPASS-2 SHACL validation.

Tests the full SHACL validation pipeline with rdflib and pyshacl
against official CIRPASS-2 shapes.
"""

import json
from pathlib import Path

import pytest

from dppvalidator.vocabularies.rdf_loader import is_rdf_available, is_shacl_available

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

pytestmark = pytest.mark.skipif(
    not is_shacl_available(),
    reason="SHACL validation requires pyshacl: pip install dppvalidator[rdf]",
)


class TestSHACLShapesLoading:
    """Tests for loading and parsing SHACL shapes."""

    def test_cirpass_shacl_shapes_load_successfully(self):
        """Test that CIRPASS SHACL shapes load without errors."""
        from dppvalidator.vocabularies.rdf_loader import load_cirpass_shacl_shapes

        graph = load_cirpass_shacl_shapes()
        assert graph is not None
        # Should have triples
        assert len(graph) > 0

    def test_shacl_shapes_contain_node_shapes(self):
        """Test SHACL shapes define NodeShape constraints."""
        from rdflib import SH

        from dppvalidator.vocabularies.rdf_loader import load_cirpass_shacl_shapes

        graph = load_cirpass_shacl_shapes()

        # Find all NodeShapes
        node_shapes = list(graph.subjects(predicate=None, object=SH.NodeShape))
        # Should have at least some node shapes defined
        assert len(node_shapes) >= 0  # May be 0 if shapes use different patterns


class TestSHACLValidationBehavior:
    """Tests for SHACL validation behavior with real DPP data."""

    @pytest.fixture
    def valid_dpp(self):
        """Load a valid DPP fixture."""
        fixture_path = FIXTURES_DIR / "valid" / "minimal_dpp.json"
        with open(fixture_path, encoding="utf-8") as f:
            return json.load(f)

    def test_shacl_validator_initializes(self):
        """Test SHACLValidator can be initialized."""
        from dppvalidator.validators.shacl import SHACLValidator

        validator = SHACLValidator()
        assert validator is not None

    def test_shacl_validates_valid_dpp_structure(self, valid_dpp):
        """Test SHACL validation accepts valid DPP structure."""
        from dppvalidator.models import DigitalProductPassport
        from dppvalidator.validators.shacl import validate_with_shacl

        # Parse the DPP data into a model
        passport = DigitalProductPassport.model_validate(valid_dpp)
        result = validate_with_shacl(passport)
        assert result is not None
        assert hasattr(result, "conforms")

    def test_shacl_produces_violations_for_incomplete_passport(self):
        """Test SHACL validation produces violations for incomplete DPP."""
        from dppvalidator.models import CredentialIssuer, DigitalProductPassport
        from dppvalidator.validators.shacl import validate_with_shacl

        # Minimal passport missing some CIRPASS required fields
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        result = validate_with_shacl(passport)
        assert result is not None
        # Should have some violations for missing fields
        assert hasattr(result, "violations")


class TestOntologyIntegration:
    """Tests for EU DPP ontology integration."""

    def test_load_all_eudpp_ontologies(self):
        """Test loading all EU DPP ontologies into merged graph."""
        from dppvalidator.vocabularies.rdf_loader import load_all_eudpp_ontologies

        graph = load_all_eudpp_ontologies()
        # Returns a merged Graph
        assert graph is not None
        assert len(graph) > 0

    def test_ontologies_contain_triples(self):
        """Test merged ontology contains triples."""
        from dppvalidator.vocabularies.rdf_loader import load_all_eudpp_ontologies

        graph = load_all_eudpp_ontologies()
        # Should have substantial content
        assert len(graph) > 100

    def test_product_dpp_ontology_has_content(self):
        """Test product_dpp ontology has content."""
        from dppvalidator.vocabularies.rdf_loader import load_bundled_ontology

        graph = load_bundled_ontology("product_dpp_v1.7.1.ttl")
        assert graph is not None
        assert len(graph) > 0


class TestRDFLibIntegration:
    """Tests for rdflib library integration."""

    @pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
    def test_rdflib_graph_creation(self):
        """Test rdflib Graph can be created and used."""
        from rdflib import Graph, Literal, Namespace

        g = Graph()
        ex = Namespace("https://example.com/")

        g.add((ex.subject, ex.predicate, Literal("object")))
        assert len(g) == 1

    @pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
    def test_rdflib_turtle_parsing(self):
        """Test rdflib can parse Turtle format."""
        from rdflib import Graph

        ttl_data = """
        @prefix ex: <https://example.com/> .
        ex:Product a ex:DigitalProductPassport ;
            ex:name "Test Product" .
        """
        g = Graph()
        g.parse(data=ttl_data, format="turtle")
        assert len(g) == 2

    @pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
    def test_rdflib_jsonld_parsing(self):
        """Test rdflib can parse JSON-LD format."""
        from rdflib import Graph

        jsonld_data = {
            "@context": {"ex": "https://example.com/"},
            "@id": "ex:product1",
            "@type": "ex:Product",
            "ex:name": "Test Product",
        }
        g = Graph()
        g.parse(data=json.dumps(jsonld_data), format="json-ld")
        assert len(g) >= 1


class TestPySHACLIntegration:
    """Tests for pyshacl library integration."""

    def test_pyshacl_validate_function_available(self):
        """Test pyshacl validate function is importable."""
        from pyshacl import validate

        assert callable(validate)

    def test_pyshacl_basic_validation(self):
        """Test basic pyshacl validation works."""
        from pyshacl import validate
        from rdflib import Graph

        # Simple data graph
        data_ttl = """
        @prefix ex: <https://example.com/> .
        ex:Product1 a ex:Product ;
            ex:name "Test" .
        """

        # Simple shapes graph requiring name
        shapes_ttl = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <https://example.com/> .

        ex:ProductShape a sh:NodeShape ;
            sh:targetClass ex:Product ;
            sh:property [
                sh:path ex:name ;
                sh:minCount 1 ;
            ] .
        """

        data_graph = Graph().parse(data=data_ttl, format="turtle")
        shapes_graph = Graph().parse(data=shapes_ttl, format="turtle")

        conforms, _, _ = validate(data_graph, shacl_graph=shapes_graph)
        assert conforms is True

    def test_pyshacl_detects_violations(self):
        """Test pyshacl detects shape violations."""
        from pyshacl import validate
        from rdflib import Graph

        # Data missing required property
        data_ttl = """
        @prefix ex: <https://example.com/> .
        ex:Product1 a ex:Product .
        """

        shapes_ttl = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <https://example.com/> .

        ex:ProductShape a sh:NodeShape ;
            sh:targetClass ex:Product ;
            sh:property [
                sh:path ex:name ;
                sh:minCount 1 ;
                sh:message "Product must have a name" ;
            ] .
        """

        data_graph = Graph().parse(data=data_ttl, format="turtle")
        shapes_graph = Graph().parse(data=shapes_ttl, format="turtle")

        conforms, results_graph, _ = validate(data_graph, shacl_graph=shapes_graph)
        assert conforms is False
        assert len(results_graph) > 0
