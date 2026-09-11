"""
src/utils/caching.py — File-based Caching for F1 Super Intelligence
====================================================================
Caches expensive API calls and computation results to disk.
Never repeat a network request if a valid cached copy exists.
"""

import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Callable

from src.utils.logging import get_logger

logger = get_logger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

DEFAULT_TTL_SEC = 3600 * 6  # 6 hours


def _cache_key(key: str) -> Path:
    """Convert a string key to a safe cache file path."""
    safe = hashlib.sha256(key.encode()).hexdigest()
    return CACHE_DIR / f"{safe}.pkl"


def cache_get(key: str, ttl_sec: int = DEFAULT_TTL_SEC) -> Optional[Any]:
    """Retrieve a cached value if it exists and has not expired."""
    path = _cache_key(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > ttl_sec:
        logger.debug(f"Cache expired for key: {key[:40]}...")
        return None
    try:
        with open(path, "rb") as f:
            value = pickle.load(f)
        logger.debug(f"Cache hit: {key[:40]}...")
        return value
    except Exception as e:
        logger.warning(f"Cache read error for {key[:40]}: {e}")
        return None


def cache_set(key: str, value: Any) -> None:
    """Store a value in the cache."""
    path = _cache_key(key)
    try:
        with open(path, "wb") as f:
            pickle.dump(value, f)
        logger.debug(f"Cached: {key[:40]}...")
    except Exception as e:
        logger.warning(f"Cache write error for {key[:40]}: {e}")


def cache_clear(key: str) -> None:
    """Delete a specific cache entry."""
    path = _cache_key(key)
    if path.exists():
        path.unlink()
        logger.info(f"Cache cleared: {key[:40]}")


def cache_clear_all() -> int:
    """Delete all cache files. Returns number of files deleted."""
    count = 0
    for f in CACHE_DIR.glob("*.pkl"):
        f.unlink()
        count += 1
    logger.info(f"Cache cleared: {count} files deleted.")
    return count


def cached(key_fn: Callable, ttl_sec: int = DEFAULT_TTL_SEC):
    """
    Decorator factory. Usage:

        @cached(lambda *a, **kw: f"my_key_{a[0]}")
        def expensive_fn(x):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            result = cache_get(key, ttl_sec)
            if result is not None:
                return result
            result = fn(*args, **kwargs)
            if result is not None:
                cache_set(key, result)
            return result
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
