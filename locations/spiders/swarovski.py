from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SwarovskiSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "swarovski"
    item_attributes = {"brand": "Swarovski", "brand_wikidata": "Q611115"}
    sitemap_urls = ["https://www.swarovski.com/sitemapindex.xml"]
    sitemap_rules = [(r"https://www.swarovski.com/en-\w+/store/[^/]+/[^/]+$", "parse_sd")]
    sitemap_follow = ["sitemap-cms"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").removeprefix("SWAROVSKI ")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        yield item
