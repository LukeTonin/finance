"""Contains useful functions for interacting with the cache-requests module."""
from __future__ import annotations

import requests_cache

from finance.utils.requests_ import create_requests_session_from_cache_name


def get_response_objects_from_cache(cache_name: str) -> Generator[requests_cache.CachedResponse]:
    """Gets all the cached responses for a given cache_name.

    Args:
        cache_name (str): One of the keys in the cache section of base_config.json

    Returns:
        Generator[requests_cache.CachedResponse]: A list of the cached responses.
    """

    session = create_requests_session_from_cache_name(cache_name=cache_name)
    return session.cache.values()
