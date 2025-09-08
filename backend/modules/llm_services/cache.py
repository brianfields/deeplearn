"""LLM response caching system for performance optimization."""

import asyncio
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from .types import LLMMessage as LLMMessageInternal
from .types import LLMResponse as LLMResponseInternal

logger = logging.getLogger(__name__)

__all__ = ["LLMCache"]


class LLMCache:
    """
    File-based cache for LLM responses to improve performance and reduce API costs.

    Features:
    - SHA-256 hash-based cache keys
    - TTL (time-to-live) support
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Configurable cache directory
    """

    def __init__(
        self,
        cache_dir: str = ".llm_cache",
        enabled: bool = True,
        ttl_hours: int = 24,
        max_cache_size_mb: int = 100,
    ):
        """
        Initialize the LLM cache.

        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled
            ttl_hours: Time-to-live for cache entries in hours
            max_cache_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.ttl_hours = ttl_hours
        self.max_cache_size_mb = max_cache_size_mb
        self._lock = asyncio.Lock()

        # Create cache directory if it doesn't exist
        if enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_cache_key(self, messages: list[LLMMessageInternal], **kwargs: Any) -> str:
        """
        Generate a cache key from messages and parameters.

        Args:
            messages: List of LLM messages
            **kwargs: Additional parameters that affect the response

        Returns:
            SHA-256 hash string as cache key
        """
        # Create a deterministic representation of the request
        request_data = {
            "messages": [msg.to_dict() for msg in messages],
            "kwargs": sorted(kwargs.items()),  # Sort for consistency
        }

        # Generate hash
        request_json = json.dumps(request_data, sort_keys=True, default=str)
        cache_key = hashlib.sha256(request_json.encode()).hexdigest()

        return cache_key

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    async def get(self, messages: list[LLMMessageInternal], **kwargs: Any) -> LLMResponseInternal | None:
        """
        Retrieve a cached response if available.

        Args:
            messages: List of LLM messages
            **kwargs: Additional parameters

        Returns:
            Cached LLMResponse if found and valid, None otherwise
        """
        if not self.enabled:
            return None

        async with self._lock:
            cache_key = self._generate_cache_key(messages, **kwargs)
            cache_path = self._get_cache_path(cache_key)

            if not cache_path.exists():
                return None

            try:
                # Read cache file
                cache_data = json.loads(cache_path.read_text())

                # Check TTL
                cached_at = datetime.fromisoformat(cache_data["cached_at"])
                if datetime.now(UTC) - cached_at > timedelta(hours=self.ttl_hours):
                    # Cache expired, remove file
                    cache_path.unlink(missing_ok=True)
                    return None

                # Reconstruct LLMResponse
                response_data = cache_data["response"]
                response = LLMResponseInternal(
                    content=response_data["content"],
                    provider=response_data["provider"],
                    model=response_data["model"],
                    tokens_used=response_data.get("tokens_used"),
                    prompt_tokens=response_data.get("prompt_tokens"),
                    completion_tokens=response_data.get("completion_tokens"),
                    cost_estimate=response_data.get("cost_estimate"),
                    finish_reason=response_data.get("finish_reason"),
                    response_time_ms=response_data.get("response_time_ms"),
                    cached=True,  # Mark as cached
                )

                logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                return response

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to read cache file {cache_path}: {e}")
                # Remove corrupted cache file
                cache_path.unlink(missing_ok=True)
                return None

    async def set(self, messages: list[LLMMessageInternal], response: LLMResponseInternal, **kwargs: Any) -> None:
        """
        Store a response in the cache.

        Args:
            messages: List of LLM messages
            response: LLMResponse to cache
            **kwargs: Additional parameters
        """
        if not self.enabled:
            return

        async with self._lock:
            try:
                # Clean up expired entries first
                await self._cleanup_expired()

                # Check cache size
                if await self._get_cache_size_mb() >= self.max_cache_size_mb:
                    await self._cleanup_old_entries()

                cache_key = self._generate_cache_key(messages, **kwargs)
                cache_path = self._get_cache_path(cache_key)

                # Prepare cache data
                cache_data = {
                    "cache_key": cache_key,
                    "cached_at": datetime.now(UTC).isoformat(),
                    "messages": [msg.to_dict() for msg in messages],
                    "kwargs": kwargs,
                    "response": response.to_dict(),
                }

                # Write to file
                cache_path.write_text(json.dumps(cache_data, indent=2, default=str))

                logger.debug(f"Cached response for key: {cache_key[:8]}...")

            except Exception as e:
                logger.warning(f"Failed to write cache file: {e}")

    async def clear(self) -> None:
        """Clear all cached responses."""
        if not self.enabled:
            return

        async with self._lock:
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink(missing_ok=True)
                logger.info("Cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear cache: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        try:
            cutoff_time = datetime.now(UTC) - timedelta(hours=self.ttl_hours)

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_data = json.loads(cache_file.read_text())
                    cached_at = datetime.fromisoformat(cache_data["cached_at"])

                    if cached_at < cutoff_time:
                        cache_file.unlink(missing_ok=True)
                        logger.debug(f"Removed expired cache file: {cache_file.name}")

                except (json.JSONDecodeError, KeyError, ValueError):
                    # Remove corrupted files
                    cache_file.unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Failed to cleanup expired cache entries: {e}")

    async def _cleanup_old_entries(self, keep_percentage: float = 0.5) -> None:
        """
        Remove oldest cache entries to free up space.

        Args:
            keep_percentage: Percentage of files to keep (0.0-1.0)
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))

            if len(cache_files) < 10:  # Don't cleanup if we have few files
                return

            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda f: f.stat().st_mtime)

            # Keep the most recent entries
            keep_count = int(len(cache_files) * keep_percentage)
            files_to_remove = cache_files[:-keep_count]

            for cache_file in files_to_remove:
                cache_file.unlink(missing_ok=True)

            logger.info(f"Cleaned up {len(files_to_remove)} old cache files")

        except Exception as e:
            logger.warning(f"Failed to cleanup old cache entries: {e}")

    async def _get_cache_size_mb(self) -> float:
        """Get the current cache size in MB."""
        try:
            total_size = 0
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size

            return total_size / (1024 * 1024)  # Convert to MB

        except Exception:
            return 0.0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}

        async with self._lock:
            try:
                cache_files = list(self.cache_dir.glob("*.json"))
                cache_size_mb = await self._get_cache_size_mb()

                # Count expired files
                expired_count = 0
                cutoff_time = datetime.now(UTC) - timedelta(hours=self.ttl_hours)

                for cache_file in cache_files:
                    try:
                        cache_data = json.loads(cache_file.read_text())
                        cached_at = datetime.fromisoformat(cache_data["cached_at"])
                        if cached_at < cutoff_time:
                            expired_count += 1
                    except Exception:
                        expired_count += 1

                return {
                    "enabled": True,
                    "total_files": len(cache_files),
                    "expired_files": expired_count,
                    "cache_size_mb": round(cache_size_mb, 2),
                    "max_cache_size_mb": self.max_cache_size_mb,
                    "ttl_hours": self.ttl_hours,
                    "cache_dir": str(self.cache_dir),
                }

            except Exception as e:
                logger.warning(f"Failed to get cache stats: {e}")
                return {
                    "enabled": True,
                    "error": str(e),
                }
