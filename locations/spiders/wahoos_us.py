from typing import Iterable

from scrapy.http import Response

from locations.items import Feature, set_closed
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class WahoosUSSpider(AgileStoreLocatorSpider):
    name = "wahoos_us"
    item_attributes = {"brand": "Wahoo's Fish Tacos", "brand_wikidata": "Q7959827"}
    allowed_domains = ["www.wahoos.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "closed" in item["name"]:
            set_closed(item)
        if " (" in item["name"]:
            item["name"] = item["name"].split(" (")[0]
        yield item
