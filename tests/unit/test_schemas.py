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
            version="9.9.9",
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

    def test_load_local_integrity_failure(self, tmp_path, monkeypatch):
        """Test _load_local with integrity check failure."""
        from dppvalidator.schemas import loader as loader_module

        # Mock _get_schema_data_dir to return tmp_path
        monkeypatch.setattr(loader_module, "_get_schema_data_dir", lambda: tmp_path)

        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256="wronghash",
            context_urls=(),
        )
        # Create local file
        local_file = tmp_path / "untp-dpp-schema-test.json"
        local_file.write_text('{"local": true}')

        result = loader._load_local(schema_def)
        assert result is None

    def test_clear_cache_removes_files(self, tmp_path):
        """Test clear_cache removes cached files."""
        loader = SchemaLoader(cache_dir=tmp_path)

        # Create some cache files
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "untp-dpp-schema-0.6.1.json").write_text("{}")
        (tmp_path / "untp-dpp-schema-0.5.0.json").write_text("{}")

        # Add to memory cache
        loader._schema_cache["0.6.1"] = {}

        loader.clear_cache()

        assert len(loader._schema_cache) == 0
        assert len(list(tmp_path.glob("*.json"))) == 0

    def test_load_schema_from_memory_cache(self, tmp_path):
        """Test load_schema uses memory cache on second call."""
        loader = SchemaLoader(cache_dir=tmp_path)

        # Pre-populate memory cache
        cached_schema = {"cached": True}
        loader._schema_cache["0.6.1"] = cached_schema

        result = loader.load_schema("0.6.1")
        assert result is cached_schema

    def test_load_schema_raises_on_failure(self, tmp_path, monkeypatch):
        """Test load_schema raises RuntimeError when all methods fail."""
        from dppvalidator.schemas import loader as loader_module

        # Mock to simulate failure: no local files, no cache, network error
        monkeypatch.setattr(loader_module, "_get_schema_data_dir", lambda: tmp_path / "nonexistent")

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, **kwargs):  # noqa: ARG002
                raise ConnectionError("Network error")

        monkeypatch.setattr(loader_module.httpx, "Client", MockClient)

        loader = SchemaLoader(cache_dir=tmp_path / "also_nonexistent")

        with pytest.raises(RuntimeError, match="Failed to load schema"):
            loader.load_schema("0.6.1")

    def test_load_schema_from_cached_after_local_fails(self, tmp_path, monkeypatch):
        """Test load_schema tries cache when local fails."""
        from dppvalidator.schemas import loader as loader_module

        monkeypatch.setattr(loader_module, "_get_schema_data_dir", lambda: tmp_path / "nonexistent")

        loader = SchemaLoader(cache_dir=tmp_path)

        # Create valid cache file (use 0.6.0 which has no SHA-256 hash)
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file = tmp_path / "untp-dpp-schema-0.6.0.json"
        cache_file.write_text('{"$schema": "test"}')

        result = loader.load_schema("0.6.0")
        assert result == {"$schema": "test"}

    def test_load_cached_json_decode_error(self, tmp_path):
        """Test _load_cached handles JSON decode errors."""
        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        # Create invalid JSON cache file
        tmp_path.mkdir(parents=True, exist_ok=True)
        cache_file = tmp_path / "untp-dpp-schema-test.json"
        cache_file.write_text("not valid json {")

        result = loader._load_cached(schema_def)
        assert result is None

    def test_cache_to_disk_oserror(self, tmp_path, monkeypatch):
        """Test _cache_to_disk handles OS errors gracefully."""
        loader = SchemaLoader(cache_dir=tmp_path / "readonly")

        # Mock mkdir to raise OSError
        def mock_mkdir(*_args, **_kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)

        # Should not raise
        loader._cache_to_disk("0.6.1", b'{"test": true}')

    def test_fetch_remote_with_httpx(self, tmp_path, monkeypatch):
        """Test _fetch_remote with httpx available."""
        import json

        from dppvalidator.schemas import loader as loader_module

        class MockResponse:
            content = b'{"$schema": "draft-2020-12"}'
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return json.loads(self.content)

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, follow_redirects=True):  # noqa: ARG002
                return MockResponse()

        # httpx is now a core dependency
        monkeypatch.setattr(loader_module.httpx, "Client", MockClient)

        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256=None,
            context_urls=(),
        )
        result = loader._fetch_remote(schema_def)
        assert result is not None
        assert result["$schema"] == "draft-2020-12"

    def test_fetch_remote_integrity_failure(self, tmp_path, monkeypatch):
        """Test _fetch_remote with integrity check failure."""
        import json

        from dppvalidator.schemas import loader as loader_module

        class MockResponse:
            content = b'{"$schema": "draft-2020-12"}'
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return json.loads(self.content)

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, follow_redirects=True):  # noqa: ARG002
                return MockResponse()

        # httpx is now a core dependency
        monkeypatch.setattr(loader_module.httpx, "Client", MockClient)

        loader = SchemaLoader(cache_dir=tmp_path)
        schema_def = SchemaVersion(
            version="test",
            url="https://example.com/schema.json",
            sha256="wronghash",  # Will fail integrity
            context_urls=(),
        )
        result = loader._fetch_remote(schema_def)
        assert result is None

    def test_download_schema_success(self, tmp_path, monkeypatch):
        """Test download_schema succeeds."""
        from dppvalidator.schemas import loader as loader_module

        class MockResponse:
            content = b'{"$schema": "draft-2020-12"}'
            status_code = 200

            def raise_for_status(self):
                pass

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, follow_redirects=True):  # noqa: ARG002
                return MockResponse()

        # httpx is now a core dependency
        monkeypatch.setattr(loader_module.httpx, "Client", MockClient)

        loader = SchemaLoader(cache_dir=tmp_path)
        result = loader.download_schema("0.6.1", tmp_path)
        assert result.exists()
        assert "untp-dpp-schema-0.6.1.json" in str(result)

    def test_download_schema_network_error(self, tmp_path, monkeypatch):
        """Test download_schema handles network errors."""
        from dppvalidator.schemas import loader as loader_module

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, follow_redirects=True):  # noqa: ARG002
                raise ConnectionError("Network error")

        # httpx is now a core dependency
        monkeypatch.setattr(loader_module.httpx, "Client", MockClient)

        loader = SchemaLoader(cache_dir=tmp_path)
        with pytest.raises(RuntimeError, match="Failed to download"):
            loader.download_schema("0.6.1", tmp_path)


class TestBundledSchema:
    """Tests for bundled schema files."""

    def test_bundled_schema_exists_and_loads(self):
        """Test that bundled UNTP DPP schema 0.6.1 loads successfully."""
        loader = SchemaLoader()
        schema = loader.load_schema("0.6.1")

        assert schema is not None
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_bundled_schema_has_required_structure(self):
        """Test that bundled schema has expected UNTP DPP structure."""
        loader = SchemaLoader()
        schema = loader.load_schema("0.6.1")

        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "issuer" in schema["properties"]
        assert "$defs" in schema
        assert "CredentialIssuer" in schema["$defs"]
        assert "ProductPassport" in schema["$defs"]

    def test_bundled_schema_required_fields(self):
        """Test that bundled schema defines required fields correctly."""
        loader = SchemaLoader()
        schema = loader.load_schema("0.6.1")

        assert "required" in schema
        required = schema["required"]
        assert "@context" in required
        assert "id" in required
        assert "issuer" in required
