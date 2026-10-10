from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class LosCucosMexicanCafeUSSpider(AgileStoreLocatorSpider):
    name = "los_cucos_mexican_cafe_us"
    item_attributes = {"brand": "Los Cucos Mexican Cafe"}
    allowed_domains = ["loscucos.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)

        # Bay City is in Texas, but the source places it in Alabama.
        if feature["id"] == "49":
            item.pop("lat", None)
            item.pop("lon", None)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "mexican"
        yield item
