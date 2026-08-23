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

        self._apply_zyte_proxy_geolocation(request, context_kwargs_meta_key)

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

    def _apply_zyte_proxy_geolocation(self, request: Request, context_kwargs_meta_key: str | None) -> None:
        """
        When a spider sets `requires_proxy`, PlaywrightSpider.update_settings()
        (see locations/playwright_spider.py) has already pointed
        PLAYWRIGHT_LAUNCH_OPTIONS/CAMOUFOX_LAUNCH_OPTIONS at Zyte API's
        proxy-mode endpoint. That only selects a Zyte-managed IP; to ask Zyte
        for an IP in a specific country, a "Zyte-Geolocation" request header
        also needs to be sent (see
        https://docs.zyte.com/zyte-api/usage/proxy-mode.html). We inject it
        via the browser context's extra_http_headers, using the same country
        resolution logic (spider name suffix, e.g. "_us") as
        ZyteApiByCountryMiddleware uses for non-browser requests.

        NOTE: this is unverified against a real Zyte account (no credentials
        in dev sandboxes) — if Zyte doesn't honour this header for
        proxy-mode/CONNECT-tunnelled traffic, this becomes a no-op and Zyte
        will just pick whatever IP it considers best, same as
        `requires_proxy = True` with no resolvable country today.
        """
        if not context_kwargs_meta_key:
            return
        if not os.environ.get("ZYTE_API_KEY"):
            return
        requires_proxy = getattr(self.crawler.spider, "requires_proxy", False)
        if not requires_proxy:
            return
        if not (country_code := get_proxy_location(requires_proxy, self.crawler.spider.name)):
            return

        context_kwargs = request.meta.setdefault(context_kwargs_meta_key, {})
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

        if Selector(response).type not in ("html", "xml"):
            # Response object is JSON format in general, and therefore doesn't need to be
            # processed further.
            return response

        # If a Playwright or Camoufox request is for a plaintext-type file
        # (for ATP, this is mostly JSON files), the browser may internally
        # render this plaintext-type file using a lightweight HTML wrapper.
        # Thus, Scrapy's Response.body would contain HTML not plaintext/JSON
        # data that was requested. We have to strip the HTML wrapping and
        # return the raw plaintext in Response.body.
        #
        # Note this is probably browser specific for how a text document is
        # rendered by a browser as HTML. The list of cases below may need to
        # be expanded to accomodate different browsers.
        plaintext = response.xpath("//body/pre/text()").get()
        if plaintext:
            return response.replace(body=plaintext.encode("utf-8"))

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
