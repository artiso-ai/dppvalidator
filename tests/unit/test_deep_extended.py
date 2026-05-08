"""Extended unit tests for deep validation behavior."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from dppvalidator.validators.deep import (
    DeepValidationResult,
    DeepValidator,
    LinkInfo,
    RateLimiter,
    RetryConfig,
    validate_deep,
)
from dppvalidator.validators.results import ValidationResult


class TestDeepValidationResultProperties:
    """Tests for DeepValidationResult properties."""

    def test_all_errors_aggregates_from_all_sources(self) -> None:
        """all_errors collects errors from root and all linked docs."""
        from dppvalidator.validators.results import ValidationError

        root_error = ValidationError(
            path="$.root",
            message="Root error",
            code="ROOT001",
            layer="model",
        )
        link_error = ValidationError(
            path="$.link",
            message="Link error",
            code="LINK001",
            layer="model",
        )

        root_result = ValidationResult(valid=False, errors=[root_error])
        link_result = ValidationResult(valid=False, errors=[link_error])

        result = DeepValidationResult(
            root_result=root_result,
            link_graph={"https://example.com/linked": link_result},
        )

        all_errors = result.all_errors
        assert len(all_errors) == 2
        assert ("root", root_error) in all_errors
        assert ("https://example.com/linked", link_error) in all_errors

    def test_to_dict_serializes_all_fields(self) -> None:
        """to_dict includes all required fields."""
        result = DeepValidationResult(
            root_result=ValidationResult(valid=True),
            visited_urls={"https://a.com", "https://b.com"},
            failed_urls={"https://fail.com": "Connection refused"},
            total_documents=3,
            max_depth_reached=2,
            cycle_detected=True,
            elapsed_time_ms=150.5,
        )

        d = result.to_dict()

        assert d["valid"] is True
        assert d["total_documents"] == 3
        assert d["max_depth_reached"] == 2
        assert d["cycle_detected"] is True
        assert d["elapsed_time_ms"] == 150.5
        assert "https://fail.com" in d["failed_urls"]
        assert len(d["visited_urls"]) == 2


class TestLinkExtraction:
    """Tests for link extraction from DPP documents."""

    def test_extract_from_object_with_url_field(self) -> None:
        """Extract URL from object with url field."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": [{"url": "https://example.com/a", "name": "A"}]}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/a"

    def test_extract_from_object_with_href_field(self) -> None:
        """Extract URL from object with href field."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": [{"href": "https://example.com/b", "label": "B"}]}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/b"

    def test_extract_from_object_with_linkURL_field(self) -> None:
        """Extract URL from object with linkURL field."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": [{"linkURL": "https://example.com/c"}]}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/c"

    def test_skip_non_http_urls(self) -> None:
        """Non-HTTP URLs are skipped."""
        validator = DeepValidator(follow_links=["links"])
        data = {
            "links": [
                "https://example.com/valid",
                "urn:uuid:123",
                "file:///etc/passwd",
                "ftp://ftp.example.com",
            ]
        }

        links = validator._extract_links(data, depth=0)

        assert len(links) == 1
        assert links[0].url == "https://example.com/valid"

    def test_extract_nested_array_paths(self) -> None:
        """Extract URLs from arrays in nested paths."""
        validator = DeepValidator(follow_links=["data.items"])
        data = {
            "data": {
                "items": [
                    "https://example.com/1",
                    "https://example.com/2",
                ]
            }
        }

        links = validator._extract_links(data, depth=0)

        assert len(links) == 2

    def test_path_not_found_returns_empty(self) -> None:
        """Non-existent path returns no links."""
        validator = DeepValidator(follow_links=["nonexistent.path"])
        data = {"other": "data"}

        links = validator._extract_links(data, depth=0)

        assert len(links) == 0

    def test_depth_incremented_correctly(self) -> None:
        """Extracted links have depth incremented by 1."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": ["https://example.com/a"]}

        links = validator._extract_links(data, depth=2)

        assert links[0].depth == 3

    def test_parent_url_stored(self) -> None:
        """Parent URL is stored in LinkInfo."""
        validator = DeepValidator(follow_links=["links"])
        data = {"links": ["https://example.com/child"]}

        links = validator._extract_links(data, depth=0, parent_url="https://example.com/parent")

        assert links[0].parent_url == "https://example.com/parent"


class TestURLPathExtraction:
    """Tests for _get_urls_at_path method."""

    def test_simple_path(self) -> None:
        """Extract from simple property path."""
        validator = DeepValidator()
        data = {"link": "https://example.com"}

        urls = validator._get_urls_at_path(data, "link")

        assert urls == ["https://example.com"]

    def test_nested_path(self) -> None:
        """Extract from nested path."""
        validator = DeepValidator()
        data = {"level1": {"level2": "https://example.com"}}

        urls = validator._get_urls_at_path(data, "level1.level2")

        assert urls == ["https://example.com"]

    def test_array_path(self) -> None:
        """Extract from array at path."""
        validator = DeepValidator()
        data = {"items": [{"id": "https://a.com"}, {"id": "https://b.com"}]}

        urls = validator._get_urls_at_path(data, "items.id")

        assert "https://a.com" in urls
        assert "https://b.com" in urls

    def test_missing_intermediate_returns_empty(self) -> None:
        """Missing intermediate path returns empty."""
        validator = DeepValidator()
        data = {"other": "value"}

        urls = validator._get_urls_at_path(data, "missing.path")

        assert urls == []


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_https_url(self) -> None:
        """HTTPS URL is valid."""
        validator = DeepValidator()
        assert validator._is_valid_url("https://example.com/path") is True

    def test_valid_http_url(self) -> None:
        """HTTP URL is valid."""
        validator = DeepValidator()
        assert validator._is_valid_url("http://example.com:8080/path") is True

    def test_invalid_urn(self) -> None:
        """URN is not valid HTTP URL."""
        validator = DeepValidator()
        assert validator._is_valid_url("urn:uuid:123") is False

    def test_invalid_file_url(self) -> None:
        """File URL is not valid."""
        validator = DeepValidator()
        assert validator._is_valid_url("file:///etc/passwd") is False

    def test_invalid_relative_path(self) -> None:
        """Relative path is not valid URL."""
        validator = DeepValidator()
        assert validator._is_valid_url("/path/to/resource") is False

    def test_empty_string(self) -> None:
        """Empty string is not valid URL."""
        validator = DeepValidator()
        assert validator._is_valid_url("") is False


class TestAsyncValidation:
    """Tests for async validation methods."""

    @pytest.mark.asyncio
    async def test_validate_with_root_url(self) -> None:
        """Validation with root URL tracks it as visited."""
        validator = DeepValidator(max_depth=0)
        data = {"id": "urn:uuid:123"}

        result = await validator.validate(data, root_url="https://example.com/root")

        assert "https://example.com/root" in result.visited_urls

    @pytest.mark.asyncio
    async def test_cycle_detection(self) -> None:
        """Cycles are detected and flagged."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = ValidationResult(valid=True)

        deep_validator = DeepValidator(
            validator_factory=lambda: mock_validator,
            max_depth=1,
            follow_links=["links"],
        )

        # Data with self-referencing link
        data = {"links": ["https://example.com/self"]}

        # First validation
        await deep_validator.validate(data)

        # When link is already visited, cycle should be detected
        # Reset and run again with the URL already visited
        deep_validator._visited = {"https://example.com/self"}
        deep_validator._cycle_detected = False

        # Queue a link that's already visited
        await deep_validator._pending.put(
            LinkInfo(url="https://example.com/self", path="links", depth=1)
        )
        await deep_validator._process_queue(mock_validator)

        assert deep_validator._cycle_detected is True

    @pytest.mark.asyncio
    async def test_depth_limit_respected(self) -> None:
        """Depth limit prevents deep traversal."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = ValidationResult(valid=True)

        deep_validator = DeepValidator(
            validator_factory=lambda: mock_validator,
            max_depth=0,  # Root only
        )

        data = {"credentialSubject": {"traceabilityEvents": ["https://example.com/event"]}}
        result = await deep_validator.validate(data)

        # Should only validate root (depth 0)
        assert result.total_documents == 1
        assert len(result.link_graph) == 0

    @pytest.mark.asyncio
    async def test_max_depth_tracked(self) -> None:
        """Maximum depth reached is tracked."""
        validator = DeepValidator(max_depth=3)
        data = {"id": "test"}

        result = await validator.validate(data)

        assert result.max_depth_reached >= 0


class TestRateLimiterBehavior:
    """Tests for rate limiter behavior."""

    @pytest.mark.asyncio
    async def test_multiple_acquires_respect_rate(self) -> None:
        """Multiple acquires are rate limited."""
        import time

        limiter = RateLimiter(requests_per_second=1000.0)  # Fast for testing

        start = time.monotonic()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should complete quickly but with small delay
        assert elapsed < 0.1


class TestRetryConfigBehavior:
    """Tests for retry configuration."""

    def test_get_delay_first_attempt(self) -> None:
        """First attempt uses base delay."""
        config = RetryConfig(base_delay=1.0)
        assert config.get_delay(0) == 1.0

    def test_get_delay_respects_max(self) -> None:
        """Delay capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=10.0)
        # 10^3 = 1000, but capped at 5
        assert config.get_delay(3) == 5.0


