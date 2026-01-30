"""Disk cache with TTL for external vocabulary data."""

from __future__ import annotations

import contextlib
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Cached vocabulary data with metadata."""

    data: frozenset[str]
    fetched_at: float
    expires_at: float
    source_url: str


class VocabularyCache:
    """Disk-based cache for external vocabulary data with TTL.

    Provides persistent caching to reduce HTTP requests and enable
    offline operation.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_hours: int = 24,
    ) -> None:
        """Initialize cache.

        Args:
            cache_dir: Directory for cache files. Uses temp dir if None.
            ttl_hours: Time-to-live in hours for cache entries.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "dppvalidator" / "vocabularies"
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_hours * 3600
        self._memory_cache: dict[str, CacheEntry] = {}

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.json"

    def get(self, url: str) -> frozenset[str] | None:
        """Get cached vocabulary data.

        Args:
            url: Source URL of the vocabulary

        Returns:
            Cached data if valid, None if expired or not found
        """
        if url in self._memory_cache:
            entry = self._memory_cache[url]
            if time.time() < entry.expires_at:
                return entry.data
            del self._memory_cache[url]

        cache_path = self._get_cache_path(url)
        if not cache_path.exists():
            return None

        try:
            cache_data = json.loads(cache_path.read_text())
            expires_at = cache_data.get("expires_at", 0)

            if time.time() >= expires_at:
                cache_path.unlink(missing_ok=True)
                return None

            data = frozenset(cache_data.get("data", []))
            entry = CacheEntry(
                data=data,
                fetched_at=cache_data.get("fetched_at", 0),
                expires_at=expires_at,
                source_url=url,
            )
            self._memory_cache[url] = entry
            return data

        except (json.JSONDecodeError, KeyError, OSError):
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, url: str, data: frozenset[str]) -> None:
        """Cache vocabulary data.

        Args:
            url: Source URL of the vocabulary
            data: Vocabulary values to cache
        """
        self._ensure_cache_dir()

        now = time.time()
        expires_at = now + self.ttl_seconds

        entry = CacheEntry(
            data=data,
            fetched_at=now,
            expires_at=expires_at,
            source_url=url,
        )
        self._memory_cache[url] = entry

        cache_data = {
            "data": list(data),
            "fetched_at": now,
            "expires_at": expires_at,
            "source_url": url,
        }

        cache_path = self._get_cache_path(url)
        with contextlib.suppress(OSError):
            cache_path.write_text(json.dumps(cache_data), encoding="utf-8")

    def clear(self) -> None:
        """Clear all cached data."""
        self._memory_cache.clear()
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink(missing_ok=True)

    def invalidate(self, url: str) -> None:
        """Invalidate cache entry for a specific URL.

        Args:
            url: Source URL to invalidate
        """
        self._memory_cache.pop(url, None)
        cache_path = self._get_cache_path(url)
        cache_path.unlink(missing_ok=True)
