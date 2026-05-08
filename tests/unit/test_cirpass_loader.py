"""Tests for CIRPASS schema loader (Phase 5)."""

from dppvalidator.schemas.cirpass_loader import (
    CIRPASS_SCHEMA_FILE,
    CIRPASS_SCHEMA_TITLE,
    CIRPASS_SCHEMA_VERSION,
    CIRPASSSchemaLoader,
    CIRPASSSHACLLoader,
    get_cirpass_schema,
    get_cirpass_schema_version,
)


class TestCIRPASSSchemaConstants:
    """Tests for CIRPASS schema constants."""

    def test_schema_version(self):
        """Test schema version constant."""
        assert CIRPASS_SCHEMA_VERSION == "1.3.0"

    def test_schema_title(self):
        """Test schema title constant."""
        assert CIRPASS_SCHEMA_TITLE == "CIRPASS DPP reference structure"

    def test_schema_file(self):
        """Test schema file constant."""
        assert CIRPASS_SCHEMA_FILE == "cirpass_dpp_schema.json"


class TestCIRPASSSchemaLoader:
    """Tests for CIRPASSSchemaLoader class."""

    def test_create_loader(self):
        """Test creating a schema loader."""
        loader = CIRPASSSchemaLoader()
        assert loader.SCHEMA_VERSION == "1.3.0"
        assert loader._schema is None

    def test_load_schema(self):
        """Test loading the CIRPASS schema."""
        loader = CIRPASSSchemaLoader()
        schema = loader.load()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "title" in schema

    def test_load_schema_cached(self):
        """Test schema is cached after first load."""
        loader = CIRPASSSchemaLoader()
        schema1 = loader.load()
        schema2 = loader.load()

        assert schema1 is schema2

    def test_schema_id(self):
        """Test getting schema ID."""
        loader = CIRPASSSchemaLoader()
        schema_id = loader.schema_id

        assert "CIRPASS DPP reference structure" in schema_id

    def test_schema_version_property(self):
        """Test getting schema version from property."""
        loader = CIRPASSSchemaLoader()
        version = loader.schema_version

        assert version == "1.3.0"

    def test_json_schema_draft(self):
        """Test getting JSON Schema draft version."""
        loader = CIRPASSSchemaLoader()
        draft = loader.json_schema_draft

        assert "json-schema.org" in draft
        assert "2020-12" in draft

    def test_get_property_names(self):
        """Test getting property names from schema."""
        loader = CIRPASSSchemaLoader()
        properties = loader.get_property_names()

        assert isinstance(properties, list)
        assert len(properties) > 0
        assert "uniqueDPPID" in properties
        assert "appliesToProduct" in properties

    def test_get_property_schema(self):
        """Test getting schema for a specific property."""
        loader = CIRPASSSchemaLoader()
        prop_schema = loader.get_property_schema("uniqueDPPID")

        assert prop_schema is not None
        assert "type" in prop_schema

    def test_get_property_schema_not_found(self):
        """Test getting schema for unknown property."""
        loader = CIRPASSSchemaLoader()
        prop_schema = loader.get_property_schema("unknownProperty")

        assert prop_schema is None

    def test_has_property_true(self):
        """Test has_property returns True for existing property."""
        loader = CIRPASSSchemaLoader()

        assert loader.has_property("uniqueDPPID")
        assert loader.has_property("appliesToProduct")

    def test_has_property_false(self):
        """Test has_property returns False for unknown property."""
        loader = CIRPASSSchemaLoader()

        assert not loader.has_property("unknownProperty")

    def test_is_additional_properties_allowed(self):
        """Test checking if additional properties are allowed."""
        loader = CIRPASSSchemaLoader()

        # CIRPASS schema has additionalProperties: false
        assert not loader.is_additional_properties_allowed()

    def test_clear_cache(self):
        """Test clearing the schema cache."""
        loader = CIRPASSSchemaLoader()
        loader.load()  # Load to populate cache
        assert loader._schema is not None

        loader.clear_cache()
        assert loader._schema is None


