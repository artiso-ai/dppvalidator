"""JSON-LD context management for UNTP DPP versions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextDefinition:
    """JSON-LD context definition for a specific schema version."""

    version: str
    contexts: tuple[str, ...]
    default_type: tuple[str, ...]


CONTEXTS: dict[str, ContextDefinition] = {
    "0.6.0": ContextDefinition(
        version="0.6.0",
        contexts=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.0/",
        ),
        default_type=("DigitalProductPassport", "VerifiableCredential"),
    ),
    "0.6.1": ContextDefinition(
        version="0.6.1",
        contexts=(
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ),
        default_type=("DigitalProductPassport", "VerifiableCredential"),
    ),
    # UNTP 0.7.0 unifies DPP, DCC, DFR, DIA and DTE under one context served
    # at vocabulary.uncefact.org/untp/0.7.0/context/. The DigitalProductPassport
    # type itself is unchanged in name; the credentialSubject envelope is what
    # restructures (see docs/plans/UNTP_0.7.0_MIGRATION.md §2.3).
    "0.7.0": ContextDefinition(
        version="0.7.0",
        contexts=(
            "https://www.w3.org/ns/credentials/v2",
            "https://vocabulary.uncefact.org/untp/0.7.0/context/",
        ),
        default_type=("DigitalProductPassport", "VerifiableCredential"),
    ),
}

DEFAULT_VERSION = "0.6.1"  # Phase 9 will flip this to "0.7.0" in dppvalidator 0.5.0.


class ContextManager:
    """Manages JSON-LD contexts for different schema versions."""

    def __init__(self, version: str = DEFAULT_VERSION) -> None:
        """Initialize context manager.

        Args:
            version: Schema version to use for context resolution
        """
        self.version = version

    def get_context(self, version: str | None = None) -> list[str]:
        """Get context URLs for a schema version.

        Args:
            version: Schema version. Uses default if None.

        Returns:
            List of context URLs
        """
        v = version or self.version
        if v not in CONTEXTS:
            v = DEFAULT_VERSION
        return list(CONTEXTS[v].contexts)

    def get_type(self, version: str | None = None) -> list[str]:
        """Get default type array for a schema version.

        Args:
            version: Schema version. Uses default if None.

        Returns:
            List of type strings
        """
        v = version or self.version
        if v not in CONTEXTS:
            v = DEFAULT_VERSION
        return list(CONTEXTS[v].default_type)

    def validate_context(self, context: list[str], version: str | None = None) -> bool:
        """Validate that context matches expected values.

        Args:
            context: Context URLs to validate
            version: Schema version to validate against

        Returns:
            True if context is valid for the version
        """
        expected = self.get_context(version)
        return all(url in context for url in expected)

    @property
    def available_versions(self) -> list[str]:
        """List of available schema versions."""
        return list(CONTEXTS.keys())
