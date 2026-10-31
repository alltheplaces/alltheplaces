from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class JohnnysPizzaHouseUSSpider(AgileStoreLocatorSpider):
    name = "johnnys_pizza_house_us"
    item_attributes = {"brand": "Johnny's Pizza House"}
    allowed_domains = ["johnnysph.com"]

    def pre_process_data(self, feature: dict) -> None:
        # One record has an empty title, which the store finder cannot strip.
        if not (feature.get("title") or "").strip():
            feature["title"] = feature.get("city")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"

        yield item