class TestFetchWithRetry:
    """Tests for fetch with retry logic."""

    @pytest.mark.asyncio
    async def test_fetch_success(self) -> None:
        """Successful fetch returns data."""
        validator = DeepValidator(max_depth=1)

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        result = await validator._fetch_with_retry(mock_client, "https://example.com")

        assert result == {"id": "test"}

    @pytest.mark.asyncio
    async def test_fetch_rate_limited_retries(self) -> None:
        """Rate limited response triggers retry."""
        validator = DeepValidator(retry_config=RetryConfig(max_retries=2, base_delay=0.01))

        # First call rate limited, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_ok = MagicMock()
        mock_response_ok.json.return_value = {"id": "success"}

        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_response_429),
            mock_response_ok,
        ]

        result = await validator._fetch_with_retry(mock_client, "https://example.com")

        assert result == {"id": "success"}

    @pytest.mark.asyncio
    async def test_fetch_network_error_retries(self) -> None:
        """Network error triggers retry."""
        validator = DeepValidator(retry_config=RetryConfig(max_retries=2, base_delay=0.01))

        mock_response_ok = MagicMock()
        mock_response_ok.json.return_value = {"id": "recovered"}

        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            httpx.RequestError("Network error"),
            mock_response_ok,
        ]

        result = await validator._fetch_with_retry(mock_client, "https://example.com")

        assert result == {"id": "recovered"}


