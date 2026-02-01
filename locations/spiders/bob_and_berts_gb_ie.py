from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BobAndBertsGBIESpider(WPStoreLocatorSpider):
    name = "bob_and_berts_gb_ie"
    item_attributes = {"brand_wikidata": "Q113494662", "brand": "Bob & Berts"}
    allowed_domains = [
        "bobandberts.co.uk",
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.CAFE, item)
        yield item