class TestCIRPASSSHACLLoader:
    """Tests for CIRPASSSHACLLoader class."""

    def test_create_shacl_loader(self):
        """Test creating a SHACL loader."""
        loader = CIRPASSSHACLLoader()
        assert loader.SHACL_FILE == "cirpass_dpp_shacl.ttl"
        assert loader._shapes_text is None

    def test_load_shacl_text(self):
        """Test loading SHACL shapes as text."""
        loader = CIRPASSSHACLLoader()
        shapes = loader.load_text()

        assert isinstance(shapes, str)
        assert len(shapes) > 0
        # SHACL files contain these prefixes
        assert "@prefix" in shapes or "PREFIX" in shapes

    def test_load_shacl_cached(self):
        """Test SHACL shapes are cached after first load."""
        loader = CIRPASSSHACLLoader()
        shapes1 = loader.load_text()
        shapes2 = loader.load_text()

        assert shapes1 is shapes2

    def test_clear_shacl_cache(self):
        """Test clearing the SHACL cache."""
        loader = CIRPASSSHACLLoader()
        loader.load_text()  # Load to populate cache
        assert loader._shapes_text is not None

        loader.clear_cache()
        assert loader._shapes_text is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_cirpass_schema(self):
        """Test get_cirpass_schema function."""
        schema = get_cirpass_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "title" in schema

    def test_get_cirpass_schema_version(self):
        """Test get_cirpass_schema_version function."""
        version = get_cirpass_schema_version()

        assert version == "1.3.0"


class TestSchemaIntegrity:
    """Tests for schema integrity and structure."""

    def test_schema_has_required_dpp_properties(self):
        """Test schema has required DPP properties."""
        loader = CIRPASSSchemaLoader()
        properties = loader.get_property_names()

        # Required DPP properties per ESPR
        required_props = [
            "uniqueDPPID",
            "validFrom",
            "appliesToProduct",
        ]

        for prop in required_props:
            assert prop in properties, f"Missing required property: {prop}"

    def test_schema_applies_to_product_structure(self):
        """Test appliesToProduct has expected structure."""
        loader = CIRPASSSchemaLoader()
        prop_schema = loader.get_property_schema("appliesToProduct")

        assert prop_schema is not None
        # appliesToProduct is an array of objects
        assert prop_schema.get("type") == "array"
        assert "items" in prop_schema

    def test_schema_is_valid_json_schema(self):
        """Test schema is valid JSON Schema draft 2020-12."""
        loader = CIRPASSSchemaLoader()
        schema = loader.load()

        # Check JSON Schema properties
        assert "$schema" in schema
        assert "https://json-schema.org/draft/2020-12/schema" in schema["$schema"]


class TestSchemaLoaderImports:
    """Tests for schema loader imports from package."""

    def test_import_from_schemas_package(self):
        """Test importing from schemas package."""
        from dppvalidator.schemas import (
            CIRPASS_SCHEMA_VERSION,
            CIRPASSSchemaLoader,
            CIRPASSSHACLLoader,
            get_cirpass_schema,
            get_cirpass_schema_version,
        )

        assert CIRPASSSchemaLoader is not None
        assert CIRPASSSHACLLoader is not None
        assert CIRPASS_SCHEMA_VERSION == "1.3.0"
        assert get_cirpass_schema is not None
        assert get_cirpass_schema_version is not None


class TestCIRPASSSchemaLoaderErrorPaths:
    """Tests for error handling in schema loader."""

    def test_load_file_not_found_raises_runtime_error(self):
        """FileNotFoundError during load raises RuntimeError."""
        from unittest.mock import MagicMock, patch

        import pytest

        loader = CIRPASSSchemaLoader()
        loader._schema = None  # Reset cache

        mock_data_dir = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.side_effect = FileNotFoundError("Schema file not found")
        mock_data_dir.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.schemas.cirpass_loader._get_cirpass_schema_dir",
            return_value=mock_data_dir,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()

            assert "not found" in str(exc_info.value).lower()

    def test_load_invalid_json_raises_runtime_error(self):
        """JSONDecodeError during load raises RuntimeError."""
        from unittest.mock import MagicMock, patch

        import pytest

        loader = CIRPASSSchemaLoader()
        loader._schema = None  # Reset cache

        mock_data_dir = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.return_value = "{ invalid json }"
        mock_data_dir.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.schemas.cirpass_loader._get_cirpass_schema_dir",
            return_value=mock_data_dir,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                loader.load()

            assert "invalid json" in str(exc_info.value).lower()

    def test_schema_version_fallback_when_no_v_in_title(self):
        """schema_version falls back to default when no 'v' in title."""
        from unittest.mock import patch

        loader = CIRPASSSchemaLoader()

        # Mock load to return a schema without version in title
        with patch.object(loader, "load", return_value={"title": "CIRPASS Schema"}):
            version = loader.schema_version

        assert version == loader.SCHEMA_VERSION
