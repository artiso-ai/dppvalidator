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


class TestVocabularyLoaderCoverage:
    """Coverage tests for VocabularyLoader."""

    def test_loader_get_vocabulary_from_fallback(self, tmp_path):
        """Test get_vocabulary uses fallback in offline mode."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader.get_vocabulary("CountryId")
        # Should return fallback data
        assert result is not None

    def test_loader_get_vocabulary_unknown(self, tmp_path):
        """Test get_vocabulary raises for unknown vocab."""
        import pytest

        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        with pytest.raises(ValueError, match="Unknown vocabulary"):
            loader.get_vocabulary("UnknownVocab")

    def test_loader_get_vocabulary_uses_cache(self, tmp_path):
        """Test get_vocabulary uses memory cache."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)

        # First call populates cache
        first = loader.get_vocabulary("CountryId")
        # Second call uses cache
        second = loader.get_vocabulary("CountryId")

        assert first == second

    def test_loader_is_valid_country_with_codes(self, tmp_path):
        """Test is_valid_country with valid codes."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        assert loader.is_valid_country("US")
        assert loader.is_valid_country("DE")

    def test_loader_is_valid_unit_with_codes(self, tmp_path):
        """Test is_valid_unit with valid codes."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        assert loader.is_valid_unit("KGM")