class TestValidateDeepFunction:
    """Tests for module-level validate_deep function."""

    @pytest.mark.asyncio
    async def test_validate_deep_returns_result(self) -> None:
        """validate_deep returns DeepValidationResult."""
        data = {"id": "urn:uuid:123"}

        result = await validate_deep(data, max_depth=0)

        assert isinstance(result, DeepValidationResult)

    @pytest.mark.asyncio
    async def test_validate_deep_custom_options(self) -> None:
        """validate_deep accepts custom options."""
        data = {"id": "urn:uuid:123"}

        result = await validate_deep(
            data,
            max_depth=2,
            follow_links=["custom.path"],
            timeout=15.0,
            auth_header={"Authorization": "Bearer token"},
        )

        assert isinstance(result, DeepValidationResult)


class TestExtractURLsFromValue:
    """Tests for _extract_urls_from_value method."""

    def test_extract_from_string(self) -> None:
        """Extract URL from string value."""
        validator = DeepValidator()
        urls = validator._extract_urls_from_value("https://example.com")

        assert urls == ["https://example.com"]

    def test_extract_from_dict_with_id(self) -> None:
        """Extract URL from dict with id field."""
        validator = DeepValidator()
        urls = validator._extract_urls_from_value({"id": "https://example.com/id"})

        assert urls == ["https://example.com/id"]

    def test_extract_from_list(self) -> None:
        """Extract URLs from list."""
        validator = DeepValidator()
        urls = validator._extract_urls_from_value(
            [
                "https://a.com",
                {"id": "https://b.com"},
            ]
        )

        assert "https://a.com" in urls
        assert "https://b.com" in urls

    def test_skip_invalid_in_dict(self) -> None:
        """Skip dict without URL fields."""
        validator = DeepValidator()
        urls = validator._extract_urls_from_value({"name": "Not a URL"})

        assert urls == []
