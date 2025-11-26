from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider, XMLFeedSpider
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.captcha_solvers import click_solver
from locations.playwright_spider import PlaywrightSpider


class PlaywrightMiddleware:
    def process_request(self, request: Request, spider: Spider) -> None:
        if issubclass(type(spider), CamoufoxSpider):
            if "camoufox" not in request.meta:
                request.meta["camoufox"] = True
            if "camoufox_page_event_handlers" not in request.meta.keys():
                request.meta["camoufox_page_event_handlers"] = {}
            if "camoufox_page_methods" not in request.meta.keys():
                request.meta["camoufox_page_methods"] = []
            if captcha_type := getattr(spider, "captcha_type", None):
                match captcha_type:
                    case "cloudflare_turnstile":
                        request.meta["camoufox_page_methods"].append(
                            PageMethod(click_solver, request=request, spider=spider)
                        )
        elif issubclass(type(spider), PlaywrightSpider) or getattr(spider, "is_playwright_spider", False):
            # TODO: remove "is_playwright_spider" check once fully deprecated
            # and removed from all ATP spiders.
            if "playwright" not in request.meta:
                request.meta["playwright"] = True
            if "playwright_page_event_handlers" not in request.meta.keys():
                request.meta["playwright_page_event_handlers"] = {}
        else:
            # Spider does not want Camoufox/Playwright to be used. Skip this
            # middleware and do nothing to the request.
            return

        if issubclass(type(spider), SitemapSpider) or issubclass(type(spider), XMLFeedSpider):
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
            setattr(spider, "_last_scrapy_request_url", request.url)
            if issubclass(type(spider), CamoufoxSpider):
                request.meta["camoufox_page_event_handlers"][
                    "response"
                ] = "detect_xml_document_from_playwright_response"
            elif issubclass(type(spider), PlaywrightSpider):
                request.meta["playwright_page_event_handlers"][
                    "response"
                ] = "detect_xml_document_from_playwright_response"

    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        if (
            not issubclass(type(spider), CamoufoxSpider)
            and not issubclass(type(spider), PlaywrightSpider)
            and not getattr(spider, "is_playwright_spider", False)
        ):
            # TODO: remove "is_playwright_spider" check once fully deprecated
            # and removed from all ATP spiders.
            # Spider does not want Camoufox/Playwright to be used. Skip this
            # middleware and do nothing to the response.
            return response

        # If a Playwright or Camoufox request is for a plaintext-type file
        # (for ATP, this is mostly JSON files), the browser may internally
        # render this plaintext-type file using a lightweight HTML wrapper.
        # Thus Scrapy's Response.body would contain HTML not plaintext/JSON
        # data that was requested. We have to strip the HTML wrapping and
        # return the raw plaintext in Response.body.
        #
        # Note this is probably browser specific for how a text document is
        # rendered by a browser as HTML. The list of cases below may need to
        # be expanded to accomodate different browsers.
        if response.xpath('//link[@href="resource://content-accessible/plaintext.css"]').get():
            # Rendering by Firefox-based web browsers
            plaintext = response.xpath("//body/pre/text()").get()
            return response.replace(body=plaintext.encode("utf-8"))

        # If a Playwright or Camoufox request is for a XML document (for ATP,
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
        if last_scrapy_request_url := getattr(spider, "_last_scrapy_request_url", None):
            if last_scrapy_request_url == response.url:
                if xml_document := getattr(spider, "_last_observed_xml_document", None):
                    setattr(spider, "_last_scrapy_request_url", None)
                    setattr(spider, "_last_observed_xml_document", None)
                    return response.replace(body=xml_document.encode("utf-8"))

        # At this point the response should be a HTML document or binary
        # file which has been downloaded by the browser (for example, ZIP
        # archive) and both HTML and binary files should be returned as-is
        # without modification.
        return response
