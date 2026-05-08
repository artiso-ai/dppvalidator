"""Tests for RDF loader with optional dependencies (Phase 7)."""

import pytest

from dppvalidator.vocabularies.rdf_loader import (
    RDFNotAvailableError,
    is_rdf_available,
    is_shacl_available,
)


class TestRDFAvailabilityChecks:
    """Tests for RDF availability checking functions."""

    def test_is_rdf_available_returns_bool(self):
        """Test is_rdf_available returns a boolean."""
        result = is_rdf_available()
        assert isinstance(result, bool)

    def test_is_shacl_available_returns_bool(self):
        """Test is_shacl_available returns a boolean."""
        result = is_shacl_available()
        assert isinstance(result, bool)


class TestRDFNotAvailableError:
    """Tests for RDFNotAvailableError exception."""

    def test_error_message_default(self):
        """Test default error message."""
        error = RDFNotAvailableError()
        assert "RDF functionality" in str(error)
        assert "pip install dppvalidator[rdf]" in str(error)

    def test_error_message_custom_feature(self):
        """Test custom feature in error message."""
        error = RDFNotAvailableError("SHACL validation")
        assert "SHACL validation" in str(error)
        assert "pip install dppvalidator[rdf]" in str(error)

    def test_error_is_import_error(self):
        """Test error is subclass of ImportError."""
        error = RDFNotAvailableError()
        assert isinstance(error, ImportError)


