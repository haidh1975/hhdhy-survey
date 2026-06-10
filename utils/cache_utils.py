"""
Application-level cache utilities for HHD-HY Survey App.

Design pattern: **Cache-Aside (Lazy Loading)**
  - Read: check cache → on miss, load from DB, populate cache, return
  - Write: update DB, then invalidate (delete) cache key
  - TTL-based expiry using Python's time module

Why Cache-Aside (System Design Primer §Caching):
  - Only data that is actually read gets cached
  - Cache failure degrades gracefully (falls back to DB)
  - Simple invalidation: delete on write

Reference:
  - System Design Primer — https://github.com/donnemartin/system-design-primer#cache
  - ByteByteGo — Caching strategies video notes
  - High Scalability — cache patterns

Note: For a single-process Streamlit app, st.session_state IS the cache.
This module provides a typed wrapper with TTL and explicit invalidation.
"""

from __future__ import annotations
import time
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ─── In-process TTL cache (no Redis dependency) ───────────────────────────────

class TTLCache:
    """
    Thread-safe in-process TTL cache (single-process Streamlit).

    Backed by a plain dict. Each entry: (value, expiry_timestamp).
    Eviction on access (lazy).
    """

    def __init__(self, default_ttl: int = 60) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> tuple[bool, Any]:
        """Return (hit, value). On miss or expiry returns (False, None)."""
        entry = self._store.get(key)
        if entry is None:
            return False, None
        value, expiry = entry
        if time.monotonic() > expiry:
            del self._store[key]
            return False, None
        return True, value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl is None:
            ttl = self.default_ttl
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        """Delete all keys starting with `prefix`. Returns count deleted."""
        to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in to_delete:
            del self._store[k]
        return len(to_delete)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        # evict expired before counting
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(self._store)

    def stats(self) -> dict:
        self.__len__()  # evict first
        return {"size": len(self._store), "keys": list(self._store.keys())}


# ─── Cache-aside pattern helper ───────────────────────────────────────────────

def cache_aside(
    cache: TTLCache,
    key: str,
    loader: Callable[[], Any],
    ttl: int | None = None,
) -> Any:
    """
    Cache-aside (lazy loading) helper.

    Usage:
        value = cache_aside(app_cache, "surveys:all", loader=get_surveys_db, ttl=60)
    """
    hit, value = cache.get(key)
    if hit:
        logger.debug(f"Cache HIT: {key}")
        return value
    logger.debug(f"Cache MISS: {key} — loading from source")
    value = loader()
    cache.set(key, value, ttl=ttl)
    return value


# ─── App-level singleton cache ────────────────────────────────────────────────
# One shared cache per Streamlit process (module-level singleton)

_app_cache: TTLCache | None = None


def get_app_cache(default_ttl: int = 60) -> TTLCache:
    """Return (or create) the application-level TTL cache."""
    global _app_cache
    if _app_cache is None:
        _app_cache = TTLCache(default_ttl=default_ttl)
    return _app_cache


# ─── Convenience wrappers for DB access ──────────────────────────────────────

def get_surveys_cached(ttl: int = 60) -> list[dict]:
    """Surveys from DB with cache-aside."""
    from utils.db_utils import get_surveys_db
    return cache_aside(get_app_cache(), "surveys:all", get_surveys_db, ttl=ttl)


def get_responses_cached(survey_uuid: str, ttl: int = 30) -> list[dict]:
    """Responses for one survey with cache-aside."""
    from utils.db_utils import get_responses_db
    return cache_aside(
        get_app_cache(),
        f"responses:{survey_uuid}",
        lambda: get_responses_db(survey_uuid),
        ttl=ttl,
    )


def get_stats_cached(ttl: int = 30) -> dict:
    """System stats with cache-aside."""
    from utils.db_utils import get_system_stats_db
    return cache_aside(get_app_cache(), "stats:system", get_system_stats_db, ttl=ttl)


def invalidate_survey_cache(survey_uuid: str | None = None) -> None:
    """
    Call after creating/updating a survey or response to invalidate stale cache.
    If survey_uuid is None, invalidates ALL survey-related cache entries.
    """
    cache = get_app_cache()
    cache.delete("surveys:all")
    cache.delete("stats:system")
    if survey_uuid:
        cache.delete(f"responses:{survey_uuid}")
    else:
        cache.invalidate_prefix("responses:")
