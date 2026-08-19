from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class Motel6Spider(SitemapSpider, StructuredDataSpider):
    name = "motel6"
    BRANDS = {
        "Studio 6": {"brand": "Studio 6", "brand_wikidata": "Q115793950"},
        "Motel 6": {"brand": "Motel 6", "brand_wikidata": "Q2188884"},
    }
    sitemap_urls = ["https://www.motel6.com/sitemap.xml"]
    sitemap_rules = [("/property/", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT, "DOWNLOAD_DELAY": 5}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Studio 6 " in item["name"]:
            item["name"] = "Studio 6"
            item.update(self.BRANDS[item["name"]])
        else:
            item["name"] = "Motel 6"
            item.update(self.BRANDS[item["name"]])
        apply_category(Categories.MOTEL, item)
        yield item
