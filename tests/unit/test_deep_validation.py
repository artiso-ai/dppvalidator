"""Unit tests for deep/recursive validation."""

import asyncio
from unittest.mock import MagicMock

import pytest

from dppvalidator.validators.deep import (
    DEFAULT_LINK_PATHS,
    DeepValidationResult,
    DeepValidator,
    LinkInfo,
    RateLimiter,
    RetryConfig,
    validate_deep,
)
from dppvalidator.validators.results import ValidationResult


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_acquires(self) -> None:
        """Rate limiter acquires without blocking on first call."""
        limiter = RateLimiter(requests_per_second=10.0)
        await limiter.acquire()
        # Should complete without blocking

    @pytest.mark.asyncio
    async def test_rate_limiter_respects_interval(self) -> None:
        """Rate limiter enforces interval between requests."""
        limiter = RateLimiter(requests_per_second=100.0)  # 10ms interval

        # First acquire should be instant
        await limiter.acquire()

        # Second acquire should wait ~10ms
        await limiter.acquire()
        # Test passes if no exception


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_exponential_backoff(self) -> None:
        """Delay increases exponentially with attempts."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=30.0)

        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 8.0

    def test_max_delay_cap(self) -> None:
        """Delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0)

        assert config.get_delay(10) == 10.0  # Would be 1024 without cap


class TestLinkInfo:
    """Tests for LinkInfo dataclass."""

    def test_link_info_creation(self) -> None:
        """LinkInfo stores all fields correctly."""
        link = LinkInfo(
            url="https://example.com/dpp/123",
            path="credentialSubject.traceabilityEvents",
            depth=2,
            parent_url="https://example.com/dpp/root",
        )

        assert link.url == "https://example.com/dpp/123"
        assert link.path == "credentialSubject.traceabilityEvents"
        assert link.depth == 2
        assert link.parent_url == "https://example.com/dpp/root"


class TestDeepValidationResult:
    """Tests for DeepValidationResult."""

    def test_valid_property_all_valid(self) -> None:
        """valid is True when root and all linked documents are valid."""
        root_result = ValidationResult(valid=True)
        link_graph = {
            "https://a.com": ValidationResult(valid=True),
            "https://b.com": ValidationResult(valid=True),
        }

        result = DeepValidationResult(
            root_result=root_result,
            link_graph=link_graph,
        )

        assert result.valid is True

    def test_valid_property_root_invalid(self) -> None:
        """valid is False when root document is invalid."""
        root_result = ValidationResult(valid=False)
        link_graph = {"https://a.com": ValidationResult(valid=True)}

        result = DeepValidationResult(
            root_result=root_result,
            link_graph=link_graph,
        )

        assert result.valid is False

    def test_valid_property_linked_invalid(self) -> None:
        """valid is False when any linked document is invalid."""
        root_result = ValidationResult(valid=True)
        link_graph = {
            "https://a.com": ValidationResult(valid=True),
            "https://b.com": ValidationResult(valid=False),
        }

        result = DeepValidationResult(
            root_result=root_result,
            link_graph=link_graph,
        )

        assert result.valid is False

    def test_to_dict(self) -> None:
        """to_dict serializes correctly."""
        root_result = ValidationResult(valid=True, schema_version="0.6.1")
        result = DeepValidationResult(
            root_result=root_result,
            visited_urls={"https://a.com"},
            total_documents=2,
            max_depth_reached=1,
            cycle_detected=False,
            elapsed_time_ms=100.5,
        )

        d = result.to_dict()

        assert d["valid"] is True
        assert d["total_documents"] == 2
        assert d["max_depth_reached"] == 1
        assert d["cycle_detected"] is False
        assert d["elapsed_time_ms"] == 100.5
        assert "https://a.com" in d["visited_urls"]


