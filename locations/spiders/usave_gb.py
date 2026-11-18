from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UsaveGBSpider(WPStoreLocatorSpider):
    name = "usave_gb"
    item_attributes = {"brand": "USave", "brand_wikidata": "Q121435010"}
    allowed_domains = ["www.usave.org.uk"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