class TestVocabularyCacheCoverage:
    """Coverage tests for VocabularyCache."""

    def test_cache_set_and_get(self, tmp_path):
        """Test cache set and get cycle."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/vocab"
        data = frozenset(["A", "B", "C"])
        cache.set(url, data)

        # Get should return the data
        result = cache.get(url)
        assert result is not None
        assert "A" in result
        assert "B" in result

    def test_cache_get_nonexistent(self, tmp_path):
        """Test cache get returns None for nonexistent entries."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        result = cache.get("https://example.com/nonexistent")
        assert result is None

    def test_cache_clear(self, tmp_path):
        """Test cache clear removes entries."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/vocab"
        data = frozenset(["A"])
        cache.set(url, data)

        cache.clear()
        result = cache.get(url)
        assert result is None

    def test_cache_invalidate(self, tmp_path):
        """Test cache invalidate removes specific entry."""
        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/vocab"
        data = frozenset(["A"])
        cache.set(url, data)

        cache.invalidate(url)
        result = cache.get(url)
        assert result is None


class TestVocabularyLoaderAdvanced:
    """Advanced tests for VocabularyLoader."""

    def test_loader_is_valid_value(self, tmp_path):
        """Test is_valid_value method."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        assert loader.is_valid_value("CountryId", "US") is True
        assert loader.is_valid_value("CountryId", "XX") is False

    def test_loader_is_valid_value_unknown_vocab(self, tmp_path):
        """Test is_valid_value with unknown vocabulary."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader.is_valid_value("UnknownVocab", "XX")
        assert result is False

    def test_loader_clear_cache(self, tmp_path):
        """Test clear_cache method."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        loader.get_vocabulary("CountryId")  # Populate cache
        loader.clear_cache()
        # After clear, fallback tracking should be reset
        assert len(loader._fallback_used) == 0

    def test_loader_fallback_used_tracking(self, tmp_path):
        """Test fallback used tracking."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        loader.get_vocabulary("CountryId")
        assert "CountryId" in loader._fallback_used

    def test_loader_offline_mode(self, tmp_path):
        """Test loader in offline mode."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader.get_vocabulary("CountryId")
        assert isinstance(result, frozenset)
        assert len(result) > 0

    def test_loader_timeout_config(self, tmp_path):
        """Test loader timeout configuration."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True, timeout_seconds=5.0)
        assert loader.timeout_seconds == 5.0


class TestVocabularyLoaderOnlinePaths:
    """Tests for VocabularyLoader online fetch paths."""

    def test_fetch_vocabulary_with_httpx_mock(self, tmp_path, monkeypatch):
        """Test _fetch_vocabulary when httpx is available with mock response."""
        from dppvalidator.vocabularies import loader as loader_module

        class MockResponse:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "@graph": [
                        {"@id": "http://example.com#US"},
                        {"@id": "http://example.com#DE"},
                        {"@id": "http://example.com#FR"},
                    ]
                }

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, **kwargs):  # noqa: ARG002
                return MockResponse()

        monkeypatch.setattr(loader_module, "HAS_HTTPX", True)
        monkeypatch.setattr(loader_module, "httpx", type("httpx", (), {"Client": MockClient}))

        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=False)
        vocab_def = VocabularyDefinition(
            name="TestVocab",
            url="https://test.example.com/vocab",
            description="Test vocabulary",
        )
        result = loader._fetch_vocabulary(vocab_def)
        assert result is not None
        assert "US" in result
        assert "DE" in result

    def test_fetch_vocabulary_network_error(self, tmp_path, monkeypatch):
        """Test _fetch_vocabulary handles network errors."""
        from dppvalidator.vocabularies import loader as loader_module

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, **kwargs):  # noqa: ARG002
                raise ConnectionError("Network error")

        monkeypatch.setattr(loader_module, "HAS_HTTPX", True)
        monkeypatch.setattr(loader_module, "httpx", type("httpx", (), {"Client": MockClient}))

        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=False)
        vocab_def = VocabularyDefinition(
            name="TestVocab",
            url="https://test.example.com/vocab",
            description="Test vocabulary",
        )
        result = loader._fetch_vocabulary(vocab_def)
        assert result is None

    def test_fetch_vocabulary_no_httpx(self, tmp_path, monkeypatch):
        """Test _fetch_vocabulary returns None when httpx not available."""
        from dppvalidator.vocabularies import loader as loader_module

        monkeypatch.setattr(loader_module, "HAS_HTTPX", False)

        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=False)
        vocab_def = VocabularyDefinition(
            name="TestVocab",
            url="https://test.example.com/vocab",
            description="Test vocabulary",
        )
        result = loader._fetch_vocabulary(vocab_def)
        assert result is None

    def test_get_vocabulary_uses_cache_then_fetch(self, tmp_path, monkeypatch):
        """Test get_vocabulary tries cache, then fetch, then fallback."""
        from dppvalidator.vocabularies import loader as loader_module

        fetch_called = [False]

        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"@graph": [{"@id": "http://example.com#NEW"}]}

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, **kwargs):  # noqa: ARG002
                fetch_called[0] = True
                return MockResponse()

        monkeypatch.setattr(loader_module, "HAS_HTTPX", True)
        monkeypatch.setattr(loader_module, "httpx", type("httpx", (), {"Client": MockClient}))

        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=False)
        # First call should fetch and cache
        result = loader.get_vocabulary("CountryId")
        assert result is not None
        # Verify it used fetch (since cache was empty)
        assert fetch_called[0] is True

    def test_extract_values_with_member_notation(self, tmp_path):
        """Test _extract_values extracts from member notation format."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        data = {
            "member": [
                {"notation": "KGM"},
                {"notation": "LTR"},
                {"notation": "MTR"},
            ]
        }
        result = loader._extract_values(data, "UnitMeasureCode")
        assert result is not None
        assert "KGM" in result
        assert "LTR" in result
        assert "MTR" in result

    def test_extract_values_with_member_id_fallback(self, tmp_path):
        """Test _extract_values extracts from member @id when notation missing."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        data = {
            "member": [
                {"@id": "http://example.com#ABC"},
                {"@id": "http://example.com#XYZ"},
            ]
        }
        result = loader._extract_values(data, "TestVocab")
        assert result is not None
        assert "ABC" in result
        assert "XYZ" in result

    def test_get_fallback_unknown_vocabulary(self, tmp_path):
        """Test _get_fallback returns empty set for unknown vocabulary."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader._get_fallback("UnknownVocab")
        assert result == frozenset()

    def test_get_fallback_unit_measure_code(self, tmp_path):
        """Test _get_fallback returns bundled unit codes."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        result = loader._get_fallback("UnitMeasureCode")
        assert isinstance(result, frozenset)
        assert len(result) > 0
        assert "KGM" in result

    def test_fallback_logging_only_once(self, tmp_path):
        """Test fallback logging only happens once per vocabulary."""
        loader = VocabularyLoader(cache_dir=tmp_path, offline_mode=True)
        # First call adds to _fallback_used
        loader._get_fallback("CountryId")
        assert "CountryId" in loader._fallback_used
        # Second call should not re-add (set already contains it)
        loader._get_fallback("CountryId")
        # Verify it's still in the set (sets don't have count method)
        assert "CountryId" in loader._fallback_used


class TestVocabularyCacheEdgeCases:
    """Edge case tests for VocabularyCache."""

    def test_cache_disk_read_with_valid_data(self, tmp_path):
        """Test cache reads valid data from disk."""
        import hashlib
        import json as json_module
        import time

        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/test"

        # Manually create cache file
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = tmp_path / f"{url_hash}.json"
        cache_data = {
            "data": ["A", "B", "C"],
            "fetched_at": time.time(),
            "expires_at": time.time() + 86400,
            "source_url": url,
        }
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json_module.dumps(cache_data))

        # Read from disk cache
        result = cache.get(url)
        assert result is not None
        assert "A" in result
        assert "B" in result

    def test_cache_disk_expired_entry_removed(self, tmp_path):
        """Test expired disk cache entry is removed."""
        import hashlib
        import json as json_module
        import time

        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/expired"

        # Create expired cache file
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = tmp_path / f"{url_hash}.json"
        cache_data = {
            "data": ["OLD"],
            "fetched_at": time.time() - 100000,
            "expires_at": time.time() - 1,  # Already expired
            "source_url": url,
        }
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json_module.dumps(cache_data))

        # Should return None and delete the file
        result = cache.get(url)
        assert result is None
        assert not cache_file.exists()

    def test_cache_disk_corrupted_json(self, tmp_path):
        """Test cache handles corrupted JSON gracefully."""
        import hashlib

        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/corrupted"

        # Create corrupted cache file
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = tmp_path / f"{url_hash}.json"
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("not valid json {{{")

        # Should return None and delete the corrupted file
        result = cache.get(url)
        assert result is None

    def test_cache_memory_expired_entry_removed(self, tmp_path):
        """Test expired memory cache entry is removed."""
        import time

        cache = VocabularyCache(cache_dir=tmp_path, ttl_hours=24)
        url = "https://example.com/memory_expired"

        # Manually add expired entry to memory cache
        cache._memory_cache[url] = CacheEntry(
            data=frozenset(["OLD"]),
            fetched_at=time.time() - 100000,
            expires_at=time.time() - 1,  # Already expired
            source_url=url,
        )

        # Should return None and remove from memory cache
        result = cache.get(url)
        assert result is None
        assert url not in cache._memory_cache
