from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MarkgrafenGetraenkemarktDESpider(WPStoreLocatorSpider):
    name = "markgrafen_getraenkemarkt_de"
    item_attributes = {
        "brand_wikidata": "Q100324493",
        "brand": "Markgrafen Getränkemarkt",
        "extras": Categories.SHOP_BEVERAGES.value,
    }
    allowed_domains = [
        "www.markgrafen.com",
    ]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["phone"]:
            item["phone"] = item["phone"].replace("/", "")
        yield item