class TestRDFLoaderImports:
    """Tests for RDF loader imports from package."""

    def test_import_from_vocabularies_package(self):
        """Test importing from vocabularies package."""
        from dppvalidator.vocabularies import (
            RDFNotAvailableError,
            is_rdf_available,
            is_shacl_available,
        )

        assert RDFNotAvailableError is not None
        assert is_rdf_available is not None
        assert is_shacl_available is not None

    def test_import_load_functions(self):
        """Test importing load functions from submodule."""
        from dppvalidator.vocabularies.rdf_loader import (
            load_bundled_ontology,
            load_ontology,
            load_ontology_text,
        )

        assert load_ontology is not None
        assert load_ontology_text is not None
        assert load_bundled_ontology is not None

    def test_import_convenience_functions(self):
        """Test importing convenience loading functions from submodule."""
        from dppvalidator.vocabularies.rdf_loader import (
            load_actor_ontology,
            load_all_eudpp_ontologies,
            load_cirpass_shacl_shapes,
            load_eudpp_core_ontology,
            load_lca_ontology,
            load_soc_ontology,
        )

        assert load_eudpp_core_ontology is not None
        assert load_soc_ontology is not None
        assert load_lca_ontology is not None
        assert load_actor_ontology is not None
        assert load_all_eudpp_ontologies is not None
        assert load_cirpass_shacl_shapes is not None

    def test_import_query_functions(self):
        """Test importing query functions from submodule."""
        from dppvalidator.vocabularies.rdf_loader import (
            get_ontology_classes,
            get_ontology_properties,
            query_ontology,
        )

        assert query_ontology is not None
        assert get_ontology_classes is not None
        assert get_ontology_properties is not None


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestRDFLoaderWithRDFLib:
    """Tests that require rdflib to be installed."""

    def test_load_bundled_ontology(self):
        """Test loading a bundled ontology."""
        from dppvalidator.vocabularies.rdf_loader import load_bundled_ontology

        graph = load_bundled_ontology("soc_v1.4.7.ttl")
        assert graph is not None
        assert len(graph) > 0

    def test_load_soc_ontology(self):
        """Test loading SOC ontology."""
        from dppvalidator.vocabularies.rdf_loader import load_soc_ontology

        graph = load_soc_ontology()
        assert graph is not None
        assert len(graph) > 0

    def test_load_lca_ontology(self):
        """Test loading LCA ontology."""
        from dppvalidator.vocabularies.rdf_loader import load_lca_ontology

        graph = load_lca_ontology()
        assert graph is not None
        assert len(graph) > 0

    def test_load_ontology_text(self):
        """Test loading ontology from text."""
        from dppvalidator.vocabularies.rdf_loader import load_ontology_text

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org/TestClass> a owl:Class ;
            rdfs:label "Test Class" .
        """

        graph = load_ontology_text(ttl_content)
        assert graph is not None
        assert len(graph) > 0

    def test_load_cirpass_shacl_shapes(self):
        """Test loading CIRPASS SHACL shapes."""
        from dppvalidator.vocabularies.rdf_loader import load_cirpass_shacl_shapes

        graph = load_cirpass_shacl_shapes()
        assert graph is not None
        assert len(graph) > 0

    def test_load_all_eudpp_ontologies(self):
        """Test loading all EU DPP ontologies."""
        from dppvalidator.vocabularies.rdf_loader import load_all_eudpp_ontologies

        graph = load_all_eudpp_ontologies()
        assert graph is not None
        # Merged graph should have many triples
        assert len(graph) > 100


@pytest.mark.skipif(is_rdf_available(), reason="Test only when rdflib not installed")
class TestRDFLoaderWithoutRDFLib:
    """Tests for graceful handling when rdflib is not installed."""

    def test_load_ontology_raises_error(self):
        """Test load_ontology raises RDFNotAvailableError."""
        from pathlib import Path

        from dppvalidator.vocabularies.rdf_loader import load_ontology

        with pytest.raises(RDFNotAvailableError):
            load_ontology(Path("/nonexistent.ttl"))

    def test_load_bundled_ontology_raises_error(self):
        """Test load_bundled_ontology raises RDFNotAvailableError."""
        from dppvalidator.vocabularies.rdf_loader import load_bundled_ontology

        with pytest.raises(RDFNotAvailableError):
            load_bundled_ontology("soc_v1.4.7.ttl")


class TestPyprojectOptionalDependencies:
    """Tests for pyproject.toml optional dependencies."""

    def test_rdf_extra_defined(self):
        """Test [rdf] extra is defined in pyproject.toml."""
        import sys
        from pathlib import Path

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # noqa: PLC0415

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)  # noqa: F821

        optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
        assert "rdf" in optional_deps

        rdf_deps = optional_deps["rdf"]
        assert any("rdflib" in dep for dep in rdf_deps)
        assert any("pyshacl" in dep for dep in rdf_deps)

    def test_all_extra_includes_rdf(self):
        """Test [all] extra includes [rdf]."""
        import sys
        from pathlib import Path

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # noqa: PLC0415

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
        assert "all" in optional_deps

        all_deps = optional_deps["all"]
        assert any("rdf" in dep for dep in all_deps)


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestRDFLoaderErrorPaths:
    """Tests for error handling paths in RDF loader."""

    def test_load_ontology_file_not_found(self):
        """Test load_ontology raises FileNotFoundError for missing file."""
        from pathlib import Path

        from dppvalidator.vocabularies.rdf_loader import load_ontology

        with pytest.raises(FileNotFoundError) as exc_info:
            load_ontology(Path("/nonexistent/path/ontology.ttl"))

        assert "Ontology file not found" in str(exc_info.value)

    def test_load_ontology_parse_error(self):
        """Test load_ontology raises RuntimeError for invalid TTL content."""
        import tempfile
        from pathlib import Path

        from dppvalidator.vocabularies.rdf_loader import load_ontology

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as f:
            f.write("this is not valid turtle syntax @#$%^&*")
            temp_path = Path(f.name)

        try:
            with pytest.raises(RuntimeError) as exc_info:
                load_ontology(temp_path)
            assert "Failed to parse ontology" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_load_ontology_text_parse_error(self):
        """Test load_ontology_text raises RuntimeError for invalid content."""
        from dppvalidator.vocabularies.rdf_loader import load_ontology_text

        with pytest.raises(RuntimeError) as exc_info:
            load_ontology_text("invalid turtle @#$%^&* syntax")

        assert "Failed to parse ontology text" in str(exc_info.value)

    def test_load_bundled_ontology_not_found(self):
        """Test load_bundled_ontology raises FileNotFoundError for missing file."""
        from dppvalidator.vocabularies.rdf_loader import load_bundled_ontology

        with pytest.raises(FileNotFoundError) as exc_info:
            load_bundled_ontology("nonexistent_ontology.ttl")

        assert "Bundled ontology not found" in str(exc_info.value)

    def test_load_cirpass_shacl_shapes_success(self):
        """Test load_cirpass_shacl_shapes loads successfully."""
        from dppvalidator.vocabularies.rdf_loader import load_cirpass_shacl_shapes

        graph = load_cirpass_shacl_shapes()
        assert graph is not None
        assert len(graph) > 0

    def test_load_eudpp_core_ontology(self):
        """Test load_eudpp_core_ontology loads the product DPP ontology."""
        from dppvalidator.vocabularies.rdf_loader import load_eudpp_core_ontology

        graph = load_eudpp_core_ontology()
        assert graph is not None
        assert len(graph) > 0

    def test_load_actor_ontology(self):
        """Test load_actor_ontology loads the actors/roles ontology."""
        from dppvalidator.vocabularies.rdf_loader import load_actor_ontology

        graph = load_actor_ontology()
        assert graph is not None
        assert len(graph) > 0


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestRDFQueryFunctions:
    """Tests for RDF query functions."""

    def test_query_ontology_returns_results(self):
        """Test query_ontology returns list of dictionaries."""
        from dppvalidator.vocabularies.rdf_loader import (
            load_ontology_text,
            query_ontology,
        )

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org/TestClass> a owl:Class ;
            rdfs:label "Test Class" .
        """

        graph = load_ontology_text(ttl_content)
        query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5"
        results = query_ontology(graph, query)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)

    def test_query_ontology_empty_results(self):
        """Test query_ontology returns empty list for no matches."""
        from dppvalidator.vocabularies.rdf_loader import (
            load_ontology_text,
            query_ontology,
        )

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        <http://example.org/TestClass> a owl:Class .
        """

        graph = load_ontology_text(ttl_content)
        # Query for something that doesn't exist
        query = "SELECT ?s WHERE { ?s a <http://nonexistent.org/Type> }"
        results = query_ontology(graph, query)

        assert isinstance(results, list)
        assert len(results) == 0

    def test_get_ontology_classes_returns_classes(self):
        """Test get_ontology_classes extracts OWL classes."""
        from dppvalidator.vocabularies.rdf_loader import (
            get_ontology_classes,
            load_ontology_text,
        )

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org/ClassA> a owl:Class ;
            rdfs:label "Class A" .
        <http://example.org/ClassB> a owl:Class ;
            rdfs:label "Class B" .
        """

        graph = load_ontology_text(ttl_content)
        classes = get_ontology_classes(graph)

        assert isinstance(classes, list)
        assert len(classes) == 2
        assert "http://example.org/ClassA" in classes
        assert "http://example.org/ClassB" in classes

    def test_get_ontology_classes_empty_graph(self):
        """Test get_ontology_classes returns empty list for graph without classes."""
        from dppvalidator.vocabularies.rdf_loader import (
            get_ontology_classes,
            load_ontology_text,
        )

        ttl_content = """
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        <http://example.org/resource> rdfs:label "Just a resource" .
        """

        graph = load_ontology_text(ttl_content)
        classes = get_ontology_classes(graph)

        assert isinstance(classes, list)
        assert len(classes) == 0

    def test_get_ontology_properties_returns_properties(self):
        """Test get_ontology_properties extracts OWL properties."""
        from dppvalidator.vocabularies.rdf_loader import (
            get_ontology_properties,
            load_ontology_text,
        )

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org/objectProp> a owl:ObjectProperty ;
            rdfs:label "Object Property" .
        <http://example.org/dataProp> a owl:DatatypeProperty ;
            rdfs:label "Datatype Property" .
        """

        graph = load_ontology_text(ttl_content)
        properties = get_ontology_properties(graph)

        assert isinstance(properties, list)
        assert len(properties) == 2
        assert "http://example.org/objectProp" in properties
        assert "http://example.org/dataProp" in properties

    def test_get_ontology_properties_empty_graph(self):
        """Test get_ontology_properties returns empty list for graph without properties."""
        from dppvalidator.vocabularies.rdf_loader import (
            get_ontology_properties,
            load_ontology_text,
        )

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        <http://example.org/TestClass> a owl:Class .
        """

        graph = load_ontology_text(ttl_content)
        properties = get_ontology_properties(graph)

        assert isinstance(properties, list)
        assert len(properties) == 0


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestLoadAllOntologies:
    """Tests for loading merged ontologies."""

    def test_load_all_eudpp_ontologies_merges_graphs(self):
        """Test load_all_eudpp_ontologies merges multiple ontology files."""
        from dppvalidator.vocabularies.rdf_loader import load_all_eudpp_ontologies

        graph = load_all_eudpp_ontologies()

        assert graph is not None
        # Merged graph should have many triples from multiple files
        assert len(graph) > 100

    def test_load_all_eudpp_ontologies_handles_missing_files(self):
        """Test load_all_eudpp_ontologies skips missing files with warning."""
        from dppvalidator.vocabularies.rdf_loader import load_all_eudpp_ontologies

        # Should not raise even if some files are missing
        graph = load_all_eudpp_ontologies()
        assert graph is not None


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestRDFLoaderWithValidFile:
    """Tests for successful ontology loading from file."""

    def test_load_ontology_from_file(self):
        """Test load_ontology successfully loads from a valid file."""
        import tempfile
        from pathlib import Path

        from dppvalidator.vocabularies.rdf_loader import load_ontology

        ttl_content = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org/TestOntology> a owl:Ontology ;
            rdfs:label "Test Ontology" .
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as f:
            f.write(ttl_content)
            temp_path = Path(f.name)

        try:
            graph = load_ontology(temp_path)
            assert graph is not None
            assert len(graph) > 0
        finally:
            temp_path.unlink()

    def test_load_ontology_with_different_format(self):
        """Test load_ontology works with different RDF formats."""
        import tempfile
        from pathlib import Path

        from dppvalidator.vocabularies.rdf_loader import load_ontology

        # N-Triples format
        nt_content = '<http://example.org/subject> <http://example.org/predicate> "object" .\n'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".nt", delete=False) as f:
            f.write(nt_content)
            temp_path = Path(f.name)

        try:
            graph = load_ontology(temp_path, format="nt")
            assert graph is not None
            assert len(graph) == 1
        finally:
            temp_path.unlink()


