from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoachUSSpider(SitemapSpider, StructuredDataSpider):
    name = "coach_us"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = ["https://www.coach.com/stores/sitemap.xml"]
    sitemap_rules = [(r"https://www.coach.com/stores/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = (item.pop("name", "") or "").removeprefix("About ")
        apply_category(Categories.SHOP_BAG, item)
        yield item
