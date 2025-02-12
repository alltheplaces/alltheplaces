from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_NL
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HiziHairNLSpider(WPStoreLocatorSpider):
    name = "hizi_hair_nl"
    item_attributes = {
        "brand_wikidata": "Q122903761",
        "brand": "Hizi Hair",
        "extras": Categories.SHOP_HAIRDRESSER.value,
    }
    allowed_domains = [
        "www.hizihair.nl",
    ]
    days = DAYS_NL  # Not supplied, but if they ever are

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["website"].startswith("/kapsalons/"):
            item["website"] = "https://www.hizihair.nl" + item["website"]
        yield item