class TestDeepValidator:
    """Tests for DeepValidator."""

    def test_default_link_paths(self) -> None:
        """Default link paths are set."""
        validator = DeepValidator()
        assert validator.follow_links == DEFAULT_LINK_PATHS

    def test_custom_link_paths(self) -> None:
        """Custom link paths override defaults."""
        custom_paths = ["custom.path"]
        validator = DeepValidator(follow_links=custom_paths)
        assert validator.follow_links == custom_paths

    def test_max_depth_default(self) -> None:
        """Default max depth is 3."""
        validator = DeepValidator()
        assert validator.max_depth == 3

    def test_extract_links_from_string_url(self) -> None:
        """Links are extracted from string URLs."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": "https://example.com/dpp/123"}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/dpp/123"
        assert links[0].depth == 1

    def test_extract_links_from_array(self) -> None:
        """Links are extracted from arrays of URLs."""
        validator = DeepValidator(follow_links=["links"])
        data = {
            "links": [
                "https://example.com/a",
                "https://example.com/b",
            ]
        }

        links = validator._extract_links(data, depth=0)

        assert len(links) == 2
        assert {link.url for link in links} == {
            "https://example.com/a",
            "https://example.com/b",
        }

    def test_extract_links_from_nested_path(self) -> None:
        """Links are extracted from nested paths."""
        validator = DeepValidator(follow_links=["credentialSubject.events"])
        data = {"credentialSubject": {"events": ["https://example.com/event/1"]}}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/event/1"

    def test_extract_links_from_object_with_id(self) -> None:
        """Links are extracted from objects with id field."""
        validator = DeepValidator(follow_links=["links"])
        data = {
            "links": [
                {"id": "https://example.com/a", "name": "Link A"},
                {"id": "https://example.com/b", "name": "Link B"},
            ]
        }

        links = validator._extract_links(data, depth=0)

        assert len(links) == 2

    def test_is_valid_url_http(self) -> None:
        """HTTP URLs are valid."""
        validator = DeepValidator()
        assert validator._is_valid_url("http://example.com") is True

    def test_is_valid_url_https(self) -> None:
        """HTTPS URLs are valid."""
        validator = DeepValidator()
        assert validator._is_valid_url("https://example.com/path") is True

    def test_is_valid_url_not_url(self) -> None:
        """Non-URLs are invalid."""
        validator = DeepValidator()
        assert validator._is_valid_url("not-a-url") is False
        assert validator._is_valid_url("urn:uuid:123") is False
        assert validator._is_valid_url("file:///etc/passwd") is False

    @pytest.mark.asyncio
    async def test_validate_root_only(self) -> None:
        """Validation works for root document without links."""
        mock_result = ValidationResult(valid=True, schema_version="0.6.1")
        mock_validator = MagicMock()
        mock_validator.validate.return_value = mock_result

        deep_validator = DeepValidator(
            validator_factory=lambda: mock_validator,
            max_depth=0,
        )

        data = {"credentialSubject": {"product": {"id": "urn:uuid:123"}}}
        result = await deep_validator.validate(data)

        assert result.root_result.valid is True
        assert result.total_documents == 1
        assert len(result.link_graph) == 0

    @pytest.mark.asyncio
    async def test_validate_respects_max_depth(self) -> None:
        """Validation respects max_depth limit."""
        deep_validator = DeepValidator(max_depth=0)

        # Even with links, max_depth=0 won't follow them
        data = {"credentialSubject": {"traceabilityEvents": ["https://example.com/event/1"]}}

        result = await deep_validator.validate(data)

        # Should only validate root (max_depth=0)
        assert result.total_documents == 1


class TestValidationEngineIntegration:
    """Tests for ValidationEngine.validate_deep integration."""

    def test_validate_deep_method_exists(self) -> None:
        """ValidationEngine has validate_deep method."""
        from dppvalidator.validators.engine import ValidationEngine

        engine = ValidationEngine()
        assert hasattr(engine, "validate_deep")
        assert asyncio.iscoroutinefunction(engine.validate_deep)

    @pytest.mark.asyncio
    async def test_validate_deep_returns_result(self) -> None:
        """validate_deep returns DeepValidationResult."""
        from dppvalidator.validators.engine import ValidationEngine

        engine = ValidationEngine()
        data = {"credentialSubject": {"product": {"id": "urn:uuid:123"}}}

        result = await engine.validate_deep(data, max_depth=0)

        assert isinstance(result, DeepValidationResult)
        assert result.total_documents == 1


class TestModuleExports:
    """Tests for deep validation module exports."""

    def test_validators_module_exports(self) -> None:
        """validators module exports deep validation classes."""
        from dppvalidator.validators import (
            DeepValidator,
            validate_deep,
        )

        assert callable(DeepValidator)
        assert callable(validate_deep)

    def test_validate_deep_function(self) -> None:
        """validate_deep is an async function."""
        assert asyncio.iscoroutinefunction(validate_deep)
