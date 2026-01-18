import importlib

from locations.exporters.geojson import iter_spider_classes_in_modules


def test_spiders_do_not_use_lower_download_delay_than_default():
    """Prevent adding spiders that speed up crawling by lowering DOWNLOAD_DELAY.

    Existing spiders that intentionally use a lower delay are allowed via the
    `ALLOWED_LOW_DOWNLOAD_DELAY` set. If you intentionally add a new spider
    that needs a lower delay, add it to the allowlist with a clear justification.
    """

    settings = importlib.import_module("locations.settings")

    violators = []
    for spider_class in iter_spider_classes_in_modules():
        cs = getattr(spider_class, "custom_settings", {}) or {}
        if not isinstance(cs, dict):
            continue
        if "DOWNLOAD_DELAY" in cs:
            try:
                val = float(cs["DOWNLOAD_DELAY"])
            except Exception:
                continue
            if val < settings.DOWNLOAD_DELAY:
                violators.append(spider_class.name)

    ALLOWED_LOW_DOWNLOAD_DELAY = set()

    unexpected = set(violators) - ALLOWED_LOW_DOWNLOAD_DELAY
    assert not unexpected, (
        "Unexpected spiders with DOWNLOAD_DELAY < default: %s.\n"
        "If this is intentional, add the spider name to ALLOWED_LOW_DOWNLOAD_DELAY." % sorted(unexpected)
    )
