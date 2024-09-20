from typing import Iterable

from locations.items import Feature
from locations.storefinders.yext_search import YextSearchSpider

# Five Guys YextSearch


FIVE_GUYS_SHARED_ATTRIBUTES = {
    "brand": "Five Guys",
    "brand_wikidata": "Q1131810",
}


class FiveGuysUSSpider(YextSearchSpider):
    name = "five_guys_us"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    host = "https://restaurants.fiveguys.com"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("name")
        item["website"] = location["c_pagesURL"]
        self.process_websites(item)
        yield item

    def process_websites(self, item) -> None:
        """Override with any changes for websites, e.g. multiple languages"""
        return
