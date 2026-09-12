import random

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Site is behind DataDome; every request needs a real browser render to get past it.
ZYTE_BROWSER_HTML = {"browserHtml": True, "geolocation": "FR", "javascript": True}


class ButFRSpider(CrawlSpider, StructuredDataSpider):
    name = "but_fr"
    item_attributes = {"brand": "But", "brand_wikidata": "Q2877537", "name": "But"}
    allowed_domains = ["but.fr"]
    # No dedicated store sitemap. The store finder's landing page links 13 region index pages
    # (also cross-linked from every region page itself, so a single start URL is enough), and
    # each region page lists every store in that region directly - no department-level page
    # needed in between.
    start_urls = ["https://www.but.fr/magasins/recherche-magasins"]
    rules = [
        # Region pages: no callback, so CrawlSpider follows them (default follow=True) without
        # yielding items - just to discover the other regions and their store links below.
        Rule(LinkExtractor(allow=r"/magasins/[^/]+/index-r\d+\.html"), process_request="use_zyte_browser"),
        Rule(LinkExtractor(allow=r"/magasins/\d+/"), callback="parse_item", process_request="use_zyte_browser"),
    ]
    # Source gives hours as "10h00"/"09h30", not "10:00"/"09:30".
    time_format = "%Hh%M"
    custom_settings = {
        # Default concurrency risked bans in manual testing against DataDome.
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,
    }

    async def start(self):
        async for request in super().start():
            request.meta["zyte_api"] = ZYTE_BROWSER_HTML
            yield request

    def use_zyte_browser(self, request, response):
        request.meta["zyte_api"] = ZYTE_BROWSER_HTML
        return request

    def parse_item(self, response: TextResponse, **kwargs):
        # Zyte occasionally returns the page before the JSON-LD has finished loading; retry
        # instead of losing the location.
        yielded = False
        for result in self.parse_sd(response):
            yielded = True
            yield result
        if not yielded and response.request is not None:
            if retry := get_retry_request(
                response.request,
                spider=self,
                max_retry_times=5,
                reason="no structured data extracted",
                priority_adjust=random.randint(-20, -1),  # noqa: S311 - retry priority jitter
            ):
                yield retry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        # JSON-LD address/name are generated from a URL slug, not the real text (spaces become
        # hyphens, accents/apostrophes drop) - street/city/branch are read from visible text
        # instead; postcode/country are fine as parsed from the JSON-LD.
        lines = response.css("div.shop-address div.address p::text").getall()
        if len(lines) == 2:
            item["street_address"] = lines[0].strip()
            item["city"] = lines[1].removeprefix(item["postcode"]).strip()

        item.pop("name", None)
        if h1 := response.css("div.detailShop-header h1::text").get():
            item["branch"] = h1.removeprefix("But ")

        # Same national call-centre number on every store page seen so far, not a store line.
        item["phone"] = None

        # Same generic "store entrance" stock photo on every store page seen so far.
        if item.get("image", "").endswith("/font-magasin/entree-magasin.jpg"):
            item["image"] = None

        yield item
