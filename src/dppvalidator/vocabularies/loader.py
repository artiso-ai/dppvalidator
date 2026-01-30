"""External vocabulary loader with HTTP caching and offline support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any, ClassVar

from dppvalidator.logging import get_logger
from dppvalidator.vocabularies.cache import VocabularyCache

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class VocabularyDefinition:
    """Definition of an external vocabulary."""

    name: str
    url: str
    description: str


VOCABULARIES: dict[str, VocabularyDefinition] = {
    "CountryId": VocabularyDefinition(
        name="CountryId",
        url="https://vocabulary.uncefact.org/CountryId",
        description="ISO 3166-1 country codes",
    ),
    "UnitMeasureCode": VocabularyDefinition(
        name="UnitMeasureCode",
        url="https://vocabulary.uncefact.org/UnitMeasureCode",
        description="UNECE Rec20 unit of measure codes",
    ),
}


def _get_data_files() -> Any:
    """Get the data directory using importlib.resources."""
    return files("dppvalidator.vocabularies").joinpath("data")


@lru_cache(maxsize=2)
def _load_bundled_vocabulary(name: str) -> frozenset[str]:
    """Load vocabulary codes from bundled JSON data file."""
    try:
        data_files = _get_data_files()
        data_file = data_files.joinpath(f"{name}.json")
        content = data_file.read_text()
        data = json.loads(content)
        return frozenset(data.get("codes", []))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load bundled vocabulary %s: %s", name, e)
        return frozenset()


def get_bundled_country_codes() -> frozenset[str]:
    """Get bundled ISO 3166-1 country codes."""
    return _load_bundled_vocabulary("countries")


def get_bundled_unit_codes() -> frozenset[str]:
    """Get bundled UNECE Rec20 unit codes."""
    return _load_bundled_vocabulary("units")


class VocabularyLoader:
    """Load and validate external vocabulary values.

    Fetches vocabulary data from UNCEFACT endpoints with caching
    and offline fallback support.
    """

    VOCABULARIES: ClassVar[dict[str, VocabularyDefinition]] = VOCABULARIES

    def __init__(
        self,
        cache_dir: Path | None = None,
        cache_ttl_hours: int = 24,
        offline_mode: bool = False,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize vocabulary loader.

        Args:
            cache_dir: Directory for cache files
            cache_ttl_hours: Cache TTL in hours
            offline_mode: If True, never make HTTP requests
            timeout_seconds: HTTP request timeout
        """
        self._cache = VocabularyCache(cache_dir, cache_ttl_hours)
        self.offline_mode = offline_mode
        self.timeout_seconds = timeout_seconds
        self._fallback_used: set[str] = set()

    def get_vocabulary(self, name: str) -> frozenset[str]:
        """Get vocabulary values by name.

        Args:
            name: Vocabulary name (e.g., "CountryId", "UnitMeasureCode")

        Returns:
            Set of valid vocabulary values

        Raises:
            ValueError: If vocabulary name is unknown
        """
        if name not in self.VOCABULARIES:
            raise ValueError(f"Unknown vocabulary: {name}")

        vocab_def = self.VOCABULARIES[name]

        cached = self._cache.get(vocab_def.url)
        if cached is not None:
            return cached

        if not self.offline_mode and HAS_HTTPX:
            fetched = self._fetch_vocabulary(vocab_def)
            if fetched is not None:
                self._cache.set(vocab_def.url, fetched)
                return fetched

        return self._get_fallback(name)

    def is_valid_value(self, vocabulary: str, value: str) -> bool:
        """Check if a value is valid for a vocabulary.

        Args:
            vocabulary: Vocabulary name
            value: Value to validate

        Returns:
            True if value is valid
        """
        try:
            vocab_values = self.get_vocabulary(vocabulary)
            return value in vocab_values
        except ValueError:
            return False

    def is_valid_country(self, code: str) -> bool:
        """Check if a country code is valid.

        Args:
            code: ISO 3166-1 alpha-2 country code

        Returns:
            True if valid
        """
        return self.is_valid_value("CountryId", code)

    def is_valid_unit(self, code: str) -> bool:
        """Check if a unit of measure code is valid.

        Args:
            code: UNECE Rec20 unit code

        Returns:
            True if valid
        """
        return self.is_valid_value("UnitMeasureCode", code)

    def _fetch_vocabulary(self, vocab_def: VocabularyDefinition) -> frozenset[str] | None:
        """Fetch vocabulary from HTTP endpoint.

        Args:
            vocab_def: Vocabulary definition

        Returns:
            Set of values or None on failure
        """
        if not HAS_HTTPX:
            return None

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(
                    vocab_def.url,
                    headers={"Accept": "application/json"},
                    follow_redirects=True,
                )
                response.raise_for_status()

                data = response.json()
                values = self._extract_values(data, vocab_def.name)
                if values:
                    logger.info("Fetched %d values for %s", len(values), vocab_def.name)
                    return values

        except OSError as e:
            logger.warning("Network error fetching vocabulary %s: %s", vocab_def.name, e)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Invalid response for vocabulary %s: %s", vocab_def.name, e)

        return None

    def _extract_values(self, data: dict | list, vocab_name: str) -> frozenset[str] | None:  # noqa: ARG002
        """Extract vocabulary values from JSON response.

        Args:
            data: JSON response data
            vocab_name: Vocabulary name for context

        Returns:
            Set of extracted values
        """
        values: set[str] = set()

        if isinstance(data, dict):
            if "@graph" in data:
                for item in data["@graph"]:
                    if isinstance(item, dict):
                        code = item.get("@id", "").split("#")[-1]
                        if code:
                            values.add(code)
            elif "member" in data:
                for member in data.get("member", []):
                    if isinstance(member, dict):
                        code = member.get("notation") or member.get("@id", "").split("#")[-1]
                        if code:
                            values.add(code)

        if values:
            return frozenset(values)
        return None

    def _get_fallback(self, name: str) -> frozenset[str]:
        """Get fallback vocabulary values.

        Args:
            name: Vocabulary name

        Returns:
            Fallback set of common values
        """
        if name not in self._fallback_used:
            logger.info("Using fallback values for %s", name)
            self._fallback_used.add(name)

        if name == "CountryId":
            return get_bundled_country_codes()
        if name == "UnitMeasureCode":
            return get_bundled_unit_codes()

        return frozenset()

    def clear_cache(self) -> None:
        """Clear all cached vocabulary data."""
        self._cache.clear()
        self._fallback_used.clear()

    @property
    def available_vocabularies(self) -> list[str]:
        """List of available vocabulary names."""
        return list(self.VOCABULARIES.keys())