class TestRDFAvailabilityCheckInternal:
    """Tests for internal RDF availability check function."""

    def test_check_rdflib_available_function_exists(self):
        """Test _check_rdflib_available function is importable."""
        from dppvalidator.vocabularies.rdf_loader import _check_rdflib_available

        assert _check_rdflib_available is not None

    @pytest.mark.skipif(is_rdf_available(), reason="Test only when rdflib not installed")
    def test_check_rdflib_available_raises_when_missing(self):
        """Test _check_rdflib_available raises RDFNotAvailableError."""
        from dppvalidator.vocabularies.rdf_loader import _check_rdflib_available

        with pytest.raises(RDFNotAvailableError):
            _check_rdflib_available()

    @pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
    def test_check_rdflib_available_succeeds_when_installed(self):
        """Test _check_rdflib_available succeeds when rdflib is installed."""
        from dppvalidator.vocabularies.rdf_loader import _check_rdflib_available

        # Should not raise
        _check_rdflib_available()


@pytest.mark.skipif(not is_rdf_available(), reason="rdflib not installed")
class TestRDFLoaderSHACLErrorPaths:
    """Tests for SHACL loading error paths."""

    def test_load_cirpass_shacl_shapes_parse_error(self):
        """Test load_cirpass_shacl_shapes handles malformed content."""
        import unittest.mock as mock

        from dppvalidator.vocabularies.rdf_loader import load_cirpass_shacl_shapes

        # Mock the file read to return invalid TTL
        mock_file = mock.MagicMock()
        mock_file.read_text.return_value = "invalid @#$ turtle content"

        mock_data_dir = mock.MagicMock()
        mock_data_dir.joinpath.return_value = mock_file

        with mock.patch(
            "dppvalidator.vocabularies.rdf_loader._get_schema_data_dir",
            return_value=mock_data_dir,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                load_cirpass_shacl_shapes()

            assert "Failed to load CIRPASS SHACL shapes" in str(exc_info.value)

    def test_load_bundled_ontology_runtime_error(self):
        """Test load_bundled_ontology wraps parsing errors in RuntimeError."""
        import unittest.mock as mock

        from dppvalidator.vocabularies.rdf_loader import load_bundled_ontology

        # Mock to return invalid content that will fail parsing
        mock_file = mock.MagicMock()
        mock_file.read_text.return_value = "completely @invalid@ turtle $syntax$"

        mock_data_dir = mock.MagicMock()
        mock_data_dir.joinpath.return_value = mock_file

        with mock.patch(
            "dppvalidator.vocabularies.rdf_loader._get_ontology_data_dir",
            return_value=mock_data_dir,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                load_bundled_ontology("test.ttl")

            assert "Failed to load bundled ontology" in str(exc_info.value)


class TestRDFLoaderDataDirectories:
    """Tests for data directory accessor functions."""

    def test_get_ontology_data_dir(self):
        """Test _get_ontology_data_dir returns a traversable."""
        from dppvalidator.vocabularies.rdf_loader import _get_ontology_data_dir

        data_dir = _get_ontology_data_dir()
        assert data_dir is not None

    def test_get_schema_data_dir(self):
        """Test _get_schema_data_dir returns a traversable."""
        from dppvalidator.vocabularies.rdf_loader import _get_schema_data_dir

        data_dir = _get_schema_data_dir()
        assert data_dir is not None
