import os

from playwright.async_api import Response as PlaywrightResponse
from scrapy import Spider
from scrapy.settings import BaseSettings

from locations.middlewares.zyte_proxy_relay import ensure_relay_running


class PlaywrightSpider(Spider):
    _last_scrapy_request_url: str | None = None
    _last_observed_xml_document: str | None = None

    # True, a 2-letter country code, or unset/False (default, no proxy).
    # Mirrors locations.middlewares.zyte_api_by_country.ZyteApiByCountryMiddleware,
    # which only applies to non-browser (Zyte API REST) requests. Playwright
    # and Camoufox launch a browser once per crawl, so proxying has to be
    # wired into *_LAUNCH_OPTIONS (below) instead of per-request.
    requires_proxy: bool | str = False

    # The settings key holding launch options for this spider's browser
    # automation backend. Overridden by CamoufoxSpider.
    _proxy_launch_options_setting = "PLAYWRIGHT_LAUNCH_OPTIONS"

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        cls._apply_zyte_proxy_launch_options(settings)

    @classmethod
    def _apply_zyte_proxy_launch_options(cls, settings: BaseSettings) -> None:
        """
        Playwright/Camoufox launch a browser once per crawl, so the proxy
        server must be configured in PLAYWRIGHT_LAUNCH_OPTIONS/
        CAMOUFOX_LAUNCH_OPTIONS at settings-merge time (here, before Scrapy
        freezes settings and the browser launches) rather than per-request.
        This only fires when the spider sets `requires_proxy`, so spiders
        that don't need a proxy aren't silently routed (and billed) through
        one.

        The browser is pointed at a local relay (see
        locations/middlewares/zyte_proxy_relay.py), not directly at Zyte's
        proxy-mode endpoint, and is given no proxy credentials. This is
        deliberate: Firefox has a confirmed bug where an *authenticated*
        proxy combined with scrapy_playwright/scrapy_camoufox's
        unconditional `route.continue_(headers=...)` (used on every request
        to keep the browser request in sync with the Scrapy Request) causes
        every navigation to fail with NS_ERROR_PROXY_CONNECTION_REFUSED.
        The relay authenticates to Zyte on the browser's behalf so the
        browser-facing proxy never needs credentials. See
        zyte_proxy_relay.py's module docstring for how this was confirmed.
        """
        if not getattr(cls, "requires_proxy", False):
            return
        if not (api_key := os.environ.get("ZYTE_API_KEY")):
            return

        host, port = ensure_relay_running(api_key)

        launch_options = dict(settings.getdict(cls._proxy_launch_options_setting))
        launch_options["proxy"] = {"server": f"http://{host}:{port}"}
        settings.set(cls._proxy_launch_options_setting, launch_options, priority="spider")

    async def detect_xml_document_from_playwright_response(self, response: PlaywrightResponse) -> None:
        """
        Refer to middlewares/playwright_middleware.py for more information on
        the purpose of this function.
        """
        if response.url == getattr(self, "_last_scrapy_request_url"):
            response_text = await response.text()
            if response_text.strip().startswith("<?xml"):
                if "<?xml-stylesheet" in response_text:
                    # Only XML documents with an XSL stylesheet need to have
                    # their original XML document temporarily captured by the
                    # spider, allowing the browser's transformation of the XML
                    # document into a HTML document (or other XML
                    # representation) to be ignored.
                    setattr(self, "_last_observed_xml_document", response_text)
