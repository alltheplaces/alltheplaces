import random
from typing import ClassVar

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GmfFRSpider(SitemapSpider, StructuredDataSpider):
    name = "gmf_fr"
    item_attributes = {"brand": "GMF", "brand_wikidata": "Q3095296"}
    # Real agency pages carry a self-contained JSON-LD InsuranceAgency block; the page's own
    # HTML microdata is broken (its "geo" block is never attached to the Organization item).
    wanted_types = ["InsuranceAgency"]
    # No dedicated agency sitemap; agency pages are mixed in with ~1500 unrelated pages.
    sitemap_urls = ["https://www.gmf.fr/accueil.sitemap.xml"]
    # Sitemap also lists ~104 department/region pages ("assurances-<slug>", plural); the
    # trailing "-" here excludes those, matching only the singular "assurance-<slug>".
    sitemap_rules = [(r"/agences-gmf/assurance-([\w-]+)$", "parse")]
    # A handful of matching URLs aren't agency pages at all; see NOT_AN_AGENCY_PAGE_SIZE below.
    #
    # Site is behind DataDome. requires_proxy is not set: it would route every request through
    # Zyte's automap unconditionally, clashing with the explicit zyte_api meta the agency-page
    # requests already carry below (scrapy_zyte_api raises on that combination). Without it,
    # only requests we explicitly give zyte_api meta go through Zyte - robots.txt and the
    # sitemap fetch are covered separately, see ROBOTSTXT_OBEY and start() below.
    custom_settings: ClassVar = {
        # Default concurrency got banned on almost every request; a lower concurrency and a
        # delay between requests got a full crawl to 100% success.
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        # Sidesteps the direct-connection issue above for robots.txt specifically, same as
        # many other anti-bot-protected spiders in this project.
        "ROBOTSTXT_OBEY": False,
    }

    # A real agency page's JSON-LD sits at a near-constant ~9KB offset into the document; a
    # full crawl found a clean gap in body sizes between incomplete renders (<10KB) and
    # disambiguation pages (>75KB, see parse() below). 60KB sits safely in that gap.
    NOT_AN_AGENCY_PAGE_SIZE = 60_000

    async def start(self):
        # Same reasoning as _parse_sitemap below: without explicit zyte_api meta, this falls
        # back to a plain connection. httpResponseBody is enough - it's XML, not a page to render.
        async for request in super().start():
            request.meta["zyte_api"] = {"httpResponseBody": True, "geolocation": "FR"}
            yield request

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            # Nested sitemaps are XML and should not be rendered; agency pages need browserHtml.
            if request.url.endswith(".xml"):
                request.meta["zyte_api"] = {
                    "httpResponseBody": True,
                    "geolocation": "FR",
                }
            else:
                request.meta["zyte_api"] = {
                    "browserHtml": True,
                    "geolocation": "FR",
                    "javascript": True,
                }
            yield request

    def parse(self, response: TextResponse, **kwargs):
        yielded = False
        for result in self.parse_sd(response):
            yielded = True
            yield result
        if yielded:
            return

        # Nothing yielded means either an incomplete render (retry) or a genuine non-agency
        # page: some "assurance-<slug>" URLs are disambiguation pages listing every agency in
        # a city that has more than one (e.g. "assurance-paris"), not an agency record -
        # retrying would just get the same listing page every time. Body size tells them
        # apart: a real agency page's JSON-LD is always well under this size, so a response
        # already past it can't be a truncated render of one.
        if len(response.body) > self.NOT_AN_AGENCY_PAGE_SIZE:
            return
        if response.request is not None:
            if retry := get_retry_request(
                response.request,
                spider=self,
                max_retry_times=5,
                reason="no structured data extracted",
                priority_adjust=random.randint(-20, -1),  # noqa: S311 - retry priority jitter
            ):
                retry.meta["dont_cache"] = True
                yield retry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        # The JSON-LD "url" is an internal CMS link, not the page itself.
        item["website"] = response.url
        item["ref"] = response.url.rsplit("/", 1)[-1].removeprefix("assurance-")

        # The JSON-LD "name" is the agency's own trading name, already brand-free.
        if item.get("name"):
            item["branch"] = item.pop("name").title()

        # The only phone number present is a generic national call centre line, identical
        # on every agency page.
        item["phone"] = None

        # Same generic corporate Twitter/Facebook accounts on every agency page.
        item["twitter"] = None
        item["facebook"] = None

        # No explicit closed-day info is kept: GMF's openingHoursSpecification omits Sunday
        # and encodes a closed Saturday as "00:00"-"00:00", which add_range() silently drops
        # rather than marking closed - accepted rather than worked around.

        yield item
