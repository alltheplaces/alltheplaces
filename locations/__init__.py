__version__ = "1.0"

import logging

import requests_cache

from locations.settings import REQUESTS_CACHE_BACKEND_SETTINGS, REQUESTS_CACHE_ENABLED

try:
    if REQUESTS_CACHE_ENABLED:
        requests_cache.install_cache(**REQUESTS_CACHE_BACKEND_SETTINGS)
except Exception as e:
    logging.warning(f"requests_cache install failed: {e}")
