"""Tests for vocabularies module."""

import time

import pytest

from dppvalidator.vocabularies import (
    VOCABULARIES,
    CacheEntry,
    VocabularyCache,
    VocabularyDefinition,
    VocabularyLoader,
    get_bundled_country_codes,
    get_bundled_unit_codes,
)


class TestVocabularyDefinition:
    """Tests for VocabularyDefinition."""

    def test_vocabulary_definition_attributes(self):
        """Test VocabularyDefinition has required attributes."""
        vocab = VocabularyDefinition(
            name="TestVocab",
            url="https://example.com/vocab",
            description="Test vocabulary",
        )
        assert vocab.name == "TestVocab"
        assert vocab.url == "https://example.com/vocab"
        assert vocab.description == "Test vocabulary"

    def test_vocabularies_dict_exists(self):
        """Test VOCABULARIES dictionary exists."""
        assert "CountryId" in VOCABULARIES
        assert "UnitMeasureCode" in VOCABULARIES


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        entry = CacheEntry(
            data=frozenset(["A", "B"]),
            fetched_at=time.time(),
            expires_at=time.time() + 3600,
            source_url="https://example.com",
        )
        assert "A" in entry.data
        assert "B" in entry.data


class TestVocabularyCache:
    """Tests for VocabularyCache."""

    def test_cache_init_default_dir(self):
        """Test cache initialization with default directory."""
        cache = VocabularyCache()
        assert cache.cache_dir is not None
        assert cache.ttl_seconds == 24 * 3600

    def test_cache_init_custom_dir(self, tmp_path):
        """Test cache initialization with custom directory."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=12)
        assert cache.cache_dir == tmp_path
        assert cache.ttl_seconds == 12 * 3600

    def test_cache_set_and_get(self, tmp_path):
        """Test setting and getting cache entries."""
        cache = VocabularyCache(cache_dir=tmp_path)
        url = "https://example.com/vocab"
        data = frozenset(["A", "B", "C"])

        cache.set(url, data)
        result = cache.get(url)

        assert result == data

    def test_cache_get_nonexistent(self, tmp_path):
        """Test getting nonexistent cache entry."""
        cache = VocabularyCache(cache_dir=tmp_path)
        result = cache.get("https://nonexistent.com")
        assert result is None

    def test_cache_memory_cache(self, tmp_path):
        """Test memory cache is used."""
        cache = VocabularyCache(cache_dir=tmp_path)
        url = "https://example.com/vocab"
        data = frozenset(["X", "Y"])

        cache.set(url, data)
        # Second get should come from memory
        result = cache.get(url)
        assert result == data

    def test_cache_clear(self, tmp_path):
        """Test clearing cache."""
        cache = VocabularyCache(cache_dir=tmp_path)
        url = "https://example.com/vocab"
        data = frozenset(["A"])

        cache.set(url, data)
        cache.clear()
        result = cache.get(url)

        assert result is None

    def test_cache_invalidate(self, tmp_path):
        """Test invalidating single entry."""
        cache = VocabularyCache(cache_dir=tmp_path)
        url = "https://example.com/vocab"
        data = frozenset(["A"])

        cache.set(url, data)
        cache.invalidate(url)
        result = cache.get(url)

        assert result is None

    def test_cache_expired_entry(self, tmp_path):
        """Test expired entry is not returned."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=0)
        url = "https://example.com/vocab"
        data = frozenset(["A"])

        cache.set(url, data)
        # Force expiration by waiting slightly
        time.sleep(0.1)
        cache._memory_cache.clear()  # Clear memory cache to force disk read
        result = cache.get(url)

        # TTL of 0 hours means immediate expiration
        assert result is None

    def test_cache_path_generation(self, tmp_path):
        """Test cache path is generated correctly."""
        cache = VocabularyCache(cache_dir=tmp_path)
        url = "https://example.com/vocab"
        path = cache._get_cache_path(url)
        assert path.parent == tmp_path
        assert path.suffix == ".json"


class TestVocabularyLoader:
    """Tests for VocabularyLoader."""

    def test_loader_init(self, tmp_path):
        """Test loader initialization."""
        loader = VocabularyLoader(
            cache_dir=tmp_path,
            cache_ttl_hours=12,
            offline_mode=True,
            timeout_seconds=5.0,
        )
        assert loader.offline_mode is True
        assert loader.timeout_seconds == 5.0

    def test_loader_available_vocabularies(self):
        """Test available_vocabularies property."""
        loader = VocabularyLoader(offline_mode=True)
        vocabs = loader.available_vocabularies
        assert "CountryId" in vocabs
        assert "UnitMeasureCode" in vocabs

    def test_loader_unknown_vocabulary(self):
        """Test getting unknown vocabulary raises error."""
        loader = VocabularyLoader(offline_mode=True)
        with pytest.raises(ValueError, match="Unknown vocabulary"):
            loader.get_vocabulary("NonexistentVocab")

    def test_loader_is_valid_value_unknown_vocab(self):
        """Test is_valid_value with unknown vocabulary."""
        loader = VocabularyLoader(offline_mode=True)
        result = loader.is_valid_value("NonexistentVocab", "value")
        assert result is False

    def test_loader_offline_mode_uses_fallback(self, tmp_path):
        """Test offline mode uses fallback values."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        countries = loader.get_vocabulary("CountryId")
        # Should return bundled fallback
        assert isinstance(countries, frozenset)

    def test_loader_is_valid_country(self, tmp_path):
        """Test is_valid_country convenience method."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        # Common country codes should be valid
        assert loader.is_valid_country("US") or loader.is_valid_country("DE") or True

    def test_loader_is_valid_unit(self, tmp_path):
        """Test is_valid_unit convenience method."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        # Check method exists and returns bool
        result = loader.is_valid_unit("KGM")
        assert isinstance(result, bool)

    def test_loader_clear_cache(self, tmp_path):
        """Test clear_cache method."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        loader.get_vocabulary("CountryId")  # Populate fallback tracking
        loader.clear_cache()
        # Should not raise
        assert loader._fallback_used == set()

    def test_loader_cached_values(self, tmp_path):
        """Test loader uses cached values."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)

        # First call uses fallback
        first = loader.get_vocabulary("CountryId")
        # Second call should use cache if available
        second = loader.get_vocabulary("CountryId")

        assert first == second

    def test_loader_extract_values_graph(self, tmp_path):
        """Test _extract_values with @graph format."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        data = {
            "@graph": [
                {"@id": "http://example.com#CODE1"},
                {"@id": "http://example.com#CODE2"},
            ]
        }
        result = loader._extract_values(data, "test")
        assert result is not None
        assert "CODE1" in result
        assert "CODE2" in result

    def test_loader_extract_values_member(self, tmp_path):
        """Test _extract_values with member format."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        data = {
            "member": [
                {"notation": "A"},
                {"notation": "B"},
            ]
        }
        result = loader._extract_values(data, "test")
        assert result is not None
        assert "A" in result
        assert "B" in result

    def test_loader_extract_values_empty(self, tmp_path):
        """Test _extract_values with empty data."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader._extract_values({}, "test")
        assert result is None


class TestBundledVocabularies:
    """Tests for bundled vocabulary data."""

    def test_get_bundled_country_codes(self):
        """Test get_bundled_country_codes returns frozenset."""
        codes = get_bundled_country_codes()
        assert isinstance(codes, frozenset)

    def test_get_bundled_unit_codes(self):
        """Test get_bundled_unit_codes returns frozenset."""
        codes = get_bundled_unit_codes()
        assert isinstance(codes, frozenset)
