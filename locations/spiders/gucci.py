from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GucciSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "gucci"
    item_attributes = {"brand": "Gucci", "brand_wikidata": "Q178516"}
    sitemap_urls = ["https://www.gucci.com/robots.txt"]
    sitemap_follow = ["sitemap/STORE"]
    sitemap_rules = [(r"https://www.gucci.com/\w+/en_\w+|\w+/store/[a-z-0-9]+", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "USER_AGENT": BROWSER_DEFAULT,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "CONCURRENT_REQUESTS": 1,
    }
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        extract_google_position(item, response)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
