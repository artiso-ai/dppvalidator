"""CIRPASS DPP Schema loader.

Provides loading and caching of CIRPASS DPP JSON Schemas from bundled
data files for validation of EU DPP data structures.

Source: CIRPASS-2 project vocabulary hub
Schema: cirpass_dpp_schema.json (v1.3.0)
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from dppvalidator.logging import get_logger

logger = get_logger(__name__)


# Schema metadata
CIRPASS_SCHEMA_VERSION = "1.3.0"
CIRPASS_SCHEMA_TITLE = "CIRPASS DPP reference structure"
CIRPASS_SCHEMA_FILE = "cirpass_dpp_schema.json"


def _get_cirpass_schema_dir() -> Any:
    """Get the CIRPASS schema data directory using importlib.resources."""
    return files("dppvalidator.vocabularies.data.schemas")


class CIRPASSSchemaLoader:
    """Load and cache CIRPASS DPP JSON Schema.

    Provides schema loading from bundled data files in the vocabularies
    package. The schema is cached after first load for performance.

    Example:
        >>> loader = CIRPASSSchemaLoader()
        >>> schema = loader.load()
        >>> print(loader.schema_id)
        'CIRPASS DPP reference structure v1.3.0'
    """

    SCHEMA_VERSION = CIRPASS_SCHEMA_VERSION

    def __init__(self) -> None:
        """Initialize CIRPASS schema loader."""
        self._schema: dict[str, Any] | None = None
        self._schema_file = CIRPASS_SCHEMA_FILE

    def load(self) -> dict[str, Any]:
        """Load and cache the CIRPASS DPP schema.

        Returns:
            Parsed JSON schema as dictionary

        Raises:
            RuntimeError: If schema cannot be loaded
        """
        if self._schema is not None:
            return self._schema

        try:
            data_dir = _get_cirpass_schema_dir()
            schema_path = data_dir.joinpath(self._schema_file)
            content = schema_path.read_text(encoding="utf-8")
            self._schema = json.loads(content)
            logger.debug("Loaded CIRPASS schema v%s", self.SCHEMA_VERSION)
            return self._schema
        except FileNotFoundError as e:
            msg = f"CIRPASS schema file not found: {self._schema_file}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in CIRPASS schema: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    @property
    def schema_id(self) -> str:
        """Get the schema title/ID.

        Returns:
            Schema title string from the loaded schema
        """
        return self.load().get("title", "")

    @property
    def schema_version(self) -> str:
        """Get the schema version.

        Returns:
            Version string extracted from schema title
        """
        title = self.schema_id
        # Extract version from title like "CIRPASS DPP reference structure v1.3.0"
        if " v" in title:
            return title.split(" v")[-1]
        return self.SCHEMA_VERSION

    @property
    def json_schema_draft(self) -> str:
        """Get the JSON Schema draft version.

        Returns:
            JSON Schema $schema URI
        """
        return self.load().get("$schema", "")

    def get_property_names(self) -> list[str]:
        """Get all top-level property names from the schema.

        Returns:
            List of property names defined in the schema
        """
        schema = self.load()
        properties = schema.get("properties", {})
        return list(properties.keys())

    def get_property_schema(self, property_name: str) -> dict[str, Any] | None:
        """Get schema definition for a specific property.

        Args:
            property_name: Name of the property

        Returns:
            Property schema definition, or None if not found
        """
        schema = self.load()
        properties = schema.get("properties", {})
        return properties.get(property_name)

    def has_property(self, property_name: str) -> bool:
        """Check if schema defines a property.

        Args:
            property_name: Name of the property

        Returns:
            True if property is defined in schema
        """
        return self.get_property_schema(property_name) is not None

    def is_additional_properties_allowed(self) -> bool:
        """Check if schema allows additional properties.

        Returns:
            True if additionalProperties is not false
        """
        schema = self.load()
        return schema.get("additionalProperties", True) is not False

    def clear_cache(self) -> None:
        """Clear the cached schema."""
        self._schema = None


class CIRPASSSHACLLoader:
    """Load and cache CIRPASS DPP SHACL shapes.

    Provides loading of SHACL constraint shapes from bundled data files
    for RDF validation of EU DPP data.

    Note: SHACL validation requires rdflib which is an optional dependency.
    """

    SHACL_FILE = "cirpass_dpp_shacl.ttl"

    def __init__(self) -> None:
        """Initialize CIRPASS SHACL loader."""
        self._shapes_text: str | None = None

    def load_text(self) -> str:
        """Load SHACL shapes as text.

        Returns:
            SHACL shapes file content as string

        Raises:
            RuntimeError: If SHACL file cannot be loaded
        """
        if self._shapes_text is not None:
            return self._shapes_text

        try:
            data_dir = _get_cirpass_schema_dir()
            shacl_path = data_dir.joinpath(self.SHACL_FILE)
            self._shapes_text = shacl_path.read_text(encoding="utf-8")
            logger.debug("Loaded CIRPASS SHACL shapes")
            return self._shapes_text
        except FileNotFoundError as e:
            msg = f"CIRPASS SHACL file not found: {self.SHACL_FILE}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def clear_cache(self) -> None:
        """Clear the cached SHACL shapes."""
        self._shapes_text = None


def get_cirpass_schema() -> dict[str, Any]:
    """Convenience function to load CIRPASS schema.

    Returns:
        Parsed CIRPASS DPP JSON schema

    Example:
        >>> schema = get_cirpass_schema()
        >>> print(schema["title"])
        'CIRPASS DPP reference structure v1.3.0'
    """
    loader = CIRPASSSchemaLoader()
    return loader.load()


def get_cirpass_schema_version() -> str:
    """Get the CIRPASS schema version.

    Returns:
        Version string (e.g., "1.3.0")
    """
    return CIRPASS_SCHEMA_VERSION
