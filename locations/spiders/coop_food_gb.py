import re
from typing import AsyncIterator

from scrapy import Request
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

STORE_URL_RE = re.compile(r"/store-finder/[A-Z0-9]+-[A-Z0-9]+/", re.IGNORECASE)
ZYTE_API_BROWSER_GB = {"browserHtml": True, "geolocation": "GB", "javascript": True}


class CoopFoodGBSpider(SitemapSpider, StructuredDataSpider):
    name = "coop_food_gb"
    item_attributes = {"brand": "Co-op Food", "brand_wikidata": "Q3277439"}
    allowed_domains = ["coop.co.uk"]
    sitemap_urls = ["https://www.coop.co.uk/store-finder/sitemap.xml"]
    sitemap_rules = [(STORE_URL_RE, "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for url in self.sitemap_urls:
            yield Request(
                url,
                self._parse_sitemap,
                meta={"zyte_api": {"httpResponseBody": True, "geolocation": "GB"}},
            )

    def sitemap_filter(self, entries):
        for entry in entries:
            if STORE_URL_RE.search(entry["loc"]):
                yield entry

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            if isinstance(request, Request):
                request.meta["zyte_api"] = ZYTE_API_BROWSER_GB
            yield request

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
