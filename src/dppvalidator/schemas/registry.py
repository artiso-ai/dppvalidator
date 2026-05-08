"""Schema registry with version management and integrity verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """Schema version definition with integrity metadata.

    Attributes:
        version: SemVer version string (e.g. ``0.6.1``, ``0.7.0``).
        url: SHA-pinned upstream URL the bundled bytes were vendored from.
            Used for re-pulling and integrity diffs; not for runtime fetch.
        sha256: SHA-256 of the LF-normalised bundled bytes; ``None`` when
            the schema isn't bundled (legacy 0.6.0 entry).
        context_urls: JSON-LD context URIs that pair with this schema
            version (W3C VC + UNTP DPP context per version).
        production_url: Optional canonical production URL — the
            human-friendly "how-the-spec-publishes-it" URL (e.g.
            ``https://untp.unece.org/...``). When set, the bytes at
            this URL are byte-for-byte identical to those at :attr:`url`
            (verified at vendor time); the SHA pin is enforced against
            the bundled copy regardless. The two-URL split lets the
            registry record provenance ("where does this schema *live*?")
            separately from integrity ("what bytes did we ship?").
    """

    version: str
    url: str
    sha256: str | None
    context_urls: tuple[str, ...]
    production_url: str | None = None

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
    # UNTP 0.7.0. Two URLs are tracked: ``url`` is the SHA-pinned upstream
    # raw URL we vendored from; ``production_url`` is the canonical
    # production hosting at ``untp.unece.org`` (verified bit-identical to
    # the SHA-pinned source on 2026-05-08 — same SHA-256). The
    # production CloudFront mirror for the JSON-LD context is captured
    # under ``context_urls`` below. The ``sha256`` pins the bundled file
    # at src/dppvalidator/schemas/data/untp-dpp-schema-0.7.0.json
    # (vendored in Phase 2, see docs/plans/UNTP_0.7.0_MIGRATION.md). The
    # hash is cross-verified by tests/unit/test_manifest_integrity.py.
    "0.7.0": SchemaVersion(
        version="0.7.0",
        url=(
            "https://opensource.unicc.org/un/unece/uncefact/spec-untp/-/raw/"
            "707cd5267deddede24bb74e453a758561972a109/artefacts/schema/v0.7.0/dpp/"
            "DigitalProductPassport.json"
        ),
        sha256="42c51943ab23547d5287899fd12b214b19b006c28d105a70ff390f8551b12653",
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ),
        production_url=(
            "https://untp.unece.org/artefacts/schema/v0.7.0/dpp/DigitalProductPassport.json"
        ),
    ),
}

DEFAULT_SCHEMA_VERSION = "0.6.1"  # Phase 9 will flip this to "0.7.0" in dppvalidator 0.5.0.


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

    def get_production_url(self, version: str | None = None) -> str | None:
        """Return the canonical production URL for the schema, if known.

        The production URL is the human-friendly hosting (e.g.
        ``https://untp.unece.org/...``) — distinct from the SHA-pinned
        :meth:`get_schema_url`, which points at the immutable source the
        bytes were vendored from. Both URLs serve the same bytes; the
        split lets callers reach for whichever URL is appropriate
        (documentation links → production_url; integrity diff →
        ``url``). Returns ``None`` for versions that have no published
        production URL recorded.
        """
        return self.get_schema(version).production_url

    @property
    def available_versions(self) -> list[str]:
        """List of available schema versions."""
        return list(self.SCHEMAS.keys())

    @property
    def default_version(self) -> str:
        """Default schema version."""
        return self.DEFAULT_VERSION
