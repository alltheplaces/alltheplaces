import requests_cache

__version__ = "1.0"

requests_cache.install_cache(expire_after=60 * 60 * 24 * 3, backend="filesystem")
