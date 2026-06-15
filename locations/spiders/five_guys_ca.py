from typing import Iterable

from locations.items import Feature
from locations.spiders.five_guys_us import FIVE_GUYS_SHARED_ATTRIBUTES
from locations.storefinders.yext_search import YextSearchSpider

# Five Guys YextSearch


class FiveGuysCASpider(YextSearchSpider):
    name = "five_guys_ca"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    host = "https://restaurants.fiveguys.ca"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("name")
        item["website"] = location["profile"]["c_pagesURL"]
        self.process_websites(item)
        yield item

    def process_websites(self, item) -> None:
        """Override with any changes for websites, e.g. multiple languages"""
        return
