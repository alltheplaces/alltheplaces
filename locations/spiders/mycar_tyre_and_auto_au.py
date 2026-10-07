from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MycarTyreAndAutoAUSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "mycar_tyre_and_auto_au"
    item_attributes = {"brand": "mycar Tyre & Auto", "brand_wikidata": "Q106224674"}
    allowed_domains = ["www.mycar.com.au"]
    sitemap_urls = ["https://www.mycar.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.mycar\.com\.au\/stores\/\w+\/(?:(?<!closed-)[\w\-](?!-closed))+$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3,
    }

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item.pop("facebook", None)  # Brand-specific not location-specific.
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
