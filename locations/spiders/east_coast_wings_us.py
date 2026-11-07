from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class EastCoastWingsUSSpider(Spider):
    name = "east_coast_wings_us"
    item_attributes = {"brand": "East Coast Wings + Grill"}
    start_urls = ["https://eastcoastwings.com/locations/"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        # One ItemList of every restaurant, in the page's JSON-LD graph.
        for node in LinkedDataParser.iter_linked_data(response):
            if node.get("@type") != "ItemList":
                continue
            for entry in node.get("itemListElement", []):
                restaurant = entry.get("item", {})
                if restaurant.get("@type") != "Restaurant":
                    continue
                # The list includes the site's own test entry.
                if restaurant.get("name", "").startswith("Protected:"):
                    continue
                item = LinkedDataParser.parse_ld(restaurant)
                item["ref"] = restaurant.get("url")
                item["branch"] = item.pop("name", None).removeprefix("East Coast Wings + Grill ").strip(" -")
                item.pop("image", None)
                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "wings"
                yield item
