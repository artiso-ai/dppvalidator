"""Schema registry with version management and integrity verification.

Phase 2 of the CIRPASS-2 migration extended this module to a two-axis
registry keyed by ``(SchemaFamily, version)``. The single-string
``SCHEMA_REGISTRY`` and ``DEFAULT_SCHEMA_VERSION`` constants are kept as
back-compat *derived views* of the tuple-keyed source of truth — every
existing UNTP caller continues to work unchanged. New code should use
:data:`SCHEMA_REGISTRY_BY_FAMILY` and :data:`DEFAULT_VERSIONS` directly.

Cardinal rule §1 still allows bare version literals here (this is one
of the two registry-source files); CIRPASS / EUDPP-module literals are
allowed for the same reason (Phase 1 cardinal-rule extension §1.2 of
the migration plan).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class SchemaFamily(str, Enum):
    """Top-level schema family.

    Phase 2 of the CIRPASS-2 migration introduced this axis. UNTP and
    CIRPASS are *parallel* validated families (see the migration plan's
    §2 Target State). EUDPP-LD is a serialization format on top of
    either family — not a third family.
    """

    UNTP = "untp"
    CIRPASS = "cirpass"


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """Schema version definition with integrity metadata.

    Attributes:
        version: SemVer version string (e.g. ``0.6.1``, ``0.7.0``,
            ``1.3.0``).
        url: SHA-pinned upstream URL the bundled bytes were vendored from.
            Used for re-pulling and integrity diffs; not for runtime fetch.
        sha256: SHA-256 of the LF-normalised bundled bytes; ``None`` when
            the schema isn't bundled (legacy 0.6.0 entry; CIRPASS 1.3.0
            placeholder until Phase 3 derives the JSON Schema).
        context_urls: JSON-LD context URIs that pair with this schema
            version (W3C VC v2 + family-specific context per version).
        production_url: Optional canonical production URL — the
            human-friendly "how-the-spec-publishes-it" URL (e.g.
            ``https://untp.unece.org/...``). When set, the bytes at
            this URL are byte-for-byte identical to those at :attr:`url`
            (verified at vendor time); the SHA pin is enforced against
            the bundled copy regardless. The two-URL split lets the
            registry record provenance ("where does this schema *live*?")
            separately from integrity ("what bytes did we ship?").
        family: Which schema family this row belongs to (UNTP or
            CIRPASS). Defaults to UNTP for back-compat with pre-Phase-2
            consumers that constructed :class:`SchemaVersion` instances
            directly.
        vocabulary_hub_guid: Opaque DPP Vocabulary Hub GUID
            (``OntologyVersion_<uuid>`` / ``JsonSchemaVersion_<uuid>``)
            that identifies this artefact in the upstream catalog.
            Phase 2 added this field; ``None`` for rows that predate the
            hub (legacy UNTP rows).
    """

    version: str
    url: str
    sha256: str | None
    context_urls: tuple[str, ...]
    production_url: str | None = None
    family: SchemaFamily = SchemaFamily.UNTP
    vocabulary_hub_guid: str | None = None

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


# =============================================================================
# Source of truth: (family, version) -> SchemaVersion
# =============================================================================
#
# Phase 2 of docs/plans/CIRPASS_2_MIGRATION.md keys the registry on the
# two-axis ``(SchemaFamily, version)`` tuple. The bare-string
# ``SCHEMA_REGISTRY`` below is derived from this for back-compat with
# every existing UNTP caller; the bare-string view filters to the UNTP
# family only (CIRPASS rows are reachable only via the tuple-keyed
# lookup or the family-aware ``SchemaRegistry.get_schema_for`` API).


SCHEMA_REGISTRY_BY_FAMILY: dict[tuple[SchemaFamily, str], SchemaVersion] = {
    (SchemaFamily.UNTP, "0.6.0"): SchemaVersion(
        version="0.6.0",
        url="https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.0.json",
        sha256=None,  # Schema not bundled locally
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
        ),
        family=SchemaFamily.UNTP,
    ),
    (SchemaFamily.UNTP, "0.6.1"): SchemaVersion(
        version="0.6.1",
        url="https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json",
        sha256="c0fdd7da5d23b6aec5d1d0ce198ca8d1cd67ca27609395a1b4961b3d1a8549a8",
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ),
        family=SchemaFamily.UNTP,
    ),
    # UNTP 0.7.0. Two URLs are tracked: ``url`` is the SHA-pinned upstream
    # raw URL we vendored from; ``production_url`` is the canonical
    # production hosting at ``untp.unece.org`` (verified bit-identical to
    # the SHA-pinned source on 2026-05-08 — same SHA-256). The
    # production CloudFront mirror for the JSON-LD context is captured
    # under ``context_urls`` below. The ``sha256`` pins the bundled file
    # at src/dppvalidator/schemas/data/untp-dpp-schema-0.7.0.json
    # (vendored in Phase 2 of UNTP 0.7.0 migration). The hash is
    # cross-verified by tests/unit/test_manifest_integrity.py.
    (SchemaFamily.UNTP, "0.7.0"): SchemaVersion(
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
        family=SchemaFamily.UNTP,
    ),
    # CIRPASS-2 reference structure v1.3.0 — Phase 2 task 2.5 of the
    # migration plan. The JSON Schema bytes do not yet exist; Phase 3
    # task 3.1 derives them from the hub's tree-view export via
    # ``tools/codegen/cirpass/derive_schema.py`` and commits the result
    # at ``src/dppvalidator/schemas/data/cirpass-reference-1.3.0.json``.
    # Until then, ``sha256=None`` is the placeholder (mirrors the
    # legacy UNTP 0.6.0 entry which is also ``sha256=None``). The
    # vocabulary-hub GUID identifies the upstream artefact even before
    # the bytes are derived.
    (SchemaFamily.CIRPASS, "1.3.0"): SchemaVersion(
        version="1.3.0",
        url=("https://dpp.vocabulary-hub.eu/specifications#cirpass-dpp-reference-structure-v1.3.0"),
        # Phase 3 task 3.2: SHA pins the bytes derived by
        # tools/codegen/cirpass/derive_schema.py from the canonical
        # ``ReferencePassport`` Pydantic model. The drift gate
        # (tools/codegen/check_drift.py) re-runs the generator on
        # every CI build and compares against this hash.
        sha256="3c957b6a5c6e9d92ae582e1c2acd20bb73820be8d27860cffdb5b721489025a6",
        context_urls=(
            "https://www.w3.org/ns/credentials/v2",
            "https://w3id.org/eudpp/",
        ),
        family=SchemaFamily.CIRPASS,
        vocabulary_hub_guid=None,  # message-tree GUID; populate when paired (see Phase 3/Phase 0 OA)
    ),
}


# =============================================================================
# Default versions per family
# =============================================================================


DEFAULT_VERSIONS: dict[SchemaFamily, str] = {
    # Phase 9 task 9.1 (2026-05-09): flipped from "0.6.1" to "0.7.0"
    # for the dppvalidator 0.5.0 Preview cut. v0.6.x remains supported
    # via auto-detection and the v0.6 → v0.7 upgrade shim.
    SchemaFamily.UNTP: "0.7.0",
    SchemaFamily.CIRPASS: "1.3.0",
}


# =============================================================================
# Back-compat single-string view
# =============================================================================
#
# Pre-Phase-2 callers used a bare-string ``SCHEMA_REGISTRY[version]``
# lookup against UNTP rows. Phase 2 kept this working as a derived
# view of the tuple-keyed source of truth.
#
# **Phase 9 task 9.4 (dppvalidator 0.5.0):** the bare-string lookup
# now emits a ``DeprecationWarning`` on every ``__getitem__``. The
# tuple-keyed :data:`SCHEMA_REGISTRY_BY_FAMILY` is the source of truth.
# Iteration / membership / ``.get()`` / ``.values()`` remain warning-
# free for read-only inspection; only the bare-string indexed lookup
# triggers the warning.
#
# **Phase 10 (dppvalidator 0.6.0):** this view will be removed
# entirely.
#
# Cardinal rule §1 lists this file as the sole place bare-string
# UNTP version literals are allowed.


class _DeprecatedSchemaRegistryDict(dict[str, "SchemaVersion"]):
    """Dict subclass that warns on bare-string indexed lookup.

    See Phase 9 task 9.4 in
    ``docs/plans/CIRPASS_2_MIGRATION.md``. Use the tuple-keyed
    :data:`SCHEMA_REGISTRY_BY_FAMILY` or the registry's ``get_schema``
    helper instead.
    """

    def __getitem__(self, key: str) -> SchemaVersion:
        import warnings

        warnings.warn(
            "Bare-string SCHEMA_REGISTRY[version] lookup is deprecated "
            "since dppvalidator 0.5.0; use SCHEMA_REGISTRY_BY_FAMILY[(family, version)] "
            "or SchemaRegistry().get_schema(version, family=...). The bare-string "
            "view will be removed in 0.6.0 (Phase 10 of CIRPASS_2_MIGRATION.md).",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__getitem__(key)


SCHEMA_REGISTRY: _DeprecatedSchemaRegistryDict = _DeprecatedSchemaRegistryDict(
    {
        schema.version: schema
        for (family, _), schema in SCHEMA_REGISTRY_BY_FAMILY.items()
        if family is SchemaFamily.UNTP
    }
)


DEFAULT_SCHEMA_VERSION = DEFAULT_VERSIONS[SchemaFamily.UNTP]


class SchemaRegistry:
    """Registry for DPP schema versions.

    Phase 2 of the CIRPASS-2 migration extended this class with
    family-aware lookup methods (``get_schema_for``, ``available_for``,
    etc.). The historic single-string methods (``get_schema``,
    ``get_schema_url``, ``get_context_urls``, ``available_versions``)
    continue to operate against the UNTP family only, preserving
    pre-Phase-2 caller behaviour.
    """

    SCHEMAS: ClassVar[dict[str, SchemaVersion]] = SCHEMA_REGISTRY
    SCHEMAS_BY_FAMILY: ClassVar[dict[tuple[SchemaFamily, str], SchemaVersion]] = (
        SCHEMA_REGISTRY_BY_FAMILY
    )
    DEFAULT_VERSION: ClassVar[str] = DEFAULT_SCHEMA_VERSION

    def get_schema(self, version: str | None = None) -> SchemaVersion:
        """Get UNTP schema version definition by bare-string lookup.

        Pre-Phase-2 API. Always resolves against the UNTP family. New
        code should use :meth:`get_schema_for` with an explicit family.

        Args:
            version: Schema version string. Uses :data:`DEFAULT_SCHEMA_VERSION`
                if None.

        Returns:
            SchemaVersion instance

        Raises:
            ValueError: If version not found in the UNTP family
        """
        v = version or self.DEFAULT_VERSION
        if v not in self.SCHEMAS:
            available = ", ".join(self.SCHEMAS.keys())
            raise ValueError(f"Unknown schema version: {v}. Available: {available}")
        return self.SCHEMAS[v]

    def get_schema_for(
        self,
        family: SchemaFamily,
        version: str | None = None,
    ) -> SchemaVersion:
        """Get schema version definition by ``(family, version)`` (Phase 2).

        Args:
            family: ``SchemaFamily.UNTP`` or ``SchemaFamily.CIRPASS``.
            version: Schema version string. Uses
                :data:`DEFAULT_VERSIONS[family]` if None.

        Returns:
            SchemaVersion instance

        Raises:
            ValueError: If ``(family, version)`` not registered
        """
        v = version or DEFAULT_VERSIONS[family]
        key = (family, v)
        if key not in self.SCHEMAS_BY_FAMILY:
            available = ", ".join(f"({f.value}, {ver})" for f, ver in self.SCHEMAS_BY_FAMILY)
            raise ValueError(f"Unknown schema {(family.value, v)!r}. Available: {available}")
        return self.SCHEMAS_BY_FAMILY[key]

    def get_schema_url(self, version: str | None = None) -> str:
        """Get UNTP schema URL for a version (pre-Phase-2 API)."""
        return self.get_schema(version).url

    def get_context_urls(self, version: str | None = None) -> tuple[str, ...]:
        """Get UNTP JSON-LD context URLs for a version (pre-Phase-2 API)."""
        return self.get_schema(version).context_urls

    def get_production_url(self, version: str | None = None) -> str | None:
        """Return the canonical production URL for the UNTP schema, if known.

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
        """List of available UNTP schema versions (pre-Phase-2 API)."""
        return list(self.SCHEMAS.keys())

    @property
    def default_version(self) -> str:
        """Default UNTP schema version (pre-Phase-2 API)."""
        return self.DEFAULT_VERSION

    def available_for(self, family: SchemaFamily) -> list[str]:
        """List of available schema versions for a given family (Phase 2)."""
        return [v for (f, v) in self.SCHEMAS_BY_FAMILY if f is family]

    @property
    def available_families(self) -> list[SchemaFamily]:
        """List of registered schema families (Phase 2)."""
        return list({f for (f, _) in self.SCHEMAS_BY_FAMILY})
