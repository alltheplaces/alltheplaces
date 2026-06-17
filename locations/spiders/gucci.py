from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GucciSpider(SitemapSpider, StructuredDataSpider):
    name = "gucci"
    item_attributes = {"brand": "Gucci", "brand_wikidata": "Q178516"}
    sitemap_urls = ["https://www.gucci.com/robots.txt"]
    sitemap_follow = ["sitemap/STORE"]
    sitemap_rules = [(r"https://www.gucci.com/\w+/en_\w+|\w+/store/[a-z-0-9]+", "parse_sd")]
    is_playwright_spider = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        extract_google_position(item, response)
        yield item
