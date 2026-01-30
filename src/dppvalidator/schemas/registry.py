"""Schema registry with version management and integrity verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """Schema version definition with integrity metadata."""

    version: str
    url: str
    sha256: str | None
    context_urls: tuple[str, ...]

    def verify_integrity(self, content: bytes) -> bool:
        """Verify content matches expected SHA-256 hash.

        Args:
            content: Schema content bytes

        Returns:
            True if hash matches or no hash specified
        """
        if self.sha256 is None:
            return True
        # Normalize line endings to LF for consistent hashing across platforms
        normalized = content.replace(b"\r\n", b"\n")
        computed = hashlib.sha256(normalized).hexdigest()
        return computed == self.sha256


SCHEMA_REGISTRY: dict[str, SchemaVersion] = {
    "0.6.0": SchemaVersion(
        version="0.6.0",
        url="https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.0.json",
        sha256=None,  # Schema not bundled locally
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
        ),
    ),
    "0.6.1": SchemaVersion(
        version="0.6.1",
        url="https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json",
        sha256="c0fdd7da5d23b6aec5d1d0ce198ca8d1cd67ca27609395a1b4961b3d1a8549a8",
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ),
    ),
}

DEFAULT_SCHEMA_VERSION = "0.6.1"


class SchemaRegistry:
    """Registry for UNTP DPP schema versions."""

    SCHEMAS: ClassVar[dict[str, SchemaVersion]] = SCHEMA_REGISTRY
    DEFAULT_VERSION: ClassVar[str] = DEFAULT_SCHEMA_VERSION

    def get_schema(self, version: str | None = None) -> SchemaVersion:
        """Get schema version definition.

        Args:
            version: Schema version string. Uses default if None.

        Returns:
            SchemaVersion instance

        Raises:
            ValueError: If version not found
        """
        v = version or self.DEFAULT_VERSION
        if v not in self.SCHEMAS:
            available = ", ".join(self.SCHEMAS.keys())
            raise ValueError(f"Unknown schema version: {v}. Available: {available}")
        return self.SCHEMAS[v]

    def get_schema_url(self, version: str | None = None) -> str:
        """Get schema URL for a version.

        Args:
            version: Schema version

        Returns:
            Schema URL string
        """
        return self.get_schema(version).url

    def get_context_urls(self, version: str | None = None) -> tuple[str, ...]:
        """Get JSON-LD context URLs for a version.

        Args:
            version: Schema version

        Returns:
            Tuple of context URLs
        """
        return self.get_schema(version).context_urls

    @property
    def available_versions(self) -> list[str]:
        """List of available schema versions."""
        return list(self.SCHEMAS.keys())

    @property
    def default_version(self) -> str:
        """Default schema version."""
        return self.DEFAULT_VERSION
