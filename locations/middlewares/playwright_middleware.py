import os

from scrapy import Selector
from scrapy.crawler import Crawler
from scrapy.http import Request, Response, TextResponse
from scrapy.spiders import SitemapSpider, XMLFeedSpider
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.captcha_solvers import click_solver
from locations.middlewares.zyte_api_by_country import get_proxy_location
from locations.playwright_spider import PlaywrightSpider


class PlaywrightMiddleware:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_request(self, request: Request) -> None:
        context_kwargs_meta_key = None
        if issubclass(type(self.crawler.spider), CamoufoxSpider):
            context_kwargs_meta_key = "camoufox_context_kwargs"
            if "camoufox" not in request.meta:
                request.meta["camoufox"] = True
            if "camoufox_page_event_handlers" not in request.meta.keys():
                request.meta["camoufox_page_event_handlers"] = {}
            if "camoufox_page_methods" not in request.meta.keys():
                request.meta["camoufox_page_methods"] = []
            if captcha_type := getattr(self.crawler.spider, "captcha_type", None):
                match captcha_type:
                    case "cloudflare_turnstile":
                        request.meta["camoufox_page_methods"].append(
                            PageMethod(click_solver, request=request, spider=self.crawler.spider)
                        )
        elif issubclass(type(self.crawler.spider), PlaywrightSpider) or getattr(
            self.crawler.spider, "is_playwright_spider", False
        ):
            # TODO: remove "is_playwright_spider" check once fully deprecated
            # and removed from all ATP spiders.
            context_kwargs_meta_key = "playwright_context_kwargs"
            if "playwright" not in request.meta:
                request.meta["playwright"] = True
            if "playwright_page_event_handlers" not in request.meta.keys():
                request.meta["playwright_page_event_handlers"] = {}
        else:
            # Spider does not want Camoufox/Playwright to be used. Skip this
            # middleware and do nothing to the request.
            return

        self._apply_zyte_proxy_context_options(request, context_kwargs_meta_key)

        if issubclass(type(self.crawler.spider), SitemapSpider) or issubclass(type(self.crawler.spider), XMLFeedSpider):
            # Workaround for Firefox always wanting to transform XML documents
            # supplied with an XSL stylesheet into HTML, and complaining with
            # a fatal error if the XSL stylesheet is prevented from being
            # downloaded. This workaround requires a hook for each Playwright
            # "response" event that calls back to a method on either a
            # CamoufoxSpider or PlaywrightSpider, which checks the body of the
            # Playwright "Response" object to see if it's an XML document,
            # then saves this body temporarily into a spider attribute.
            # Another hook on the "domcontentloaded" Playwright event also
            # calls back to a method on either CamoufoxSpider or
            # PlaywrightSpider to check if the final Playwright page (after
            # redirects are resolved) URL matches the original Scrapy Request
            # URL. If there is a match, the Playwright Page content is
            # checked to confirm it is HTML (XSL stylesheet applied) and then
            # the page is replaced with a link with the "download" attribute
            # set, which is then clicked to force Firefox to download (not
            # render) the XML document.
            setattr(self.crawler.spider, "_last_scrapy_request_url", request.url)
            if issubclass(type(self.crawler.spider), CamoufoxSpider):
                request.meta["camoufox_page_event_handlers"][
                    "response"
                ] = "detect_xml_document_from_playwright_response"
            elif issubclass(type(self.crawler.spider), PlaywrightSpider):
                request.meta["playwright_page_event_handlers"][
                    "response"
                ] = "detect_xml_document_from_playwright_response"

    def _apply_zyte_proxy_context_options(self, request: Request, context_kwargs_meta_key: str | None) -> None:
        """
        When a spider sets `requires_proxy`, PlaywrightSpider.update_settings()
        (see locations/playwright_spider.py) has already pointed
        PLAYWRIGHT_LAUNCH_OPTIONS/CAMOUFOX_LAUNCH_OPTIONS at a local relay
        that forwards to Zyte API's proxy-mode endpoint. Two more things
        need to be set on the browser *context* (not the launch options) for
        that to actually work:

        1. ignore_https_errors=True -- Zyte's proxy-mode intercepts HTTPS
           traffic (to inject Zyte-* headers/controls and, when requested,
           serve from a specific geolocation), presenting a certificate
           signed by Zyte's own CA rather than the destination site's real
           certificate. Firefox doesn't trust that CA by default, so
           without this every HTTPS navigation through the proxy fails with
           SEC_ERROR_UNKNOWN_ISSUER/SSL_ERROR_UNKNOWN. Zyte does publish a
           CA certificate that could instead be installed into Firefox's
           trust store (https://docs.zyte.com/misc/ca.html), which would be
           the more rigorous fix, but Camoufox launches a fresh, ephemeral
           Firefox profile per run, so there's no persistent trust store to
           install into -- it would have to be re-provisioned into every
           profile at launch time. ignore_https_errors is the pragmatic
           alternative: it's scoped to just this browser context, and only
           applied when `requires_proxy` is set, so it never weakens
           certificate checking for a spider that isn't proxying through
           Zyte.
        2. Zyte-Geolocation -- asks Zyte for an IP in a specific country.
           Reuses the same country-resolution logic
           (ZyteApiByCountryMiddleware.get_proxy_location()) used for
           non-browser requires_proxy requests.

        NOTE: unverified against a real Zyte account at the time this was
        written (the org's Zyte account was out of credits) -- see the pull
        request description for what a real crawl succeeding/failing would
        indicate.
        """
        if not context_kwargs_meta_key:
            return
        if not os.environ.get("ZYTE_API_KEY"):
            return
        if not (spider := self.crawler.spider):
            return
        if not (requires_proxy := getattr(spider, "requires_proxy", False)):
            return

        context_kwargs = request.meta.setdefault(context_kwargs_meta_key, {})
        context_kwargs["ignore_https_errors"] = True

        if country_code := get_proxy_location(requires_proxy, spider.name):
            extra_http_headers = context_kwargs.setdefault("extra_http_headers", {})
            extra_http_headers["Zyte-Geolocation"] = country_code.upper()

    def process_response(self, request: Request, response: Response) -> Response:
        if (
            not issubclass(type(self.crawler.spider), CamoufoxSpider)
            and not issubclass(type(self.crawler.spider), PlaywrightSpider)
            and not getattr(self.crawler.spider, "is_playwright_spider", False)
        ):
            # TODO: remove "is_playwright_spider" check once fully deprecated
            # and removed from all ATP spiders.
            # Spider does not want Camoufox/Playwright to be used. Skip this
            # middleware and do nothing to the response.
            return response

        if not isinstance(response, TextResponse):
            # Skip binary responses such as .gz sitemaps, ZIP archives etc.
            return response

        # If a Playwright or Camoufox request is for a plaintext-type file
        # (for ATP, this is mostly JSON files), the browser may internally
        # render this plaintext-type file using a lightweight HTML wrapper.
        # Thus, Scrapy's Response.body would contain HTML not plaintext/JSON
        # data that was requested. We have to strip the HTML wrapping and
        # return the raw plaintext in Response.body.
        # Content-Type might still report the original type (e.g.
        # application/json) even when this has happened, so we detect the
        # wrapping by inspecting the body itself rather than trusting the
        # header. This avoids mistaking a genuine XML/HTML response (which
        # is correctly declared as such) for a wrapped one.
        content_type = (response.headers.get("Content-Type") or b"").decode("utf-8", "replace").lower()
        declared_markup = "html" in content_type or "xml" in content_type
        body_looks_wrapped = response.body.lstrip().startswith(b"<")

        if not declared_markup and body_looks_wrapped:
            # Force type="html" explicitly. response.xpath()/Selector(response)
            # would otherwise infer type="json" from Content-Type and raise
            # ValueError: Cannot use xpath on a Selector of type 'json'.
            #
            # Note this //body/pre/text() extraction is probably browser
            # specific for how a text document is rendered as HTML. This may
            # need to be expanded to accommodate different browsers.
            plaintext = Selector(text=response.text, type="html").xpath("//body/pre/text()").get()
            if plaintext:
                return response.replace(body=plaintext.encode("utf-8"))

        if Selector(response).type not in ("html", "xml"):
            # Response object is JSON format in general, and therefore doesn't need to be
            # processed further.
            return response

        # If a Playwright or Camoufox request is for an XML document (for ATP,
        # this is mostly sitemap.xml for websites) and this XML document
        # contains a <?xml-stylesheet type="text/xsl" href="//style.xsl"?>
        # type of XML comment, the browser may attempt to transform the XML
        # document into HTML, then render the HTML using the XSL stylesheet.
        # If this occurs, Scrapy's Response.body contains HTML not XML data.
        # The transformation is typically lossy with original data in the XML
        # document lost in the rendered HTML.
        #
        # For Firefox-based web browsers, there doesn't appear to be a
        # configuration preference available to disable XSL stylesheets being
        # used to transform XML documents rendered by the browser. As a
        # workaround, an <a href="document.xml" download>Click Here</a>
        # element can be added to the DOM, then a click on this link is
        # simulated, causing the browser to download the XML document instead
        # of rendering it (and using XSL stylesheets to do so).
        if last_scrapy_request_url := getattr(self.crawler.spider, "_last_scrapy_request_url", None):
            if last_scrapy_request_url == response.url:
                if xml_document := getattr(self.crawler.spider, "_last_observed_xml_document", None):
                    setattr(self.crawler.spider, "_last_scrapy_request_url", None)
                    setattr(self.crawler.spider, "_last_observed_xml_document", None)
                    return response.replace(body=xml_document.encode("utf-8"))

        return response
