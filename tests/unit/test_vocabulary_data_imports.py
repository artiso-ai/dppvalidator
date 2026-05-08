"""Tests for vocabulary data file imports via importlib.resources.

These tests ensure that all bundled data files are properly packaged
and accessible at runtime.
"""

import json

import pytest


class TestVocabularyDataPackages:
    """Tests that vocabulary data packages are importable."""

    def test_vocabularies_data_package_exists(self):
        """Test that vocabularies.data package is importable."""
        from importlib.resources import files

        data_pkg = files("dppvalidator.vocabularies.data")
        assert data_pkg is not None

    def test_vocabularies_data_ontologies_package_exists(self):
        """Test that vocabularies.data.ontologies package is importable."""
        from importlib.resources import files

        ontologies_pkg = files("dppvalidator.vocabularies.data.ontologies")
        assert ontologies_pkg is not None

    def test_vocabularies_data_schemas_package_exists(self):
        """Test that vocabularies.data.schemas package is importable."""
        from importlib.resources import files

        schemas_pkg = files("dppvalidator.vocabularies.data.schemas")
        assert schemas_pkg is not None


class TestBundledJsonFiles:
    """Tests for bundled JSON vocabulary files."""

    def test_countries_json_exists_and_valid(self):
        """Test countries.json is bundled and valid JSON."""
        from importlib.resources import files

        data_pkg = files("dppvalidator.vocabularies.data")
        countries_file = data_pkg.joinpath("countries.json")
        content = countries_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, dict)
        assert "codes" in data or isinstance(data, list) or len(data) > 0

    def test_units_json_exists_and_valid(self):
        """Test units.json is bundled and valid JSON."""
        from importlib.resources import files

        data_pkg = files("dppvalidator.vocabularies.data")
        units_file = data_pkg.joinpath("units.json")
        content = units_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, (dict, list))

    def test_materials_json_exists_and_valid(self):
        """Test materials.json is bundled and valid JSON."""
        from importlib.resources import files

        data_pkg = files("dppvalidator.vocabularies.data")
        materials_file = data_pkg.joinpath("materials.json")
        content = materials_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, (dict, list))

    def test_hs_codes_json_exists_and_valid(self):
        """Test hs_codes.json is bundled and valid JSON."""
        from importlib.resources import files

        data_pkg = files("dppvalidator.vocabularies.data")
        hs_codes_file = data_pkg.joinpath("hs_codes.json")
        content = hs_codes_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, (dict, list))


class TestBundledOntologyFiles:
    """Tests for bundled ontology TTL files."""

    @pytest.mark.parametrize(
        "filename",
        [
            "eudpp_core_v1.3.1.ttl",
            "product_dpp_v1.7.1.ttl",
            "actors_roles_v1.5.1.ttl",
            "lca_v2.0.ttl",
            "soc_v1.4.7.ttl",
        ],
    )
    def test_ontology_ttl_files_exist(self, filename):
        """Test that ontology TTL files are bundled."""
        from importlib.resources import files

        ontologies_pkg = files("dppvalidator.vocabularies.data.ontologies")
        ttl_file = ontologies_pkg.joinpath(filename)

        # Check file exists and has content
        content = ttl_file.read_text(encoding="utf-8")
        assert len(content) > 0
        assert "@prefix" in content or "prefix" in content.lower()


class TestBundledSchemaFiles:
    """Tests for bundled CIRPASS schema files."""

    def test_cirpass_schema_json_exists(self):
        """Test cirpass_dpp_schema.json is bundled and valid."""
        from importlib.resources import files

        schemas_pkg = files("dppvalidator.vocabularies.data.schemas")
        schema_file = schemas_pkg.joinpath("cirpass_dpp_schema.json")
        content = schema_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, dict)
        assert "$schema" in data or "type" in data or "properties" in data

    def test_cirpass_shacl_ttl_exists(self):
        """Test cirpass_dpp_shacl.ttl is bundled."""
        from importlib.resources import files

        schemas_pkg = files("dppvalidator.vocabularies.data.schemas")
        shacl_file = schemas_pkg.joinpath("cirpass_dpp_shacl.ttl")
        content = shacl_file.read_text(encoding="utf-8")

        assert len(content) > 0
        assert "sh:" in content or "shacl" in content.lower() or "@prefix" in content

    def test_cirpass_openapi_json_exists(self):
        """Test cirpass_dpp_openapi.json is bundled and valid."""
        from importlib.resources import files

        schemas_pkg = files("dppvalidator.vocabularies.data.schemas")
        openapi_file = schemas_pkg.joinpath("cirpass_dpp_openapi.json")
        content = openapi_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert isinstance(data, dict)


class TestVocabularyLoaderIntegration:
    """Integration tests for vocabulary loading functions."""

    def test_get_bundled_country_codes_returns_data(self):
        """Test get_bundled_country_codes returns non-empty frozenset."""
        from dppvalidator.vocabularies.loader import get_bundled_country_codes

        codes = get_bundled_country_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0

    def test_get_bundled_unit_codes_returns_data(self):
        """Test get_bundled_unit_codes returns non-empty frozenset."""
        from dppvalidator.vocabularies.loader import get_bundled_unit_codes

        codes = get_bundled_unit_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0


class TestCodeListsLoader:
    """Tests for code_lists module loading."""

    def test_get_material_codes_returns_data(self):
        """Test loading material codes via code_lists module."""
        from dppvalidator.vocabularies.code_lists import get_material_codes

        codes = get_material_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0

    def test_get_hs_codes_returns_data(self):
        """Test loading HS codes via code_lists module."""
        from dppvalidator.vocabularies.code_lists import get_hs_codes

        codes = get_hs_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0

    def test_is_valid_material_code(self):
        """Test material code validation."""
        from dppvalidator.vocabularies.code_lists import (
            get_material_codes,
            is_valid_material_code,
        )

        codes = get_material_codes()
        if codes:
            sample_code = next(iter(codes))
            assert is_valid_material_code(sample_code) is True

    def test_is_valid_hs_code(self):
        """Test HS code validation."""
        from dppvalidator.vocabularies.code_lists import get_hs_codes, is_valid_hs_code

        codes = get_hs_codes()
        if codes:
            sample_code = next(iter(codes))
            assert is_valid_hs_code(sample_code) is True
