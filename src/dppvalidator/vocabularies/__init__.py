"""External vocabulary loading and validation."""

from dppvalidator.vocabularies.cache import CacheEntry, VocabularyCache
from dppvalidator.vocabularies.loader import (
    VOCABULARIES,
    VocabularyDefinition,
    VocabularyLoader,
    get_bundled_country_codes,
    get_bundled_unit_codes,
)

__all__ = [
    # Loader
    "VocabularyLoader",
    "VocabularyDefinition",
    "VOCABULARIES",
    # Cache
    "VocabularyCache",
    "CacheEntry",
    # Bundled data accessors
    "get_bundled_country_codes",
    "get_bundled_unit_codes",
]
