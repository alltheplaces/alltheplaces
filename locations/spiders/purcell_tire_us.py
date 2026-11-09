import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PurcellTireUSSpider(AgileStoreLocatorSpider):
    name = "purcell_tire_us"
    item_attributes = {"brand": "Purcell Tire"}
    allowed_domains = ["purcelltire.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["categories"] == "3":  # Retread plants are industrial sites, not shops
            return

        item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = re.sub(r"\s*,\s*[A-Z]{2}\b", "", item.pop("name"))

        if feature["categories"] == "4":  # Distribution Services
            apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
        else:
            apply_category(Categories.SHOP_TYRES, item)

        yield item
