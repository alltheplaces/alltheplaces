from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider

# Snappy Tomato runs the Agile Store Locator WordPress plugin, which returns
# every pizzeria in one admin-ajax.php response.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class SnappyTomatoPizzaUSSpider(AgileStoreLocatorSpider):
    name = "snappy_tomato_pizza_us"
    item_attributes = {"brand": "Snappy Tomato Pizza"}
    allowed_domains = ["www.snappytomato.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["ref"] = feature["id"]
        item["website"] = f"https://www.snappytomato.com/location/{feature['slug']}" if feature.get("slug") else None

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "pizza"

        yield item
