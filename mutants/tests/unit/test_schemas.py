"""Tests for schema registry and loader."""

import pytest

from dppvalidator.schemas import (
    DEFAULT_SCHEMA_VERSION,
    SchemaLoader,
    SchemaRegistry,
    SchemaVersion,
)


class TestSchemaVersion:
    """Tests for SchemaVersion."""

    def test_verify_integrity_no_hash(self):
        """Test integrity verification with no hash."""
        version = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        assert version.verify_integrity(b"any content") is True

    def test_verify_integrity_matching_hash(self):
        """Test integrity verification with matching hash."""
        import hashlib

        content = b'{"test": "schema"}'
        expected_hash = hashlib.sha256(content).hexdigest()

        version = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256=expected_hash,
            context_urls=(),
        )
        assert version.verify_integrity(content) is True

    def test_verify_integrity_mismatched_hash(self):
        """Test integrity verification with wrong hash."""
        version = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256="wronghash",
            context_urls=(),
        )
        assert version.verify_integrity(b"any content") is False


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""

    def test_default_version(self):
        """Test default version is 0.6.1."""
        registry = SchemaRegistry()
        assert registry.default_version == "0.6.1"

    def test_available_versions(self):
        """Test listing available versions."""
        registry = SchemaRegistry()
        versions = registry.available_versions
        assert "0.6.1" in versions
        assert "0.6.0" in versions

    def test_get_schema(self):
        """Test getting schema definition."""
        registry = SchemaRegistry()
        schema = registry.get_schema("0.6.1")
        assert schema.version == "0.6.1"
        assert "untp-dpp-schema-0.6.1" in schema.url

    def test_get_schema_default(self):
        """Test getting default schema."""
        registry = SchemaRegistry()
        schema = registry.get_schema()
        assert schema.version == DEFAULT_SCHEMA_VERSION

    def test_get_schema_unknown(self):
        """Test getting unknown version raises."""
        registry = SchemaRegistry()
        with pytest.raises(ValueError, match="Unknown schema version"):
            registry.get_schema("9.9.9")

    def test_get_context_urls(self):
        """Test getting context URLs."""
        registry = SchemaRegistry()
        urls = registry.get_context_urls("0.6.1")
        assert "https://www.w3.org/ns/credentials/v2" in urls
        assert any("untp/dpp/0.6.1" in url for url in urls)


class TestSchemaLoader:
    """Tests for SchemaLoader."""

    def test_init(self):
        """Test loader initialization."""
        loader = SchemaLoader()
        assert loader.timeout_seconds == 30.0

    def test_init_custom_params(self, tmp_path):
        """Test loader initialization with custom params."""
        loader = SchemaLoader(cache_dir=tmp_path, timeout_seconds=10.0)
        assert loader.timeout_seconds == 10.0
        assert loader._cache_dir == tmp_path

    def test_load_schema_unknown_version(self):
        """Test loading unknown version raises."""
        loader = SchemaLoader()
        with pytest.raises(ValueError, match="Unknown schema version"):
            loader.load_schema("9.9.9")

    def test_clear_cache(self, tmp_path):
        """Test clearing cache."""
        loader = SchemaLoader(cache_dir=tmp_path)
        # Create a cache file
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "test.json").write_text("{}")
        loader.clear_cache()
        # Memory cache should be empty
        assert loader._schema_cache == {}

    def test_load_schema_uses_memory_cache(self, tmp_path):
        """Test that memory cache is used."""
        loader = SchemaLoader(cache_dir=tmp_path)
        # Pre-populate memory cache
        loader._schema_cache["0.6.1"] = {"$schema": "test"}
        result = loader.load_schema("0.6.1")
        assert result == {"$schema": "test"}

    def test_load_schema_default_version(self, tmp_path):
        """Test loading default version."""
        loader = SchemaLoader(cache_dir=tmp_path)
        # Pre-populate cache
        loader._schema_cache[DEFAULT_SCHEMA_VERSION] = {"default": True}
        result = loader.load_schema()  # No version specified
        assert result == {"default": True}

    def test_load_local_nonexistent(self, tmp_path):
        """Test _load_local with nonexistent file."""
        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        result = loader._load_local(schema_def)
        assert result is None

    def test_load_cached_nonexistent(self, tmp_path):
        """Test _load_cached with nonexistent file."""
        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        result = loader._load_cached(schema_def)
        assert result is None

    def test_load_cached_valid(self, tmp_path):
        """Test _load_cached with valid cache file."""
        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256=None,  # No integrity check
            context_urls=(),
        )
        # Create cache file
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file = tmp_path / "untp-dpp-schema-test.json"
        cache_file.write_text('{"cached": true}')

        result = loader._load_cached(schema_def)
        assert result == {"cached": True}

    def test_load_cached_integrity_failure(self, tmp_path):
        """Test _load_cached with integrity check failure."""
        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256="wronghash",  # Will fail integrity
            context_urls=(),
        )
        # Create cache file
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file = tmp_path / "untp-dpp-schema-test.json"
        cache_file.write_text('{"cached": true}')

        result = loader._load_cached(schema_def)
        assert result is None
        # File should be deleted
        assert not cache_file.exists()

    def test_cache_to_disk(self, tmp_path):
        """Test _cache_to_disk."""
        loader = SchemaLoader(cache_dir=tmp_path)
        content = b'{"test": true}'
        loader._cache_to_disk("0.6.1", content)
        cache_file = tmp_path / "untp-dpp-schema-0.6.1.json"
        assert cache_file.exists()
        assert cache_file.read_bytes() == content

    def test_download_schema_no_httpx(self, tmp_path, monkeypatch):
        """Test download_schema without httpx."""
        import dppvalidator.schemas.loader as loader_module

        monkeypatch.setattr(loader_module, "HAS_HTTPX", False)

        loader = SchemaLoader(cache_dir=tmp_path)
        with pytest.raises(RuntimeError, match="httpx required"):
            loader.download_schema("0.6.1", tmp_path)

    def test_fetch_remote_no_httpx(self, tmp_path, monkeypatch):
        """Test _fetch_remote without httpx."""
        import dppvalidator.schemas.loader as loader_module

        monkeypatch.setattr(loader_module, "HAS_HTTPX", False)

        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="0.6.1",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        result = loader._fetch_remote(schema_def)
        assert result is None
