"""Schema loader with caching and integrity verification."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from dppvalidator.logging import get_logger
from dppvalidator.schemas.registry import (
    DEFAULT_SCHEMA_VERSION,
    SchemaRegistry,
    SchemaVersion,
)

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    HAS_HTTPX = False

logger = get_logger(__name__)


def _get_schema_data_dir() -> Any:
    """Get the schema data directory using importlib.resources."""
    return files("dppvalidator.schemas").joinpath("data")


class SchemaLoader:
    """Load and cache UNTP DPP schemas.

    Provides schema loading from:
    1. Bundled local files (data/ directory)
    2. Remote URLs with optional caching
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize schema loader.

        Args:
            cache_dir: Directory to cache downloaded schemas
            timeout_seconds: HTTP request timeout
        """
        self._registry = SchemaRegistry()
        self._cache_dir = cache_dir or (Path.home() / ".cache" / "dppvalidator" / "schemas")
        self.timeout_seconds = timeout_seconds
        self._schema_cache: dict[str, dict[str, Any]] = {}

    def load_schema(self, version: str | None = None) -> dict[str, Any]:
        """Load schema for a version.

        Attempts loading in order:
        1. Memory cache
        2. Bundled local file
        3. Disk cache
        4. Remote URL (with caching)

        Args:
            version: Schema version. Uses default if None.

        Returns:
            Parsed JSON schema as dictionary

        Raises:
            ValueError: If version unknown
            RuntimeError: If schema cannot be loaded
        """
        v = version or DEFAULT_SCHEMA_VERSION
        schema_def = self._registry.get_schema(v)

        if v in self._schema_cache:
            return self._schema_cache[v]

        schema = self._load_local(schema_def)
        if schema is None:
            schema = self._load_cached(schema_def)
        if schema is None:
            schema = self._fetch_remote(schema_def)

        if schema is None:
            raise RuntimeError(f"Failed to load schema {v}")

        self._schema_cache[v] = schema
        return schema

    def _load_local(self, schema_def: SchemaVersion) -> dict[str, Any] | None:
        """Load schema from bundled data directory."""
        try:
            data_dir = _get_schema_data_dir()
            local_file = data_dir.joinpath(f"untp-dpp-schema-{schema_def.version}.json")
            content = local_file.read_bytes()
            if not schema_def.verify_integrity(content):
                logger.warning("Schema %s failed integrity check", schema_def.version)
                return None
            return json.loads(content)
        except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
            logger.debug("Failed to load local schema %s: %s", schema_def.version, e)
            return None

    def _load_cached(self, schema_def: SchemaVersion) -> dict[str, Any] | None:
        """Load schema from disk cache."""
        cache_path = self._cache_dir / f"untp-dpp-schema-{schema_def.version}.json"
        if not cache_path.exists():
            return None

        try:
            content = cache_path.read_bytes()
            if not schema_def.verify_integrity(content):
                logger.warning("Cached schema %s failed integrity check", schema_def.version)
                cache_path.unlink(missing_ok=True)
                return None
            return json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load cached schema %s: %s", schema_def.version, e)
            return None

    def _fetch_remote(self, schema_def: SchemaVersion) -> dict[str, Any] | None:
        """Fetch schema from remote URL and cache."""
        if not HAS_HTTPX:
            logger.warning("httpx not installed, cannot fetch remote schema")
            return None

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(schema_def.url, follow_redirects=True)
                response.raise_for_status()

            content = response.content
            if not schema_def.verify_integrity(content):
                logger.warning("Remote schema %s failed integrity check", schema_def.version)
                return None

            self._cache_to_disk(schema_def.version, content)

            logger.info("Fetched schema %s from %s", schema_def.version, schema_def.url)
            return response.json()

        except OSError as e:
            logger.warning("Network error fetching schema %s: %s", schema_def.version, e)
            return None
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in schema %s: %s", schema_def.version, e)
            return None

    def _cache_to_disk(self, version: str, content: bytes) -> None:
        """Cache schema content to disk."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = self._cache_dir / f"untp-dpp-schema-{version}.json"
            cache_path.write_bytes(content)
        except OSError as e:
            logger.warning("Failed to cache schema %s: %s", version, e)

    def clear_cache(self) -> None:
        """Clear memory and disk cache."""
        self._schema_cache.clear()
        if self._cache_dir.exists():
            for cache_file in self._cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)

    def download_schema(self, version: str, output_dir: Path | None = None) -> Path:
        """Download schema to specified directory.

        Args:
            version: Schema version to download
            output_dir: Output directory. Uses current dir if None.

        Returns:
            Path to downloaded schema file

        Raises:
            RuntimeError: If download fails
        """
        schema_def = self._registry.get_schema(version)
        out_dir = output_dir or Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"untp-dpp-schema-{version}.json"

        if not HAS_HTTPX:
            raise RuntimeError("httpx required for download. Install with: pip install httpx")

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(schema_def.url, follow_redirects=True)
                response.raise_for_status()

            out_path.write_bytes(response.content)
            logger.info("Downloaded schema %s to %s", version, out_path)
            return out_path

        except OSError as e:
            raise RuntimeError(f"Failed to download schema {version}: {e}") from e
