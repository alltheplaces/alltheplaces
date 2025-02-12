from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.closeby import ClosebySpider


class SpeedyStopUSSpider(ClosebySpider):
    name = "speedy_stop_us"
    item_attributes = {
        "brand": "Speedy Stop",
        "brand_wikidata": "Q123419843",
        "extras": Categories.FUEL_STATION.value,
    }
    api_key = "c9271c9124f5bdd13fc0258d3453ed6f"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if branch_name := item.pop("name", None):
            if " - " in branch_name:
                item["ref"] = branch_name.split(" - ", 1)[0].removeprefix("Speedy Stop #")
                item["branch"] = branch_name.split(" - ", 1)[1]
        yield item
