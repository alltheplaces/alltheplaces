__version__ = "1.0"

import logging

import requests_cache
from requests_cache.session import CachedSession

from locations.settings import REQUESTS_CACHE_BACKEND_SETTINGS, REQUESTS_CACHE_ENABLED

try:
    if REQUESTS_CACHE_ENABLED:
        settings = REQUESTS_CACHE_BACKEND_SETTINGS
        cache_name = str(settings.pop("cache_name", "http_cache"))
        backend = str(settings.pop("backend", None))
        session_factory = settings.pop("session_factory", None)
        # TODO: perhaps allow override of session_factory if a use case for
        # such is identified in the future. CachedSession is the default.
        requests_cache.install_cache(cache_name, backend, session_factory=CachedSession, **settings)
except Exception as e:
    logging.warning(f"requests_cache install failed: {e}")
