"""Contains useful functions for caching HTTP requests."""
import requests
import datetime

import requests_cache
import pandas as pd

from finance.config import config


def create_requests_session_from_cache_name(cache_name: str = None) -> requests_cache.CachedSession:
    """Get requests session that is cached with a partical cache backed.

    Args:
        cache_name (str): The name of the cache to use.
            Valid cache names can be found as keys of the "cache" section of the config.
            If None, return an uncached session.

    Returns:
        requests_cache.CachedSession: A cached session that can be used to make requests.
    """

    if cache_name is None:
        return requests.Session()

    cache_config = config.get_cache_config(cache_name=cache_name)
    path = cache_config["path"]
    expire_after = cache_config["expire_after"]
    backend = cache_config["backend"]
    serializer = cache_config["serializer"]

    session = create_requests_session(cache_path=path, expire_after=expire_after, backend=backend, serializer=serializer)

    return session


def create_requests_session(
    cache_path: str, backend: str = "filesystem", serializer: str = "json", expire_after: datetime.timedelta = None
):
    """Create a cached session which stores data locally.

    Args:
        cache_path: The path at which the cache will be stored.
        backend: The type of the cache (see requests_cache documentation for more details.)
        serializer: The serializer used for caching (see requests_cache documentation for more details.)

    This is wrapper around the CachedSession object from the requests_cache library.
    More details can be found here:
    https://requests-cache.readthedocs.io/en/stable/modules/requests_cache.backends.filesystem.html#requests_cache.backends.filesystem.FileCache
    """
    session = requests_cache.CachedSession(cache_path, backend=backend, serializer=serializer, expire_after=expire_after)
    return session
