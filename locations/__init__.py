__version__ = "1.0"

import requests_cache

from locations.settings import REQUESTS_CACHE_BACKEND_SETTINGS, REQUESTS_CACHE_ENABLED

try:
    if REQUESTS_CACHE_ENABLED:
        requests_cache.install_cache(**REQUESTS_CACHE_BACKEND_SETTINGS)
except Exception as e:
    print("requests_cache install failed:")
    print(e)
